"""
CareFlow Pulse - Caller Agent

This module defines the LangGraph-based conversational agent for handling
patient phone calls. It uses ReAct architecture with tools for:
- Making outbound calls via Twilio
- Communicating with CareFlow Pulse Agent via A2A protocol
- Managing conversation state and history

Architecture:
    - LangGraph ReAct agent with Gemini 2.0 Flash
    - MemorySaver for conversation persistence
    - A2A tools for inter-agent communication
    - Twilio integration for phone calls

Author: CareFlow Pulse Team
Version: 1.0.0
"""

import asyncio
import json
import os
import time
import uuid
import yaml
import aiohttp
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Mapping, Optional
from urllib.parse import quote, urljoin

from fastapi import WebSocket
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.tools import tool
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field

from a2a.types import AgentCard
from .app_utils.config import NGROK_URL
from .app_utils.conversation_relay import SessionData
from .app_utils.llm import ModelConfig, get_model
from .app_utils.prompts.system_prompts import CALLER_SYSTEM_PROMPT
from .core.security.model_armor import ModelArmorClient

# Initialize Model Armor
model_armor_client = ModelArmorClient()

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# CALL DEDUPLICATION
# =============================================================================

# In-memory cache for call deduplication
_CALL_CACHE: Dict[str, float] = {}
_CALL_LOCK = asyncio.Lock()

# Deduplication window in seconds
CALL_DEDUP_WINDOW = 60


# =============================================================================
# TWILIO CALL TOOL
# =============================================================================

class CallPatientInput(BaseModel):
    """Input schema for the call_patient tool."""
    message: str = Field(
        description="The context/instructions for the call."
    )
    patient_name: str = Field(
        description="Name of the patient to call."
    )
    patient_id: str = Field(
        description="Unique identifier of the patient."
    )
    patient_phone: Optional[str] = Field(
        default=None,
        description="Patient's phone number (e.g., +1555123456). Required for outbound calls."
    )
    expect_reply: bool = Field(
        default=True,
        description="Whether to wait for patient reply. Set False for interstitial messages."
    )


@tool("call_patient", args_schema=CallPatientInput)
async def call_patient(
    message: str,
    patient_name: str,
    patient_id: str,
    patient_phone: Optional[str] = None,
    expect_reply: bool = True
) -> str:
    """
    Initiate a phone call to a patient via Twilio.
    
    This tool creates a Twilio call that connects to our ConversationRelay
    WebSocket endpoint, enabling real-time voice conversation.
    
    Args:
        message: Context/instructions for the call
        patient_name: Patient's name for personalization
        patient_id: Patient's unique ID for tracking
        patient_phone: Phone number to call (falls back to TEST_PATIENT_PHONE)
        expect_reply: Whether this is an interactive call
    
    Returns:
        Status message indicating call result
    """
    try:
        from twilio.rest import Client
        
        # Get Twilio credentials
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_number = os.environ.get("TWILIO_PHONE_NUMBER")
        to_number = patient_phone or os.environ.get("TEST_PATIENT_PHONE")
        ngrok_url = os.environ.get("NGROK_URL")
        
        # Validate configuration
        missing = []
        if not account_sid:
            missing.append("TWILIO_ACCOUNT_SID")
        if not auth_token:
            missing.append("TWILIO_AUTH_TOKEN")
        if not from_number:
            missing.append("TWILIO_PHONE_NUMBER")
        if not ngrok_url:
            missing.append("NGROK_URL")
        if not to_number:
            missing.append("patient_phone/TEST_PATIENT_PHONE")
        
        if missing:
            return f"Error: Missing configuration: {', '.join(missing)}"
        
        # Deduplication check
        async with _CALL_LOCK:
            current_time = time.time()
            last_call_time = _CALL_CACHE.get(patient_id, 0)
            
            if current_time - last_call_time < CALL_DEDUP_WINDOW:
                elapsed = int(current_time - last_call_time)
                logger.info(f"Duplicate call blocked for {patient_name} ({elapsed}s ago)")
                return (
                    f"SUCCESS: Call to {patient_name} is ALREADY IN PROGRESS "
                    f"(initiated {elapsed}s ago). DO NOT call again. "
                    "Wait for patient response via WebSocket."
                )
            
            # Mark call as initiated
            _CALL_CACHE[patient_id] = current_time
        
        # Create Twilio call
        logger.info(f"Initiating call to {patient_name} ({to_number})")
        
        client = Client(account_sid, auth_token)
        
        # Build TwiML webhook URL with patient context
        twiml_url = (
            f"https://{ngrok_url}/twiml"
            f"?patient_name={quote(patient_name)}"
            f"&patient_id={quote(patient_id)}"
            f"&context={quote(message)}"
        )
        
        call = client.calls.create(
            to=to_number,
            from_=from_number,
            url=twiml_url
        )
        
        logger.info(f"Call created - SID: {call.sid}")
        
        return (
            f"SYSTEM: Call initiated (SID: {call.sid}). "
            "Phone is ringing. DO NOT GENERATE TEXT yet. "
            "Wait for ConversationRelay WebSocket connection."
        )
        
    except Exception as e:
        logger.error(f"Twilio call error: {e}")
        return f"Failed to initiate call: {str(e)}"


# =============================================================================
# A2A COMMUNICATION TOOLS
# =============================================================================

def format_agent_params(obj: Mapping[str, Any], depth: int = 0) -> str:
    """
    Format agent parameters for display.
    
    Args:
        obj: Dictionary of parameters
        depth: Current indentation depth
    
    Returns:
        Formatted string representation
    """
    indent = "    " * depth
    lines = []
    for key, value in obj.items():
        if isinstance(value, dict):
            lines.append(f"{indent}{key}:\n{format_agent_params(value, depth + 2)}")
        else:
            lines.append(f"{indent}{key} ({value or 'unknown'})")
    return '\n'.join(lines)


# =============================================================================
# CALLER AGENT CLASS
# =============================================================================

class CallerAgent:
    """
    LangGraph-based conversational agent for patient phone calls.
    
    Handles both inbound (patient calls in) and outbound (system calls patient)
    scenarios. Integrates with CareFlow Pulse Agent via A2A protocol for
    medical context and decision support.
    
    Attributes:
        system_message: Base system prompt for the agent
        model: LLM instance (Gemini 2.0 Flash)
        memory: Conversation state persistence
        a2a_servers: List of A2A server URLs for inter-agent communication
        agent_cards: Cached AgentCard metadata from A2A servers
        ws: Active WebSocket connection (if in call)
    """
    
    def __init__(self, system_message: str, a2a_servers: Optional[List[str]] = None):
        """
        Initialize the Caller Agent.
        
        Args:
            system_message: System prompt defining agent behavior
            a2a_servers: Optional list of A2A server URLs
        """
        self.system_message = SystemMessage(content=system_message or '')
        self.model = get_model(ModelConfig(streaming=True))
        self.memory = MemorySaver()
        self.a2a_servers = a2a_servers or []
        self.agent_cards: List[AgentCard] = []
        self.ws: Optional[WebSocket] = None
        
        # Build the ReAct agent with tools
        self.agent = create_agent(
            model=self.model,
            tools=self._get_a2a_tools() + [call_patient],
            checkpointer=self.memory
        )
    
    async def init(self) -> None:
        """Initialize agent by loading A2A server agent cards."""
        await self._load_agent_cards()
    
    def set_ws_channel(self, ws: WebSocket) -> None:
        """
        Set the active WebSocket channel for voice communication.
        
        Args:
            ws: FastAPI WebSocket connection
        """
        self.ws = ws
    
    # -------------------------------------------------------------------------
    # A2A Server Integration
    # -------------------------------------------------------------------------
    
    async def _load_agent_cards(self) -> None:
        """
        Load agent cards from all configured A2A servers.
        
        Fetches agent metadata to understand available capabilities
        and update system message with available remote agents.
        """
        logger.info("Loading agent cards from A2A servers...")
        
        async def fetch_card(server_url: str) -> Optional[dict]:
            try:
                url = urljoin(server_url, "/.well-known/agent.json")
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers={"Accept": "application/json"}) as resp:
                        if resp.ok:
                            return await resp.json()
                        logger.error(f"Failed to fetch card from {url}: {resp.status}")
                        return None
            except Exception as e:
                logger.error(f"Error fetching agent card from {server_url}: {e}")
                return None
        
        # Fetch all cards in parallel
        tasks = [fetch_card(url) for url in self.a2a_servers]
        results = await asyncio.gather(*tasks)
        
        self.agent_cards = [
            AgentCard.model_validate(card)
            for card in results if card is not None
        ]
        
        logger.info(f"Loaded {len(self.agent_cards)} agent cards")
        
        # Update system message with available agents
        if self.agent_cards:
            self._append_agent_info_to_system_message()
    
    def _append_agent_info_to_system_message(self) -> None:
        """Append available agent information to system message."""
        formatted_cards = []
        
        for i, card in enumerate(self.agent_cards):
            # Format skills
            skills_str = "    None specified"
            if card.skills:
                skills = []
                for skill in card.skills:
                    skill_info = f"    • {skill.name}: {skill.description}"
                    if skill.examples:
                        skill_info += f"\n      Examples: {', '.join(skill.examples)}"
                    skills.append(skill_info)
                skills_str = "\n".join(skills)
            
            server_url = self.a2a_servers[i] if i < len(self.a2a_servers) else 'Unknown'
            formatted_cards.append(
                f"{i + 1}. {card.name or 'Unnamed Agent'}\n"
                f"   Server URL: {server_url}\n"
                f"   Description: {card.description or 'No description'}\n"
                f"   Skills:\n{skills_str}"
            )
        
        agents_info = "\n\nAvailable Remote Agents:\n" + "\n\n".join(formatted_cards)
        self.system_message.content += agents_info
    
    # -------------------------------------------------------------------------
    # A2A Tools
    # -------------------------------------------------------------------------
    
    def _get_a2a_tools(self) -> list:
        """
        Create A2A communication tools for the agent.
        
        Returns:
            List of LangChain tools for A2A communication
        """
        
        @tool("list_remote_agents")
        async def list_remote_agents() -> str:
            """
            List all available remote A2A agents with their capabilities.
            
            Returns:
                Formatted list of available agents
            """
            logger.info("Listing remote agents")
            
            if not self.agent_cards:
                return "No remote A2A servers are currently available."
            
            formatted = []
            for i, card in enumerate(self.agent_cards):
                skills_str = "    None specified"
                if card.skills:
                    skills = [f"    • {s.name}: {s.description}" for s in card.skills]
                    skills_str = "\n".join(skills)
                
                server_url = self.a2a_servers[i] if i < len(self.a2a_servers) else 'Unknown'
                formatted.append(
                    f"{i + 1}. {card.name or 'Unnamed'}\n"
                    f"   URL: {server_url}\n"
                    f"   Description: {card.description or 'No description'}\n"
                    f"   Skills:\n{skills_str}"
                )
            
            return "Available remote A2A servers:\n\n" + "\n\n".join(formatted)
        
        class SendMessageInput(BaseModel):
            server_url: str = Field(description="URL of the remote A2A server")
            message: str = Field(description="Message content to send")
            task_id: Optional[str] = Field(
                default=None,
                description="TaskId for continuing existing conversation"
            )
        
        @tool("send_message", args_schema=SendMessageInput)
        async def send_message(
            server_url: str,
            message: str,
            task_id: Optional[str] = None
        ) -> str:
            """
            Send a message to a remote A2A agent.
            
            Use this to communicate with CareFlow Pulse Agent for medical
            context, patient lookups, and clinical guidance.
            
            Args:
                server_url: Target A2A server URL
                message: Message to send
                task_id: Optional task ID for conversation continuity
            
            Returns:
                Agent response
            """
            # --- MODEL ARMOR INPUT SCAN ---
            logger.info(f"Model Armor scanning A2A prompt to {server_url}")
            input_scan = await model_armor_client.scan_prompt(message)
            if input_scan.get("is_blocked"):
                logger.warning(f"Model Armor BLOCKED A2A message to {server_url}")
                return "Error: Security policy blocked this request."
            # ------------------------------

            logger.info(f"Sending A2A message to {server_url}")
            
            if server_url not in self.a2a_servers:
                self.a2a_servers.append(server_url)
            
            try:
                request_id = int(uuid.uuid1().int >> 64)
                
                message_payload = {
                    "messageId": str(uuid.uuid4()),
                    "kind": "message",
                    "role": "user",
                    "parts": [{"kind": "text", "text": message}],
                }
                
                if task_id:
                    message_payload["taskId"] = task_id
                
                rpc_request = {
                    "jsonrpc": "2.0",
                    "method": "message/stream",
                    "id": request_id,
                    "params": {"message": message_payload}
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        server_url,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "text/event-stream"
                        },
                        json=rpc_request
                    ) as response:
                        if not response.ok:
                            return f"Error: {response.status} {await response.text()}"
                        
                        # Process SSE response
                        final_result = None
                        returned_task_id = None
                        
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            if line.startswith("data:"):
                                try:
                                    data = json.loads(line[5:].strip())
                                    if data.get("result", {}).get("final"):
                                        final_result = self._extract_a2a_response(
                                            data["result"]
                                        )
                                        returned_task_id = data["result"].get("taskId")
                                except json.JSONDecodeError:
                                    pass
                        
                        print(f"\n[CALLER -> CAREFLOW]: {message}")
                        print(f"[CAREFLOW -> CALLER]: {final_result}\n")
                        
                        # --- MODEL ARMOR OUTPUT SCAN ---
                        if final_result:
                            logger.info(f"Model Armor scanning A2A response from {server_url}")
                            output_scan = await model_armor_client.sanitize_response(final_result)
                            if output_scan.get("is_blocked"):
                                final_result = "[REDACTED] Clinical data blocked by security policy."
                            else:
                                final_result = output_scan.get("sanitized_text", final_result)
                        # -------------------------------

                        result = f"Response: {final_result}"
                        if returned_task_id:
                            result += f"\nTaskId: {returned_task_id}"
                        return result
                        
            except Exception as e:
                return f"Failed to send message: {str(e)}"
        
        class SubscribeInput(BaseModel):
            server_url: str = Field(description="URL of the remote A2A server")
            task_id: str = Field(description="Task ID to subscribe to")
        
        @tool("subscribe_to_task", args_schema=SubscribeInput)
        async def subscribe_to_task(server_url: str, task_id: str) -> str:
            """Subscribe to real-time updates for a task."""
            return f"Subscribed to task {task_id}"
        
        class WebhookInput(BaseModel):
            server_url: str = Field(description="URL of the remote A2A server")
            task_id: str = Field(description="Task ID")
            webhook_url: str = Field(description="Webhook URL for notifications")
        
        @tool("register_webhook", args_schema=WebhookInput)
        async def register_webhook(
            server_url: str,
            task_id: str,
            webhook_url: str
        ) -> str:
            """Register a webhook for push notifications."""
            try:
                request_id = int(uuid.uuid1().int >> 64)
                rpc_request = {
                    "jsonrpc": "2.0",
                    "method": "tasks/pushNotificationConfig/set",
                    "id": request_id,
                    "params": {
                        "taskId": task_id,
                        "pushNotificationConfig": {
                            "url": webhook_url,
                            "format": "json"
                        }
                    }
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        server_url,
                        headers={"Content-Type": "application/json"},
                        json=rpc_request
                    ) as response:
                        if not response.ok:
                            return f"Error: {await response.text()}"
                        return f"Webhook registered for task {task_id}"
            except Exception as e:
                return f"Failed to register webhook: {str(e)}"
        
        return [list_remote_agents, send_message, subscribe_to_task, register_webhook]
    
    def _extract_a2a_response(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Extract text response from A2A status update event.
        
        Args:
            event: A2A event data
        
        Returns:
            Extracted text or None
        """
        try:
            if event.get("kind") != "status-update" or not event.get("final"):
                return None
            
            # Try various response structures
            status = event.get("status", {})
            message = status.get("message", {})
            
            # Try message.text
            if message.get("text"):
                return message["text"]
            
            # Try message.parts
            if message.get("parts"):
                parts = message["parts"]
                return "".join(
                    p.get("text", "") for p in parts if p.get("kind") == "text"
                )
            
            # Try direct event text
            if event.get("text"):
                return event["text"]
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting A2A response: {e}")
            return None
    
    # -------------------------------------------------------------------------
    # WebSocket Communication
    # -------------------------------------------------------------------------
    
    async def send_ws_message(
        self,
        text: Optional[str] = None,
        source: Optional[str] = None
    ) -> None:
        """
        Send a message through the WebSocket channel.
        
        Args:
            text: Text content to speak via TTS
            source: Audio source URL to play
        """
        if not self.ws:
            logger.warning("WebSocket not connected")
            return
        
        message = None
        
        if text:
            message = {
                "type": "text",
                "token": text,
                "last": True,
                "interruptible": False,
                "preemptible": False,
            }
        elif source:
            message = {
                "type": "play",
                "source": source,
                "interruptible": False,
                "preemptible": True,
            }
        
        if message:
            await self.ws.send_text(json.dumps(message))
    
    # -------------------------------------------------------------------------
    # Message Streaming
    # -------------------------------------------------------------------------
    
    async def stream_message(
        self,
        user_message: str,
        session_data: SessionData
    ) -> AsyncGenerator[str, None]:
        """
        Stream agent response to a user message.
        
        Processes the message through the ReAct agent and yields
        response chunks for real-time voice synthesis.
        
        Args:
            user_message: Text from user (STT result)
            session_data: Session state with conversation history
        
        Yields:
            Response text chunks
        """
        try:
            session_id = session_data.call_sid or 'default-session'
            
            # Convert conversation history to LangChain format
            messages: List[BaseMessage] = []
            for msg in session_data.conversation:
                if msg.role == 'user':
                    messages.append(HumanMessage(content=msg.content))
                else:
                    messages.append(AIMessage(content=msg.content))
            
            # Play typing indicator sound
            await self.send_ws_message(
                source=f"https://{NGROK_URL}/public/keyboard-typing.mp3"
            )
            
            # --- MODEL ARMOR INPUT SCAN ---
            logger.info(f"Model Armor scanning patient message: {user_message[:50]}...")
            input_scan = await model_armor_client.scan_prompt(user_message)
            if input_scan.get("is_blocked"):
                logger.warning("Model Armor BLOCKED patient message")
                yield "I'm sorry, I cannot process that request due to my safety guidelines. How else can I help you today?"
                return
            # ------------------------------

            messages.append(HumanMessage(content=user_message))
            
            # Stream from agent
            streams = self.agent.astream_events(
                {
                    "messages": [self.system_message] + messages
                    if self.system_message else messages,
                },
                config={
                    "configurable": {"thread_id": session_id},
                    "callbacks": [],
                },
                version="v2"
            )
            
            full_response = ''
            
            async for stream in streams:
                if stream.get('event') in ('on_chat_model_stream', 'on_llm_stream'):
                    data = stream.get('data')
                    if not isinstance(data, dict):
                        continue
                    
                    chunk = data.get('chunk')
                    if not isinstance(chunk, AIMessageChunk):
                        continue
                    
                    content = chunk.content
                    if content and isinstance(content, str):
                        full_response += content
                        # Note: We stream chunks for voice, but we'll log the full response for final sanitization
                        # Since we yield here, we can't easily sanitize the whole block AFTER it's spoken.
                        # For the Hackathon, we will scan the FULL response at the end for audit/logging.
                        yield content
            
            # --- MODEL ARMOR OUTPUT SCAN (Audit) ---
            logger.info(f"Model Armor auditing caller response for PII/PHI")
            await model_armor_client.sanitize_response(full_response)
            # ---------------------------------------

            logger.info(f"Agent response for session {session_id}: {full_response[:100]}...")
            
        except Exception as e:
            logger.error(f"Error in stream_message: {e}")
            yield "I apologize, but I encountered an error. Please try again."


# =============================================================================
# CONFIGURATION AND INITIALIZATION
# =============================================================================

def load_config() -> dict:
    """
    Load agent configuration from YAML file.
    
    Returns:
        Configuration dictionary
    
    Raises:
        Exception: If config file cannot be loaded
    """
    try:
        # Find config file
        current_file = Path(__file__).resolve()
        config_path = current_file.parent / 'config.yaml'
        
        if not config_path.exists():
            config_path = Path.cwd() / 'config.yaml'
        
        logger.info(f"Loading config from: {config_path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Override with environment variable if set
        agent_url = os.environ.get(
            "CAREFLOW_AGENT_URL",
            f"http://localhost:{config['servers'][0]['port']}"
        )
        config['servers'] = [{"name": "CareFlow Agent", "port": None, "url": agent_url}]
        
        return config
        
    except Exception as e:
        logger.error(f"Error loading config.yaml: {e}")
        raise


# Load configuration
config = load_config()

# Build A2A server URLs
a2a_server_urls = [
    s.get('url') or f"http://localhost:{s['port']}"
    for s in config['servers']
    if s.get('url') or s.get('port')
]

# Create agent instance
agent = CallerAgent(
    system_message=config['client']['system'] + CALLER_SYSTEM_PROMPT,
    a2a_servers=a2a_server_urls
)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['agent', 'CallerAgent', 'call_patient']
