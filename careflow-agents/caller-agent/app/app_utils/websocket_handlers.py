"""
WebSocket Message Handlers for Twilio ConversationRelay

This module handles all ConversationRelay message types for voice streaming:
- setup: Initial connection with call metadata
- prompt: User speech transcription (STT)
- interrupt: User interrupted agent response
- dtmf: Keypad input (used for typing simulation)
- error: ConversationRelay errors

Author: CareFlow Pulse Team
Version: 2.0.0
"""

import json
import logging
from datetime import datetime
from typing import Optional

import websockets
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from .conversation_relay import (
    ConversationMessage,
    DTMFMessage,
    ErrorMessage,
    InterruptMessage,
    PromptMessage,
    SessionData,
    SetupMessage,
    handle_interruption,
)


logger = logging.getLogger(__name__)


# =============================================================================
# CONNECTION MANAGER
# =============================================================================

class ConnectionManager:
    """Manages active WebSocket connections."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    def connect(self, websocket: WebSocket) -> str:
        """Register a new connection and return its ID."""
        connection_id = str(id(websocket))
        self.active_connections[connection_id] = websocket
        logger.info(f"New connection registered: {connection_id}")
        return connection_id
    
    def disconnect(self, connection_id: str) -> None:
        """Remove a connection by ID."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"Connection removed: {connection_id}")
    
    def get_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)


# Global connection manager instance
connection_manager = ConnectionManager()


# =============================================================================
# MESSAGE HANDLER
# =============================================================================

class MessageHandler:
    """Handles all ConversationRelay message types for a WebSocket session."""
    
    def __init__(self, agent, websocket: WebSocket, session_data: SessionData):
        """
        Initialize message handler for a WebSocket session.
        
        Args:
            agent: The LangGraph agent instance
            websocket: Active WebSocket connection
            session_data: Session state for this call
        """
        self.agent = agent
        self.websocket = websocket
        self.session_data = session_data
    
    async def handle_setup(self, message: dict) -> None:
        """
        Handle ConversationRelay setup message.
        
        Args:
            message: Raw setup message from Twilio
        """
        setup_msg = SetupMessage(
            session_id=message.get('sessionId'),
            call_sid=message.get('callSid'),
            from_num=message.get('from'),
            to_num=message.get('to'),
            direction=message.get('direction'),
            custom_parameters=message.get('customParameters')
        )
        
        self.session_data.call_sid = setup_msg.call_sid
        
        logger.info(f"Call setup - SID: {setup_msg.call_sid}, Direction: {setup_msg.direction}")
        if setup_msg.custom_parameters:
            logger.info(f"Custom parameters: {setup_msg.custom_parameters}")
            
            # Context Injection for Console/Simulated Calls
            patient_name = setup_msg.custom_parameters.get('patient_name')
            patient_id = setup_msg.custom_parameters.get('patient_id')
            context = setup_msg.custom_parameters.get('context')
            
            if patient_name and patient_id:
                logger.info(f"Injecting context for patient: {patient_name} ({patient_id})")
                system_instruction = (
                    f"URGENT CONTEXT: You are now connected with patient {patient_name} "
                    f"(ID: {patient_id}).\n"
                    f"ACTIVE CALL SID: {setup_msg.call_sid}\n"
                    f"IMPORTANT: If you need to use the 'end_call' tool, you MUST use the Call SID: {setup_msg.call_sid}."
                )
                if context:
                    system_instruction += f"\nSpecific Instructions:\n{context}"
                system_instruction += "\n\nThe patient has just picked up. Start the interview."
                
                self.session_data.conversation.append(ConversationMessage(
                    role='system',
                    content=system_instruction,
                    timestamp=datetime.now().isoformat()
                ))
                # Note: Initial greeting is now handled in server.py before message loop starts
    
    async def handle_prompt(self, message: dict) -> bool:
        """
        Handle user speech transcription (prompt message).
        
        Processes user speech, sends it to the agent, and streams
        the response back through the WebSocket.
        
        Args:
            message: Raw prompt message from Twilio
        
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
        self.session_data.conversation.append(ConversationMessage(
            role='user',
            content=prompt_msg.voice_prompt,
            timestamp=datetime.now().isoformat()
        ))
        
        # Reset response tracking
        self.session_data.current_response = ''
        self.session_data.interrupted_at = None
        
        try:
            accumulated_response = ''
            should_hangup = False
            
            # Stream agent response
            async for chunk in self.agent.stream_message(prompt_msg.voice_prompt, self.session_data):
                # Check connection state
                if self.websocket.client_state.name != "CONNECTED":
                    logger.info("WebSocket disconnected during streaming")
                    return False
                
                if not chunk:
                    continue
                
                # Check for hangup signal
                if "[HANGUP]" in chunk or "[[END_CALL_SIGNAL]]" in chunk:
                    logger.info("Agent requested call termination via signal")
                    clean_chunk = chunk.replace("[HANGUP]", "").replace("[[END_CALL_SIGNAL]]", "").strip()
                    if clean_chunk and self.websocket.client_state.name == "CONNECTED":
                        await self.send_text_token(clean_chunk, last=False)
                        accumulated_response += clean_chunk
                    should_hangup = True
                    continue
                
                # Send chunk to Twilio
                if not should_hangup:
                    await self.send_text_token(chunk, last=False)
                    accumulated_response += chunk
            
            # Handle hangup after agent finishes
            if should_hangup:
                logger.info("Closing connection after agent completion")
                await self.websocket.close(code=1000)
                return False
            
            # Save complete response to history (if not interrupted)
            if not self.session_data.interrupted_at and accumulated_response:
                self.session_data.conversation.append(ConversationMessage(
                    role='assistant',
                    content=accumulated_response,
                    timestamp=datetime.now().isoformat()
                ))
            
            self.session_data.current_response = None
            
            # Mark end of turn
            if self.websocket.client_state.name == "CONNECTED":
                await self.send_text_token("", last=True)
            
            return True
            
        except (websockets.exceptions.ConnectionClosed, WebSocketDisconnect):
            logger.info("Client disconnected during message processing")
            return False
        except Exception as e:
            logger.error(f"Error processing prompt: {e}", exc_info=True)
            raise
    
    def handle_interrupt(self, message: dict) -> None:
        """
        Handle user interruption message.
        
        Args:
            message: Raw interrupt message from Twilio
        """
        interrupt_msg = InterruptMessage(
            utterance_until_interrupt=message.get('utteranceUntilInterrupt'),
            duration_until_interrupt_ms=message.get('durationUntilInterruptMs')
        )
        logger.info(f"User interrupted at: {interrupt_msg.utterance_until_interrupt}")
        handle_interruption(interrupt_msg, self.session_data)
    
    def handle_dtmf(self, message: dict) -> None:
        """
        Handle DTMF (keypad) input.
        
        This is used for typing simulation - while the agent waits for
        A2A responses from CareFlow Pulse Agent, it sends DTMF tones
        to simulate "thinking" (like keyboard typing sounds).
        
        Args:
            message: Raw DTMF message from Twilio
        """
        dtmf_msg = DTMFMessage(digit=message.get('digit'))
        logger.info(f"DTMF received: {dtmf_msg.digit}")
    
    def handle_error(self, message: dict) -> None:
        """
        Handle ConversationRelay error notification.
        
        Args:
            message: Raw error message from Twilio
        """
        error_msg = ErrorMessage(description=message.get('description'))
        logger.error(f"ConversationRelay error: {error_msg.description}")
    
    async def send_text_token(self, text: str, last: bool = False) -> None:
        """
        Send a text token to Twilio ConversationRelay for TTS.
        
        Args:
            text: Text content to speak
            last: Whether this is the last token in the response
        """
        message = {
            "type": "text",
            "token": text,
            "last": last
        }
        await self.websocket.send_text(json.dumps(message))
