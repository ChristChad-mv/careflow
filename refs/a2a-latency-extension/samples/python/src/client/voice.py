#!/usr/bin/env python3
import os
import json
from datetime import datetime
import argparse
from fastapi import WebSocket
import websockets
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.utils.config import NGROK_URL, PORT
from src.utils.conversation_relay import (
    ConversationRelayTextToken,
    DTMFMessage,
    ErrorMessage,
    InterruptMessage,
    PromptMessage,
    SessionData,
    SetupMessage,
    ConversationMessage
)
from src.client.agent import agent
from typing import Optional
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ngrok_url: Optional[str] = NGROK_URL
port = PORT

# Parse command line arguments for server configuration
def parse_arguments():
    parser = argparse.ArgumentParser(description='Voice Client Server')
    parser.add_argument('--port', type=int, help='Port to run the server on')
    parser.add_argument('--supportsLatencyTaskUpdates', action='store_true',
                        help='Whether this client supports latency task updates')
    return parser.parse_args()

args = parse_arguments()
port_from_args = args.port

# Set environment variable for latency task updates support
if args.supportsLatencyTaskUpdates:
    os.environ['SUPPORTS_LATENCY_TASK_UPDATES'] = 'true'

# Handle interruption events by updating conversation history
def handle_interruption(interrupt_message: InterruptMessage, session_data: SessionData):
    logger.info('Handling interruption...')

    if session_data.current_response:
        utterance_until_interrupt = interrupt_message.utterance_until_interrupt
        current_response = session_data.current_response

        interrupt_position = len(current_response)
        if utterance_until_interrupt and utterance_until_interrupt.strip():
            position = current_response.lower().find(utterance_until_interrupt.lower())
            if position != -1:
                interrupt_position = position + len(utterance_until_interrupt)

        spoken_portion = current_response[:interrupt_position]

        if spoken_portion.strip():
            session_data.conversation.append(ConversationMessage(
                role='assistant',
                content=spoken_portion,
                timestamp=datetime.now().isoformat(),
                interrupted=True,
                interrupted_at=interrupt_position
            ))

            logger.info(f'Added interrupted response to conversation: "{spoken_portion}"')
            logger.info(f'Interrupted at position: {interrupt_position} of {len(current_response)}')

        session_data.interrupted_at = interrupt_position

# Create FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/public", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "public")), name="public")

@app.post("/twiml", response_class=PlainTextResponse)
async def twiml(request: Request):
    host = ngrok_url or str(request.headers.get('host')) or f"localhost:{port_from_args or int(port)}"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <ConversationRelay url="wss://{host}/ws" welcomeGreeting="Hello, how can I help you?" ttsProvider="ElevenLabs" voice="UgBBYS2sOqTuMpoF3BR0" />
    </Connect>
</Response>"""

    return Response(content=twiml, media_type="text/xml")

# Store active WebSocket connections
connections = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection_id = str(id(websocket))
    connections[connection_id] = websocket

    logger.info('New WebSocket connection established')

    # Store session data for this connection
    session_data = SessionData(
        connected_at=datetime.now().isoformat(),
        call_sid=None,
        conversation=[]
    )

    agent.set_ws_channel(websocket)
    await agent.init()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            logger.info('Received message:', message)

            # Handle different ConversationRelay message types
            if message.get('type') == 'setup':
                # Convert to typed message
                setup_message = SetupMessage(
                    session_id=message.get('sessionId'),
                    call_sid=message.get('callSid'),
                    from_num=message.get('from'),
                    to_num=message.get('to'),
                    direction=message.get('direction'),
                    custom_parameters=message.get('customParameters')
                )

                logger.info('ConversationRelay setup')
                session_data.call_sid = setup_message.call_sid
                logger.info(f"Session ID: {setup_message.session_id}")
                logger.info(f"Call SID: {setup_message.call_sid}")
                if setup_message.custom_parameters:
                    logger.info(f"Custom parameters: {setup_message.custom_parameters}")

            elif message.get('type') == 'prompt':
                # Convert to typed message
                prompt_message = PromptMessage(
                    voice_prompt=message.get('voicePrompt'),
                    lang=message.get('lang'),
                    last=message.get('last')
                )

                logger.info(f"User said: {prompt_message.voice_prompt}")

                # Add user message to conversation history
                session_data.conversation.append(ConversationMessage(
                    role='user',
                    content=prompt_message.voice_prompt,
                    timestamp=datetime.now().isoformat()
                ))

                # Stream response from our LangGraph agent
                try:
                    is_first_chunk = True
                    token_index = 0
                    accumulated_response = ''

                    # Clear any previous response tracking
                    session_data.current_response = ''
                    session_data.interrupted_at = None

                    async for chunk in agent.stream_message(
                        prompt_message.voice_prompt,
                        session_data
                    ):
                        # Accumulate the response for tracking
                        accumulated_response += chunk
                        session_data.current_response = accumulated_response

                        # Send each chunk as a streaming text token
                        response_message = ConversationRelayTextToken(
                            token=chunk,
                            last=False,
                            interruptible=is_first_chunk
                        )

                        await websocket.send_text(json.dumps(response_message.to_dict()))
                        logger.info(f"Sent streaming chunk {token_index}:{chunk}")
                        is_first_chunk = False
                        token_index += 1

                    # Send final empty token to indicate end of stream
                    final_message = ConversationRelayTextToken(
                        token="",
                        last=True
                    )

                    await websocket.send_text(json.dumps(final_message.to_dict()))
                    logger.info('Sent final streaming token')

                    # Add complete response to conversation history if not interrupted
                    if not session_data.interrupted_at:
                        session_data.conversation.append(ConversationMessage(
                            role='assistant',
                            content=accumulated_response,
                            timestamp=datetime.now().isoformat()
                        ))

                    # Clear tracking
                    session_data.current_response = None

                except Exception as error:
                    logger.error('Error processing message:', error)
                    raise

            elif message.get('type') == 'interrupt':
                # Convert to typed message
                interrupt_message = InterruptMessage(
                    utterance_until_interrupt=message.get('utteranceUntilInterrupt'),
                    duration_until_interrupt_ms=message.get('durationUntilInterruptMs')
                )

                logger.info(f"User interrupted at: {interrupt_message.utterance_until_interrupt}")
                logger.info(f"Interrupt duration: {interrupt_message.duration_until_interrupt_ms}ms")

                # Handle interruption for conversation tracking
                handle_interruption(interrupt_message, session_data)

            elif message.get('type') == 'dtmf':
                # Convert to typed message
                dtmf_message = DTMFMessage(digit=message.get('digit'))
                logger.info(f"DTMF received: {dtmf_message.digit}")

            elif message.get('type') == 'error':
                # Convert to typed message
                error_message = ErrorMessage(description=message.get('description'))
                logger.info('ConversationRelay error:', error_message.description)

            else:
                logger.info('Unknown message type:', message.get('type'))
                logger.info('Full message:', message)

    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error("WebSocket error:", e)
    finally:
        # Clean up the connection
        if connection_id in connections:
            del connections[connection_id]
        logger.info('WebSocket connection removed')


# Run server
def start_server():
    import uvicorn
    port = port_from_args or int(PORT)

    logger.info(f"🚀 Twilio ConversationRelay server running on port {port}")

    configured_ngrok_url = NGROK_URL

    logger.info(f"📞 Local TwiML endpoint: http://localhost:{port}/twiml")
    if configured_ngrok_url:
        logger.info(f"📞 Public TwiML endpoint: https://{configured_ngrok_url}/twiml")

    logger.info(f"🔌 WebSocket endpoint: ws://localhost:{port}/ws")

    if configured_ngrok_url:
        logger.info("🔗 ngrok tunnel configured:")
        logger.info(f"   Public URL: https://{configured_ngrok_url}")
        logger.info(f"   Configure your Twilio phone number webhook to: https://{configured_ngrok_url}/twiml")
    else:
        logger.info("🔗 To use with ngrok:")
        logger.info(f"1. Run: ngrok http {port}")
        logger.info("2. Configure your Twilio phone number webhook to: https://YOUR_NGROK_URL.ngrok.io/twiml")

    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    start_server()
