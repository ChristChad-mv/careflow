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
Version: 2.0.0
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiohttp
from fastapi import WebSocket
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from a2a.types import AgentCard

# Internal imports - modular structure
from .config import NGROK_URL
from .app_utils.config_loader import load_config, get_a2a_server_urls
from .app_utils.conversation_relay import SessionData
from .app_utils.llm import ModelConfig, get_model
from .app_utils.prompts.system_prompts import CALLER_SYSTEM_PROMPT
from .core.security.model_armor import ModelArmorClient
from .tools import call_patient, create_a2a_tools


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# MODEL ARMOR CLIENT
# =============================================================================

model_armor_client = ModelArmorClient()


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
        a2a_tools = create_a2a_tools(
            agent_cards=self.agent_cards,
            a2a_servers=self.a2a_servers,
            extract_response_fn=self._extract_a2a_response
        )
        
        self.agent = create_react_agent(
            model=self.model,
            tools=a2a_tools + [call_patient],
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
                from urllib.parse import urljoin
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
            skills_str = "    None specified"
            if card.skills:
                skills = [
                    f"    • {skill.name}: {skill.description}"
                    + (f"\n      Examples: {', '.join(skill.examples)}" if skill.examples else "")
                    for skill in card.skills
                ]
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
    # A2A Response Extraction
    # -------------------------------------------------------------------------
    
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
            logger.info(f"🔍 Model Armor scanning patient message: '{user_message[:50]}...'")
            input_scan = await model_armor_client.scan_prompt(user_message)
            
            if input_scan.get("is_blocked"):
                blocked_cats = input_scan.get("blocked_categories", [])
                logger.warning(f"🚨 Model Armor BLOCKED patient message. Categories: {blocked_cats}")
                yield "I'm sorry, I cannot process that request due to my safety guidelines. How else can I help you today?"
                return
            else:
                logger.debug("✅ Model Armor input scan passed")
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
                        yield content
            
            # --- MODEL ARMOR OUTPUT SCAN (Audit & Sanitize) ---
            logger.info("🔍 Model Armor auditing caller response for PII/PHI...")
            sanitization_result = await model_armor_client.sanitize_response(full_response)
            
            if sanitization_result.get("is_blocked"):
                logger.error("🚨 Model Armor BLOCKED entire response - critical safety issue detected")
                # Log for audit but don't return blocked content
            elif sanitization_result.get("redactions_applied"):
                redacted = sanitization_result.get("redactions_applied", [])
                logger.warning(f"🔒 Model Armor applied redactions: {', '.join(redacted)}")
                # In production: consider if we should return sanitized_text instead
                # For now, we audit but allow original (since it's voice - hard to redact mid-stream)
            else:
                logger.debug("✅ Model Armor output scan passed (no PHI detected)")
            # --------------------------------------------------

            logger.info(f"Agent response for session {session_id}: {full_response[:100]}...")
            
        except Exception as e:
            logger.error(f"Error in stream_message: {e}")
            yield "I apologize, but I encountered an error. Please try again."


# =============================================================================
# AGENT INITIALIZATION
# =============================================================================

# Load configuration
config = load_config()

# Build A2A server URLs
a2a_server_urls = get_a2a_server_urls(config)

# Create agent instance
agent = CallerAgent(
    system_message=config['client']['system'] + CALLER_SYSTEM_PROMPT,
    a2a_servers=a2a_server_urls
)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['agent', 'CallerAgent', 'call_patient']
