#!/usr/bin/env python3
"""
CareFlow Pulse - Caller Agent Server

This server handles voice communications with patients via Twilio ConversationRelay.
It provides both WebSocket endpoints for real-time voice streaming and A2A protocol
support for inter-agent communication with the CareFlow Pulse Agent.

Architecture:
    - FastAPI server with WebSocket support
    - Twilio ConversationRelay integration for voice calls
    - ElevenLabs TTS for natural speech synthesis
    - A2A protocol for agent-to-agent communication
    - OpenTelemetry instrumentation for observability

Endpoints:
    - POST /twiml: Twilio webhook returning TwiML for call handling
    - WS /ws: WebSocket endpoint for ConversationRelay voice streaming
    - /* : A2A protocol endpoints (mounted at root)

Author: CareFlow Pulse Team
Version: 1.0.0
"""

import os
import json
import argparse
import logging
from datetime import datetime
from typing import Optional
from urllib.parse import quote

import uvicorn
import websockets
from fastapi import FastAPI, Request, Response, WebSocket
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect

# OpenTelemetry imports for observability
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# A2A protocol imports
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

# Local imports
from .app_utils.config import NGROK_URL, PORT
from .app_utils.conversation_relay import (
    ConversationMessage,
    DTMFMessage,
    ErrorMessage,
    InterruptMessage,
    PromptMessage,
    SessionData,
    SetupMessage,
)
from .agent import agent
from .executor import CallerAgentExecutor, caller_agent_card


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CLI ARGUMENT PARSING
# =============================================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for server configuration.
    
    Returns:
        Namespace with parsed arguments including port and feature flags.
    """
    parser = argparse.ArgumentParser(
        description='CareFlow Pulse Caller Agent Server',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='Port to run the server on (overrides config)'
    )
    parser.add_argument(
        '--supportsLatencyTaskUpdates',
        action='store_true',
        help='Enable latency task updates support'
    )
    return parser.parse_args()


# Parse CLI arguments
args = parse_arguments()
server_port = args.port or int(PORT)

# Set environment variable for latency task updates support
if args.supportsLatencyTaskUpdates:
    os.environ['SUPPORTS_LATENCY_TASK_UPDATES'] = 'true'


# =============================================================================
# FASTAPI APPLICATION SETUP
# =============================================================================

app = FastAPI(
    title="CareFlow Caller Agent",
    description="Voice interface for patient communication via Twilio",
    version="1.0.0"
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (audio prompts, etc.)
static_dir = os.path.join(os.path.dirname(__file__), "public")
if os.path.exists(static_dir):
    app.mount("/public", StaticFiles(directory=static_dir), name="public")


# =============================================================================
# OPENTELEMETRY CONFIGURATION
# =============================================================================

def setup_telemetry() -> None:
    """
    Configure OpenTelemetry for distributed tracing.
    
    Sets up Jaeger exporter via OTLP gRPC protocol.
    Falls back gracefully if telemetry backend is unavailable.
    """
    logger.info("Configuring OpenTelemetry instrumentation...")
    
    resource = Resource(attributes={
        "service.name": "careflow-caller-agent",
        "service.version": "1.0.0",
        "deployment.environment": os.environ.get("DEPLOYMENT_ENV", "development")
    })
    
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # Configure OTLP exporter (Jaeger compatible)
    otlp_endpoint = os.environ.get("OTLP_ENDPOINT", "http://localhost:4317")
    try:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"Telemetry enabled - exporting to {otlp_endpoint}")
    except Exception as e:
        logger.warning(f"Telemetry backend unavailable: {e}")
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)


setup_telemetry()


# =============================================================================
# A2A PROTOCOL SETUP
# =============================================================================

def setup_a2a() -> A2AStarletteApplication:
    """
    Configure the A2A (Agent-to-Agent) protocol application.
    
    Returns:
        Configured A2A Starlette application ready to be mounted.
    """
    executor = CallerAgentExecutor(agent)
    task_store = InMemoryTaskStore()
    request_handler = DefaultRequestHandler(executor, task_store)
    
    return A2AStarletteApplication(
        agent_card=caller_agent_card,
        http_handler=request_handler
    ).build()


a2a_app = setup_a2a()


# =============================================================================
# CONVERSATION HANDLING UTILITIES
# =============================================================================

def handle_interruption(interrupt_message: InterruptMessage, session_data: SessionData) -> None:
    """
    Handle user interruption during agent response.
    
    When a user interrupts the agent mid-speech, this function:
    1. Calculates how much of the response was actually spoken
    2. Updates conversation history with the partial response
    3. Marks the interruption point for context continuity
    
    Args:
        interrupt_message: Contains the utterance spoken until interruption
        session_data: Current session state including conversation history
    """
    logger.info("Handling user interruption...")
    
    if not session_data.current_response:
        return
    
    utterance_until_interrupt = interrupt_message.utterance_until_interrupt
    current_response = session_data.current_response
    
    # Calculate interruption position
    interrupt_position = len(current_response)
    if utterance_until_interrupt and utterance_until_interrupt.strip():
        position = current_response.lower().find(utterance_until_interrupt.lower())
        if position != -1:
            interrupt_position = position + len(utterance_until_interrupt)
    
    # Extract the portion actually spoken
    spoken_portion = current_response[:interrupt_position]
    
    if spoken_portion.strip():
        session_data.conversation.append(ConversationMessage(
            role='assistant',
            content=spoken_portion,
            timestamp=datetime.now().isoformat(),
            interrupted=True,
            interrupted_at=interrupt_position
        ))
        logger.info(f"Interrupted at position {interrupt_position}/{len(current_response)}")
    
    session_data.interrupted_at = interrupt_position


# =============================================================================
# TWILIO TWIML ENDPOINT
# =============================================================================

@app.post("/twiml", response_class=PlainTextResponse)
async def twiml_endpoint(request: Request) -> Response:
    """
    Twilio webhook endpoint returning TwiML for ConversationRelay.
    
    This endpoint is called by Twilio when a call is initiated or received.
    It returns TwiML that connects the call to our WebSocket endpoint
    for real-time voice streaming via ConversationRelay.
    
    Query Parameters (for outbound calls):
        patient_name: Name of the patient being called
        patient_id: Unique identifier for the patient
        context: Additional context for the call
    
    Returns:
        TwiML response configuring ConversationRelay with ElevenLabs TTS
    """
    # Determine host for WebSocket URL
    host = NGROK_URL or str(request.headers.get('host')) or f"localhost:{server_port}"
    
    # Extract call parameters (present for outbound calls, absent for inbound)
    params = request.query_params
    patient_name = params.get("patient_name")
    patient_id = params.get("patient_id", "")
    context = params.get("context", "")
    
    # Build WebSocket URL with parameters
    ws_url = f"wss://{host}/ws"
    query_parts = []
    
    if patient_name:
        query_parts.append(f"patient_name={quote(patient_name)}")
    if patient_id:
        query_parts.append(f"patient_id={quote(patient_id)}")
    if context:
        query_parts.append(f"context={quote(context)}")
    
    if query_parts:
        ws_url += "?" + "&".join(query_parts)
    
    # Escape XML special characters for TwiML
    ws_url_xml = ws_url.replace("&", "&amp;")
    
    # Build TwiML response
    # Note: No welcomeGreeting - the agent controls the first message
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <ConversationRelay 
            url="{ws_url_xml}" 
            ttsProvider="ElevenLabs" 
            voice="UgBBYS2sOqTuMpoF3BR0" 
        />
    </Connect>
</Response>"""
    
    return Response(content=twiml, media_type="text/xml")


# =============================================================================
# WEBSOCKET VOICE STREAMING ENDPOINT
# =============================================================================

# Track active WebSocket connections
active_connections: dict = {}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for Twilio ConversationRelay voice streaming.
    
    Handles the bidirectional voice communication between Twilio and our
    LangGraph-based conversational agent. Supports both inbound and outbound calls.
    
    Message Types Handled:
        - setup: Initial connection setup with call metadata
        - prompt: User speech transcription (STT result)
        - interrupt: User interrupted agent response
        - dtmf: Keypad input from user
        - error: ConversationRelay error notifications
    
    Args:
        websocket: FastAPI WebSocket connection
    """
    await websocket.accept()
    connection_id = str(id(websocket))
    active_connections[connection_id] = websocket
    
    logger.info("New WebSocket connection established")
    
    # Initialize session state
    session_data = SessionData(
        connected_at=datetime.now().isoformat(),
        call_sid=None,
        conversation=[]
    )
    
    # Extract context from query parameters (outbound calls)
    params = websocket.query_params
    patient_name = params.get("patient_name")
    patient_id = params.get("patient_id")
    call_context = params.get("context")
    
    if patient_name:
        # Outbound call - inject patient context
        logger.info(f"Outbound call to {patient_name} (ID: {patient_id})")
        system_instruction = (
            f"URGENT CONTEXT: You are now connected with patient {patient_name} "
            f"(ID: {patient_id})."
        )
        if call_context:
            system_instruction += f"\nSpecific Instructions:\n{call_context}"
        system_instruction += "\n\nThe patient has just picked up. Start the interview."
        
        session_data.conversation.append(ConversationMessage(
            role='system',
            content=system_instruction,
            timestamp=datetime.now().isoformat()
        ))
    else:
        # Inbound call - no patient context yet
        logger.info("Inbound call - patient identity unknown")
    
    # Connect agent to this WebSocket
    agent.set_ws_channel(websocket)
    await agent.init()
    
    try:
        await _handle_websocket_messages(websocket, session_data)
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"WebSocket closed: {e.code} - {e.reason}")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        # Cleanup
        if connection_id in active_connections:
            del active_connections[connection_id]
        if hasattr(agent, 'ws') and agent.ws == websocket:
            agent.ws = None
        logger.info("WebSocket connection cleaned up")


async def _handle_websocket_messages(websocket: WebSocket, session_data: SessionData) -> None:
    """
    Main message handling loop for WebSocket connection.
    
    Processes incoming ConversationRelay messages and routes them
    to appropriate handlers based on message type.
    
    Args:
        websocket: Active WebSocket connection
        session_data: Current session state
    """
    while True:
        data = await websocket.receive_text()
        message = json.loads(data)
        message_type = message.get('type')
        
        logger.debug(f"Received message type: {message_type}")
        
        if message_type == 'setup':
            await _handle_setup_message(message, session_data)
        
        elif message_type == 'prompt':
            should_continue = await _handle_prompt_message(
                message, websocket, session_data
            )
            if not should_continue:
                break
        
        elif message_type == 'interrupt':
            _handle_interrupt_message(message, session_data)
        
        elif message_type == 'dtmf':
            _handle_dtmf_message(message)
        
        elif message_type == 'error':
            _handle_error_message(message)
        
        else:
            logger.warning(f"Unknown message type: {message_type}")


async def _handle_setup_message(message: dict, session_data: SessionData) -> None:
    """
    Handle ConversationRelay setup message.
    
    Args:
        message: Raw setup message from Twilio
        session_data: Session state to update
    """
    setup_msg = SetupMessage(
        session_id=message.get('sessionId'),
        call_sid=message.get('callSid'),
        from_num=message.get('from'),
        to_num=message.get('to'),
        direction=message.get('direction'),
        custom_parameters=message.get('customParameters')
    )
    
    session_data.call_sid = setup_msg.call_sid
    
    logger.info(f"Call setup - SID: {setup_msg.call_sid}, Direction: {setup_msg.direction}")
    if setup_msg.custom_parameters:
        logger.info(f"Custom parameters: {setup_msg.custom_parameters}")


async def _handle_prompt_message(
    message: dict,
    websocket: WebSocket,
    session_data: SessionData
) -> bool:
    """
    Handle user speech transcription (prompt message).
    
    Processes user speech, sends it to the agent, and streams
    the response back through the WebSocket.
    
    Args:
        message: Raw prompt message from Twilio
        websocket: Active WebSocket connection
        session_data: Current session state
    
    Returns:
        bool: True to continue processing, False to close connection
    """
    prompt_msg = PromptMessage(
        voice_prompt=message.get('voicePrompt'),
        lang=message.get('lang'),
        last=message.get('last')
    )
    
    logger.info(f"User said: {prompt_msg.voice_prompt}")
    
    # Add user message to conversation history
    session_data.conversation.append(ConversationMessage(
        role='user',
        content=prompt_msg.voice_prompt,
        timestamp=datetime.now().isoformat()
    ))
    
    # Reset response tracking
    session_data.current_response = ''
    session_data.interrupted_at = None
    
    try:
        accumulated_response = ''
        should_hangup = False
        
        # Stream agent response
        async for chunk in agent.stream_message(prompt_msg.voice_prompt, session_data):
            # Check connection state
            if websocket.client_state.name != "CONNECTED":
                logger.info("WebSocket disconnected during streaming")
                return False
            
            if not chunk:
                continue
            
            # Check for hangup signal
            if "[HANGUP]" in chunk:
                logger.info("Agent requested call termination")
                clean_chunk = chunk.replace("[HANGUP]", "").strip()
                if clean_chunk and websocket.client_state.name == "CONNECTED":
                    await _send_text_token(websocket, clean_chunk, last=False)
                    accumulated_response += clean_chunk
                should_hangup = True
                continue
            
            # Send chunk to Twilio
            if not should_hangup:
                await _send_text_token(websocket, chunk, last=False)
                accumulated_response += chunk
        
        # Handle hangup after agent finishes
        if should_hangup:
            logger.info("Closing connection after agent completion")
            await websocket.close(code=1000)
            return False
        
        # Save complete response to history (if not interrupted)
        if not session_data.interrupted_at and accumulated_response:
            session_data.conversation.append(ConversationMessage(
                role='assistant',
                content=accumulated_response,
                timestamp=datetime.now().isoformat()
            ))
        
        session_data.current_response = None
        
        # Mark end of turn
        if websocket.client_state.name == "CONNECTED":
            await _send_text_token(websocket, "", last=True)
        
        return True
        
    except (websockets.exceptions.ConnectionClosed, WebSocketDisconnect):
        logger.info("Client disconnected during message processing")
        return False
    except Exception as e:
        logger.error(f"Error processing prompt: {e}", exc_info=True)
        raise


def _handle_interrupt_message(message: dict, session_data: SessionData) -> None:
    """Handle user interruption message."""
    interrupt_msg = InterruptMessage(
        utterance_until_interrupt=message.get('utteranceUntilInterrupt'),
        duration_until_interrupt_ms=message.get('durationUntilInterruptMs')
    )
    logger.info(f"User interrupted at: {interrupt_msg.utterance_until_interrupt}")
    handle_interruption(interrupt_msg, session_data)


def _handle_dtmf_message(message: dict) -> None:
    """Handle DTMF (keypad) input."""
    dtmf_msg = DTMFMessage(digit=message.get('digit'))
    logger.info(f"DTMF received: {dtmf_msg.digit}")


def _handle_error_message(message: dict) -> None:
    """Handle ConversationRelay error notification."""
    error_msg = ErrorMessage(description=message.get('description'))
    logger.error(f"ConversationRelay error: {error_msg.description}")


async def _send_text_token(websocket: WebSocket, text: str, last: bool = False) -> None:
    """
    Send a text token to Twilio ConversationRelay.
    
    Args:
        websocket: Active WebSocket connection
        text: Text content to speak
        last: Whether this is the last token in the response
    """
    message = {
        "type": "text",
        "token": text,
        "last": last
    }
    await websocket.send_text(json.dumps(message))


# =============================================================================
# A2A MOUNT (Must be last to avoid route shadowing)
# =============================================================================

app.mount("/", a2a_app)


# =============================================================================
# SERVER STARTUP
# =============================================================================

def start_server() -> None:
    """
    Start the CareFlow Caller Agent server.
    
    Initializes uvicorn with configured host/port and logs
    connection information for debugging.
    """
    logger.info("=" * 60)
    logger.info("  CareFlow Pulse - Caller Agent Server")
    logger.info("=" * 60)
    
    logger.info(f"🚀 Starting server on port {server_port}")
    
    # Log endpoint information
    logger.info(f"📞 TwiML endpoint: http://localhost:{server_port}/twiml")
    logger.info(f"🔌 WebSocket endpoint: ws://localhost:{server_port}/ws")
    
    if NGROK_URL:
        logger.info(f"🌐 Public URL: https://{NGROK_URL}")
        logger.info(f"📞 Public TwiML: https://{NGROK_URL}/twiml")
        logger.info(f"🤖 A2A endpoint: https://{NGROK_URL}/.well-known/agent.json")
    else:
        logger.info("💡 Tip: Set NGROK_URL for public access")
    
    logger.info("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=server_port)


if __name__ == "__main__":
    start_server()
