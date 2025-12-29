"""
CareFlow Pulse - Caller Agent A2A Executor

This module implements the A2A (Agent-to-Agent) protocol executor for the
Caller Agent. It handles incoming A2A requests and translates them to
LangGraph agent invocations.

Architecture:
    - Implements AgentExecutor interface from a2a.server
    - Manages task lifecycle (submitted -> working -> completed)
    - Converts between A2A Message format and LangChain BaseMessage
    - Streams responses back via EventQueue

Author: CareFlow Pulse Team
Version: 1.0.0
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, HumanMessage

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)

from agent import CallerAgent
from .app_utils.conversation_relay import ConversationMessage, SessionData


logger = logging.getLogger(__name__)


# =============================================================================
# AGENT CARD DEFINITION
# =============================================================================

# Service URL from environment (for Cloud Run deployment)
SERVICE_URL = os.environ.get("SERVICE_URL", "http://localhost:8080/")

caller_agent_card = AgentCard(
    name="CareFlow Caller Agent",
    description=(
        "Voice interface for CareFlow Pulse. Handles phone calls with patients "
        "and relays information to the Healthcare Agent via A2A protocol."
    ),
    url=SERVICE_URL,
    provider=AgentProvider(
        organization="CareFlow Pulse",
        url="https://careflow-pulse.com",
    ),
    version="1.0.0",
    capabilities=AgentCapabilities(
        streaming=True,
        pushNotifications=False,
        stateTransitionHistory=True,
    ),
    securitySchemes=None,
    security=None,
    defaultInputModes=["text"],
    defaultOutputModes=["text", "task-status"],
    skills=[
        AgentSkill(
            id="voice_call_handling",
            name="Voice Call Handling",
            description=(
                "Handle voice calls with patients, conduct wellness interviews, "
                "and relay information to Healthcare Agent"
            ),
            tags=["voice", "healthcare", "patient-communication"],
            examples=[
                "Call patient about medication",
                "Follow up on patient symptoms",
                "Conduct wellness check",
                "follow-up calls"
            ],
            inputModes=["text"],
            outputModes=["text", "task-status"],
        )
    ],
    supportsAuthenticatedExtendedCard=False,
)


# =============================================================================
# MESSAGE HISTORY CACHE
# =============================================================================

# Simple in-memory cache for conversation context
# Key: contextId, Value: List of Messages
MESSAGE_HISTORY_CACHE: Dict[str, List[Message]] = {}


# =============================================================================
# A2A EXECUTOR
# =============================================================================

class CallerAgentExecutor(AgentExecutor):
    """
    A2A Protocol executor for the Caller Agent.
    
    Translates A2A requests into LangGraph agent invocations and
    streams responses back through the A2A event queue.
    
    Attributes:
        agent: The underlying CallerAgent instance
        cancelled_tasks: Set of task IDs that have been cancelled
    """
    
    def __init__(self, agent: CallerAgent):
        """
        Initialize the executor.
        
        Args:
            agent: CallerAgent instance to delegate execution to
        """
        self.agent = agent
        self.cancelled_tasks: Set[str] = set()
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Cancel a running task.
        
        Args:
            context: Request context containing task ID
            event_queue: Event queue (unused for cancellation)
        """
        if context.task_id and context.task_id not in self.cancelled_tasks:
            self.cancelled_tasks.add(context.task_id)
            logger.info(f"Cancelled task: {context.task_id}")
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute an A2A request.
        
        Processes the incoming message through the LangGraph agent
        and streams status updates and responses via the event queue.
        
        Args:
            context: Request context with message and task info
            event_queue: Queue for publishing A2A events
        """
        user_message = context.message
        current_task = context.current_task
        
        if not user_message:
            logger.error("No user message provided in context")
            return
        
        # Determine task and context IDs
        task_id = self._get_task_id(context, current_task)
        context_id = self._get_context_id(context, user_message, current_task)
        message_id = getattr(user_message, 'messageId', None) or getattr(user_message, 'message_id', None)
        
        logger.info(f"[{context_id}] Processing message {message_id} for task {task_id}")
        
        # Publish initial task if new
        if not current_task:
            await self._publish_initial_task(
                event_queue, task_id, context_id, user_message
            )
        
        # Publish working status
        await self._publish_working_status(event_queue, task_id, context_id)
        
        # Extract message text
        message_text = self._extract_message_text(user_message)
        if not message_text:
            logger.warning("No text content found in message")
            return
        
        # Build conversation history
        session_data = self._build_session_data(context_id, user_message)
        langchain_messages = self._build_langchain_messages(context_id)
        
        try:
            # Execute agent
            final_response = await self._execute_agent(
                task_id, context_id, message_text, langchain_messages
            )
            
            # Publish completion
            await self._publish_completion(
                event_queue, task_id, context_id, final_response
            )
            
        except Exception as e:
            logger.error(f"Error executing agent: {e}", exc_info=True)
            await self._publish_error(event_queue, task_id, context_id, str(e))
    
    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------
    
    def _get_task_id(self, context: RequestContext, current_task: Optional[Task]) -> str:
        """Extract or generate task ID."""
        if current_task and hasattr(current_task, 'id'):
            return current_task.id
        if context.task_id:
            return context.task_id
        return str(uuid.uuid4())
    
    def _get_context_id(
        self,
        context: RequestContext,
        message: Message,
        current_task: Optional[Task]
    ) -> str:
        """Extract or generate context ID."""
        # Try message context ID
        msg_ctx = getattr(message, 'contextId', None) or getattr(message, 'context_id', None)
        if msg_ctx:
            return msg_ctx
        
        # Try task context ID
        if current_task:
            task_ctx = getattr(current_task, 'contextId', None) or getattr(current_task, 'context_id', None)
            if task_ctx:
                return task_ctx
        
        # Try request context
        req_ctx = getattr(context, 'context_id', None)
        if req_ctx:
            return req_ctx
        
        return str(uuid.uuid4())
    
    def _extract_message_text(self, message: Message) -> str:
        """Extract text content from A2A message."""
        text_parts = []
        for part in message.parts:
            if part.root.kind == "text" and hasattr(part.root, "text"):
                text_parts.append(part.root.text)
        return "\n".join(text_parts).strip()
    
    def _build_session_data(self, context_id: str, message: Message) -> SessionData:
        """Build SessionData from message history."""
        # Update message history cache
        history = MESSAGE_HISTORY_CACHE.get(context_id, [])
        message_id = getattr(message, 'messageId', None) or getattr(message, 'message_id', None)
        
        if not any(
            (getattr(m, 'messageId', None) or getattr(m, 'message_id', None)) == message_id
            for m in history
        ):
            history.append(message)
        MESSAGE_HISTORY_CACHE[context_id] = history
        
        # Convert to ConversationMessage format
        conversation_history = []
        for msg in history[:-1]:  # Exclude current message
            text = self._extract_message_text(msg)
            if text:
                role = 'assistant' if msg.role == Role.agent else 'user'
                conversation_history.append(ConversationMessage(
                    role=role,
                    content=text,
                    timestamp=datetime.now().isoformat()
                ))
        
        return SessionData(
            connected_at=datetime.now().isoformat(),
            call_sid=context_id,
            conversation=conversation_history
        )
    
    def _build_langchain_messages(self, context_id: str) -> List[BaseMessage]:
        """Build LangChain message list from history."""
        history = MESSAGE_HISTORY_CACHE.get(context_id, [])
        messages: List[BaseMessage] = []
        
        for msg in history[:-1]:  # Exclude current message
            text = self._extract_message_text(msg)
            if text:
                if msg.role == Role.agent:
                    messages.append(AIMessage(content=text))
                else:
                    messages.append(HumanMessage(content=text))
        
        return messages
    
    async def _execute_agent(
        self,
        task_id: str,
        context_id: str,
        message_text: str,
        history: List[BaseMessage]
    ) -> str:
        """Execute the LangGraph agent and collect response."""
        messages = [self.agent.system_message] + history + [HumanMessage(content=message_text)]
        
        streams = self.agent.agent.astream_events(
            {"messages": messages},
            config={
                "configurable": {"thread_id": context_id},
                "callbacks": [],
                "recursion_limit": 100
            },
            version="v2"
        )
        
        final_response = ""
        
        async for stream in streams:
            # Check for cancellation
            if task_id in self.cancelled_tasks:
                logger.info(f"Task cancelled: {task_id}")
                return "Task cancelled"
            
            event_type = stream.get("event")
            if event_type in ('on_chat_model_stream', 'on_llm_stream'):
                data = stream.get('data')
                if isinstance(data, dict):
                    chunk = data.get('chunk')
                    if isinstance(chunk, AIMessageChunk) and chunk.content:
                        if isinstance(chunk.content, str):
                            final_response += chunk.content
        
        logger.info(f"Agent response: {final_response[:200]}...")
        return final_response
    
    # -------------------------------------------------------------------------
    # Event Publishing
    # -------------------------------------------------------------------------
    
    async def _publish_initial_task(
        self,
        event_queue: EventQueue,
        task_id: str,
        context_id: str,
        message: Message
    ) -> None:
        """Publish initial task event."""
        task = Task(
            kind="task",
            id=task_id,
            contextId=context_id,
            status=TaskStatus(
                state=TaskState.submitted,
                timestamp=datetime.now().isoformat(),
            ),
            history=[message],
            metadata=message.metadata if message.metadata else {},
        )
        await event_queue.enqueue_event(task)
    
    async def _publish_working_status(
        self,
        event_queue: EventQueue,
        task_id: str,
        context_id: str
    ) -> None:
        """Publish working status update."""
        status_update = TaskStatusUpdateEvent(
            kind="status-update",
            taskId=task_id,
            contextId=context_id,
            status=TaskStatus(
                state=TaskState.working,
                message=Message(
                    kind="message",
                    role=Role.agent,
                    messageId=str(uuid.uuid4()),
                    parts=[Part(root=TextPart(kind="text", text="Processing your request..."))],
                    taskId=task_id,
                    contextId=context_id,
                ),
                timestamp=datetime.now().isoformat(),
            ),
            final=False,
        )
        await event_queue.enqueue_event(status_update)
    
    async def _publish_completion(
        self,
        event_queue: EventQueue,
        task_id: str,
        context_id: str,
        response: str
    ) -> None:
        """Publish task completion event."""
        agent_message = Message(
            kind="message",
            role=Role.agent,
            messageId=str(uuid.uuid4()),
            parts=[Part(root=TextPart(kind="text", text=response or "Task processed."))],
            taskId=task_id,
            contextId=context_id,
        )
        
        # Update history cache
        history = MESSAGE_HISTORY_CACHE.get(context_id, [])
        history.append(agent_message)
        MESSAGE_HISTORY_CACHE[context_id] = history
        
        final_update = TaskStatusUpdateEvent(
            kind="status-update",
            taskId=task_id,
            contextId=context_id,
            status=TaskStatus(
                state=TaskState.completed,
                message=agent_message,
                timestamp=datetime.now().isoformat(),
            ),
            final=True,
        )
        await event_queue.enqueue_event(final_update)
    
    async def _publish_error(
        self,
        event_queue: EventQueue,
        task_id: str,
        context_id: str,
        error: str
    ) -> None:
        """Publish task error event."""
        error_message = Message(
            kind="message",
            role=Role.agent,
            messageId=str(uuid.uuid4()),
            parts=[Part(root=TextPart(kind="text", text=f"Error: {error}"))],
            taskId=task_id,
            contextId=context_id,
        )
        
        error_update = TaskStatusUpdateEvent(
            kind="status-update",
            taskId=task_id,
            contextId=context_id,
            status=TaskStatus(
                state=TaskState.failed,
                message=error_message,
                timestamp=datetime.now().isoformat(),
            ),
            final=True,
        )
        await event_queue.enqueue_event(error_update)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['CallerAgentExecutor', 'caller_agent_card']
