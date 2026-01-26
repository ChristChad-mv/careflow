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
import aiohttp
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

# A2A protocol imports
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

# Local imports
from app.config import PUBLIC_URL, PORT
from app.app_utils.conversation_relay import SessionData, ConversationMessage
from app.app_utils.websocket_handlers import MessageHandler, connection_manager
from app.app_utils.telemetry import setup_telemetry
from app.agent import agent
from app.app_utils.executor.caller_executor import CallerAgentExecutor
from app.schemas.agent_card.v1.caller_card import caller_card


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


# =============================================================================
# CONFIGURATION
# =============================================================================

# Default port from environment
server_port = int(PORT)


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

setup_telemetry()  # Use the comprehensive setup from app_utils.telemetry


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
        agent_card=caller_card,
        http_handler=request_handler
    ).build()


a2a_app = setup_a2a()


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
    # Priority: PUBLIC_URL > Host Header > Localhost
    host = PUBLIC_URL or str(request.headers.get('host')) or f"localhost:{server_port}"
    
    # Strip protocol if present in PUBLIC_URL/NGROK_URL for correct WebSocket URL construction
    if "://" in host:
        host = host.split("://")[1]
    
    # Extract call parameters (present for outbound calls, absent for inbound)
    params = request.query_params
    patient_name = params.get("patient_name")
    patient_id = params.get("patient_id", "")
    context = params.get("context", "")
    
    logger.info(f"⚓ Received TwiML request for {patient_name} (ID: {patient_id}) from {request.client.host}")
    
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
    
    logger.info(f"🔗 Generated WebSocket URL: {ws_url}")
    
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
    <Hangup/>
</Response>"""
    
    return Response(content=twiml, media_type="text/xml")


@app.post("/call-status")
async def call_status_endpoint(request: Request):
    """
    Twilio Status Callback.
    Triggered when the call ends (completed).
    Sends A2A message to CareFlow Agent (Pulse) to analyze the audio.
    """
    data = await request.form()
    call_sid = data.get("CallSid")
    call_status = data.get("CallStatus")
    answered_by = data.get("AnsweredBy") # human, machine, fax, unknown
    
    # Extract patient context from query params
    patient_id = request.query_params.get("patient_id", "UNKNOWN_ID")
    patient_name = request.query_params.get("patient_name", "Unknown Patient")
    
    # Extract retry count from query params (passed from call_patient tool)
    retry_count = int(request.query_params.get("retry_count", "0"))
    
    log_msg = f"📞 Call Status: {call_sid} -> {call_status} (Patient: {patient_name})"
    if answered_by:
        log_msg += f" [AnsweredBy: {answered_by}]"
    if retry_count > 0:
        log_msg += f" [Retry #{retry_count}]"
    logger.info(log_msg)
    
    # 1. Handle "Answered" event (Status: in-progress)
    if call_status == "in-progress":
        if answered_by == "machine":
            logger.warning(f"🤖 Call answered by MACHINE for {patient_name}. Agent will likely speak to voicemail.")
        else:
            logger.info(f"👤 Call answered by HUMAN for {patient_name}. Conversation starting...")

    # 2. Handle "Completed" event (Successful call finished)
    elif call_status == "completed":
        try:
            import uuid
            msg_id = str(uuid.uuid4())
            
            instruction_text = (
                f"CALL_COMPLETE: Interview with patient {patient_name} (ID: {patient_id}) finished. "
                f"Call SID: {call_sid}. Analyze the audio."
            )
            
            payload = {
                "jsonrpc": "2.0",
                "method": "message/stream",
                "params": {
                    "message": {
                        "messageId": msg_id,
                        "role": "user",
                        "parts": [{"text": instruction_text, "kind": "text"}],
                        "metadata": {
                            "task": "analyze_call_audio",
                            "call_sid": call_sid,
                            "source": "telephony_webhook"
                        }
                    }
                },
                "id": f"evt-{call_sid}"
            }
            
            pulse_url = os.environ.get("CAREFLOW_AGENT_URL", "http://localhost:8080")
            if pulse_url.endswith("/rpc"): pulse_url = pulse_url[:-4]
            
            async with aiohttp.ClientSession() as session:
                headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
                async with session.post(pulse_url, json=payload, headers=headers) as resp:
                    # Consume response to properly close connection
                    await resp.read()
                        
        except Exception as e:
            logger.error(f"❌ Error sending A2A record analysis: {e}")
    
    # 3. Handle Failed States (busy, no-answer, failed)
    elif call_status in ["busy", "no-answer", "failed"]:
        logger.warning(f"⚠️ Call {call_status} for patient {patient_name} ({patient_id})")
        
        try:
            from datetime import datetime as dt, timezone
            from app.app_utils.retry_utils import get_schedule_slot_key, schedule_patient_retry
            import uuid
            
            # Infer schedule hour from current time
            current_hour = dt.now(timezone.utc).hour
            schedule_hour = 8 if current_hour < 10 else (12 if current_hour < 16 else 20)
            schedule_slot = get_schedule_slot_key(schedule_hour)
            
            logger.info(f"🔄 Reporting failure to Pulse Agent for {patient_name} ({call_status})")
            
            # Construct A2A Message for Pulse Agent (include CallSid for logging)
            failure_instruction = (
                f"CALL_FAILED: Patient {patient_name} (ID: {patient_id}) was unreachable. "
                f"Call SID: {call_sid}. Status: {call_status}. Slot: {schedule_slot}. "
                "Log this failed attempt and wait for scheduled retry."
            )
            
            payload = {
                "jsonrpc": "2.0",
                "method": "message/stream",
                "params": {
                    "message": {
                        "messageId": str(uuid.uuid4()),
                        "role": "user",
                        "parts": [{"text": failure_instruction, "kind": "text"}],
                        "metadata": {
                            "task": "log_call_failure",
                            "call_sid": call_sid,
                            "patient_id": patient_id,
                            "status": call_status
                        }
                    }
                },
                "id": f"fail-{call_sid}"
            }
            
            pulse_url = os.environ.get("CAREFLOW_AGENT_URL", "http://localhost:8080")
            if pulse_url.endswith("/rpc"): pulse_url = pulse_url[:-4]
            
            # 1. Notify Pulse Agent first (fire-and-forget, but consume response)
            async with aiohttp.ClientSession() as session:
                headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
                async with session.post(pulse_url, json=payload, headers=headers) as resp:
                    # Consume response to properly close connection
                    await resp.read()
            
            # 2. Schedule the background retry with INCREMENTED retry_count
            next_retry_count = retry_count + 1
            success = await schedule_patient_retry(
                patient_id=patient_id,
                reason=call_status,
                schedule_slot=schedule_slot,
                retry_count=next_retry_count,  # Pass incremented count!
                delay_seconds=900  # 15 minutes
            )
            
            if success:
                logger.info(f"✅ Retry #{next_retry_count} scheduled for patient {patient_id} in 15 minutes")
            else:
                logger.warning(f"⚠️ Failed to schedule retry #{next_retry_count} for {patient_id}")
                
        except Exception as e:
            logger.error(f"❌ Error during failure handling: {e}", exc_info=True)
            
    return Response(status_code=200)


# =============================================================================
# WEBSOCKET VOICE STREAMING ENDPOINT
# =============================================================================

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
    connection_id = connection_manager.connect(websocket)
    
    logger.info(f"New WebSocket connection established ({connection_manager.get_count()} active)")
    
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
    
    # IMPORTANT: For outbound calls, generate initial greeting immediately!
    # The agent should speak FIRST when connecting to a patient
    if patient_name:
        await _send_initial_greeting(agent, websocket, session_data, patient_name)
    
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
        connection_manager.disconnect(connection_id)
        if hasattr(agent, 'ws') and agent.ws == websocket:
            agent.ws = None
        logger.info(f"WebSocket connection cleaned up ({connection_manager.get_count()} active)")


async def _send_initial_greeting(agent, websocket: WebSocket, session_data: SessionData, patient_name: str) -> None:
    """
    Generate and send the initial greeting when an outbound call connects.
    
    The agent speaks FIRST when connecting to a patient - this is critical
    for natural conversation flow. Without this, there would be awkward silence
    until the patient says something.
    
    Args:
        agent: The LangGraph agent instance
        websocket: Active WebSocket connection
        session_data: Session state for this call
        patient_name: Name of the patient for logging
    """
    logger.info(f"🎤 Generating initial greeting for {patient_name}...")
    
    try:
        # CRITICAL: Tell the agent explicitly that this is LIVE - no tools needed!
        greeting_prompt = (
            f"LIVE CALL ACTIVE with {patient_name}. "
            "The patient just picked up the phone and can hear you NOW. "
            "DO NOT use any tools - just speak directly! "
            "Say your greeting to confirm you're speaking with the right person."
        )
        
        # Stream the agent's greeting response
        async for chunk in agent.stream_message(greeting_prompt, session_data):
            if not chunk:
                continue
            
            # Check for hangup signal (shouldn't happen on greeting, but safety first)
            if "[HANGUP]" in chunk or "[[END_CALL_SIGNAL]]" in chunk:
                continue
            
            # Send chunk to Twilio for TTS
            if websocket.client_state.name == "CONNECTED":
                text_message = {
                    "type": "text",
                    "token": chunk,
                    "last": False
                }
                await websocket.send_json(text_message)
        
        logger.info("✅ Initial greeting sent to patient")
        
    except Exception as e:
        logger.error(f"❌ Error sending initial greeting: {e}", exc_info=True)


async def _handle_websocket_messages(websocket: WebSocket, session_data: SessionData) -> None:
    """
    Main message handling loop for WebSocket connection.
    
    Processes incoming ConversationRelay messages and routes them
    to appropriate handlers based on message type.
    
    Args:
        websocket: Active WebSocket connection
        session_data: Current session state
    """
    handler = MessageHandler(agent, websocket, session_data)
    
    while True:
        data = await websocket.receive_text()
        message = json.loads(data)
        message_type = message.get('type')
        
        logger.debug(f"Received message type: {message_type}")
        
        if message_type == 'setup':
            await handler.handle_setup(message)
        
        elif message_type == 'prompt':
            should_continue = await handler.handle_prompt(message)
            if not should_continue:
                break
        
        elif message_type == 'interrupt':
            handler.handle_interrupt(message)
        
        elif message_type == 'dtmf':
            handler.handle_dtmf(message)
        
        elif message_type == 'error':
            handler.handle_error(message)
        
        else:
            logger.warning(f"Unknown message type: {message_type}")


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
    
    if PUBLIC_URL:
        logger.info(f"🌐 Public URL: https://{PUBLIC_URL}")
        logger.info(f"📞 Public TwiML: https://{PUBLIC_URL}/twiml")
        logger.info(f"🤖 A2A endpoint: https://{PUBLIC_URL}/.well-known/agent.json")
    else:
        logger.info("💡 Tip: Set PUBLIC_URL or NGROK_URL for public access")
    
    logger.info("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=server_port)


if __name__ == "__main__":
    # Parse CLI arguments only when running directly
    args = parse_arguments()
    server_port = args.port or server_port
    
    # Set environment variable for latency task updates support
    if args.supportsLatencyTaskUpdates:
        os.environ['SUPPORTS_LATENCY_TASK_UPDATES'] = 'true'
    
    start_server()
