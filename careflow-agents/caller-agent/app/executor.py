import logging
import uuid
import os
from datetime import datetime
from typing import Optional, List, Dict, Set, Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    Role,
    AgentCard,
    TaskState,
    TaskStatus,
    AgentProvider,
    AgentSkill,
    AgentCapabilities,
    AgentExtension,
    Message,
    Task,
    TaskStatusUpdateEvent,
    Part,
    TextPart,
    DataPart,
)
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage, AIMessageChunk

from agent import Agent
from utils.conversation_relay import SessionData

logger = logging.getLogger(__name__)

# --- Latency Configuration ---
# Estimated latency for tools (in milliseconds)
latency_by_tools = {
    "call_patient": 2000,
    "send_remote_agent_task": 1000
}

# --- Agent Card Definition ---
caller_agent_card = AgentCard(
    name="Caller Agent",
    description="Voice interface for CareFlow Pulse. Handles phone calls with patients and relays information to the Healthcare Agent.",
    url="http://localhost:8080/",
    provider=AgentProvider(
        organization="CareFlow Pulse",
        url="https://careflow-pulse.com",
    ),
    version="1.0.0",
    capabilities=AgentCapabilities(
        streaming=True,
        pushNotifications=False,
        stateTransitionHistory=True,
        extensions=[
            AgentExtension(
                uri="https://github.com/twilio-labs/a2a-latency-extension",
                description="Provides latency updates for tasks. The server will send DataPart messages with latency information for each tool call.",
                required=True,
                params={
                    "skillLatency": latency_by_tools,
                    "supportsLatencyTaskUpdates": True
                }
            )
        ],
    ),
    securitySchemes=None,
    security=None,
    defaultInputModes=["text"],
    defaultOutputModes=["text", "task-status"],
    skills=[
        AgentSkill(
            id="voice_call_handling",
            name="Voice Call Handling",
            description="Handle voice calls with patients in French, relay information to Healthcare Agent",
            tags=["voice", "twilio", "healthcare", "french"],
            examples=[
                "Call patient about medication",
                "Follow up on patient symptoms",
                "Conduct wellness check",
            ],
            inputModes=["text"],
            outputModes=["text", "task-status"],
        )
    ],
    supportsAuthenticatedExtendedCard=False,
)

# Simple store for contexts (In-memory for now, could be replaced by Redis or similar)
MESSAGE_HISTORY_CACHE: Dict[str, List[Message]] = {}

class CallerAgentExecutor(AgentExecutor):
    def __init__(self, agent: Agent):
        self.agent = agent
        self.cancelled_tasks: Set[str] = set()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel a task by ID."""
        if context.task_id in self.cancelled_tasks:
            return
        if context.task_id:
            self.cancelled_tasks.add(context.task_id)
        logger.error(f"Cancelled task {context.task_id}")

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info("Executing Caller Agent via A2A")
        user_message: Optional[Message] = context.message
        currentTask = context.current_task

        if not user_message:
            logger.error("No user message provided")
            return

        # Determine IDs
        taskId = (getattr(currentTask, 'id', None) if currentTask else getattr(context, 'task_id', None)) or str(uuid.uuid4())
        
        msg_context_id = getattr(user_message, 'contextId', None) or getattr(user_message, 'context_id', None)
        task_context_id = getattr(currentTask, 'contextId', None) or getattr(currentTask, 'context_id', None) if currentTask else None
        ctx_context_id = getattr(context, 'context_id', None)
        
        contextId = msg_context_id or task_context_id or ctx_context_id or str(uuid.uuid4())
        
        messageId = getattr(user_message, 'messageId', None) or getattr(user_message, 'message_id', None)

        logger.info(f"[{contextId}] Processing message {messageId} for task {taskId}")

        # 1. Publish initial Task event if it's a new task
        if not currentTask:
            initial_task = Task(
                kind="task",
                id=taskId,
                contextId=contextId,
                status=TaskStatus(
                    state=TaskState.submitted,
                    timestamp=datetime.now().isoformat(),
                ),
                history=[user_message],
                metadata=user_message.metadata if user_message.metadata else {},
            )
            await event_queue.enqueue_event(initial_task)

        # 2. Publish "working" status update
        working_status_update = TaskStatusUpdateEvent(
            kind="status-update",
            taskId=taskId,
            contextId=contextId,
            status=TaskStatus(
                state=TaskState.working,
                message=Message(
                    kind="message",
                    role=Role.agent,
                    messageId=str(uuid.uuid4()),
                    parts=[
                        Part(root=TextPart(kind="text", text="Processing your request..."))
                    ],
                    taskId=taskId,
                    contextId=contextId,
                ),
                timestamp=datetime.now().isoformat(),
            ),
            final=False,
        )
        await event_queue.enqueue_event(working_status_update)

        # 3. Prepare messages for LangGraph agent
        # We maintain a separate history cache for A2A context mapping
        history_for_agent = MESSAGE_HISTORY_CACHE.get(contextId, [])
        if not any(m.messageId == messageId for m in history_for_agent):
            history_for_agent.append(user_message)
        MESSAGE_HISTORY_CACHE[contextId] = history_for_agent

        # Convert A2A messages to LangChain BaseMessage format
        langchain_messages: List[BaseMessage] = []
        for m in history_for_agent[:-1]: # All except current
            text_content = ""
            for p in m.parts:
                if p.root.kind == "text" and hasattr(p.root, "text"):
                    text_content += p.root.text + "\n"
            
            if text_content.strip():
                if m.role == Role.agent:
                    langchain_messages.append(AIMessage(content=text_content))
                else:
                    langchain_messages.append(HumanMessage(content=text_content))

        # Extract current user message text
        current_message_text = ""
        for p in user_message.parts:
            if p.root.kind == "text" and hasattr(p.root, "text"):
                current_message_text += p.root.text + "\n"
        current_message_text = current_message_text.strip()

        if not current_message_text:
            logger.warning("No text found in user message")
            # Handle failure...
            return

        # Add current message to LangChain messages
        # Note: The Agent.stream_message method usually takes just the user message and session data
        # But here we want to use the underlying agent directly or pass history via session data.
        # The Agent class uses `session_data.conversation` to build history.
        # We can construct a dummy SessionData with the history we have.
        
        # However, `Agent.stream_message` does:
        # messages = [system_message] + history + [HumanMessage(user_message)]
        # So we can just pass the history via SessionData.
        
        # Construct SessionData from langchain_messages
        # Wait, SessionData expects ConversationMessage objects
        from utils.conversation_relay import ConversationMessage
        
        conversation_history = []
        for msg in langchain_messages:
            role = 'assistant' if isinstance(msg, AIMessage) else 'user'
            conversation_history.append(ConversationMessage(
                role=role,
                content=str(msg.content),
                timestamp=datetime.now().isoformat()
            ))
            
        session_data = SessionData(
            connected_at=datetime.now().isoformat(),
            call_sid=contextId, # Use contextId as session ID
            conversation=conversation_history
        )

        try:
            # 4. Run the agent streaming
            # We use self.agent.stream_message which yields strings
            # But we might want more granular control (events) like in MovieAgentExecutor
            # Agent.stream_message uses self.agent.agent.astream_events internally but only yields content chunks.
            # To support latency updates (tool calls), we need to access the raw events.
            
            # Let's call self.agent.agent.astream_events directly here, similar to how Agent.stream_message does it.
            
            # Prepare input for LangGraph agent
            messages = [self.agent.system_message] + langchain_messages + [HumanMessage(content=current_message_text)]
            
            streams = self.agent.agent.astream_events(
                {
                    "messages": messages,
                },
                config={
                    "configurable": {"thread_id": contextId},
                    "callbacks": [],
                },
                version="v2"
            )

            final_response = ""
            
            async for stream in streams:
                if taskId in self.cancelled_tasks:
                    logger.info(f"Request cancelled for task: {taskId}")
                    # Send cancel event...
                    return

                event_type = stream.get("event")
                
                # Handle Tool Calls (Latency Updates)
                if event_type == "on_tool_start":
                    data = stream.get("data", {})
                    tool_name = stream.get("name")
                    if tool_name:
                        # Send latency update
                        tool_update_event = TaskStatusUpdateEvent(
                            kind="status-update",
                            taskId=taskId,
                            contextId=contextId,
                            status=TaskStatus(
                                state=TaskState.working,
                                message=Message(
                                    kind="message",
                                    role=Role.agent,
                                    messageId=str(uuid.uuid4()),
                                    parts=[Part(root=DataPart(
                                        kind="data",
                                        data={
                                            "latency": latency_by_tools.get(tool_name, 0)
                                        }
                                    ))],
                                    taskId=taskId,
                                    contextId=contextId,
                                    metadata={"toolName": tool_name}
                                ),
                                timestamp=datetime.now().isoformat(),
                            ),
                            final=False,
                        )
                        await event_queue.enqueue_event(tool_update_event)

                # Handle Streaming Content
                elif event_type in ('on_chat_model_stream', 'on_llm_stream'):
                    data = stream.get('data')
                    if not isinstance(data, dict): continue
                    chunk = data.get('chunk')
                    if not isinstance(chunk, AIMessageChunk): continue
                    content = chunk.content
                    if content and isinstance(content, str):
                        final_response += content
                        # We could stream partial text updates if A2A supports it (it does via multiple messages or parts)
                        # But typically we wait for final or send chunks. 
                        # For now let's just accumulate for the final response to match the MovieAgent example structure
                        # which sends one final message. 
                        # OR we could send intermediate updates? 
                        # The MovieAgent example seems to only send final response text.

            logger.info(f"Agent response: {final_response}")

            # 5. Publish final task status update
            agent_message = Message(
                kind="message",
                role=Role.agent,
                messageId=str(uuid.uuid4()),
                parts=[Part(root=TextPart(kind="text", text=final_response or "Completed."))],
                taskId=taskId,
                contextId=contextId,
            )
            
            # Update history
            history_for_agent.append(agent_message)
            MESSAGE_HISTORY_CACHE[contextId] = history_for_agent

            final_update = TaskStatusUpdateEvent(
                kind="status-update",
                taskId=taskId,
                contextId=contextId,
                status=TaskStatus(
                    state=TaskState.completed,
                    message=agent_message,
                    timestamp=datetime.now().isoformat(),
                ),
                final=True,
            )
            await event_queue.enqueue_event(final_update)

        except Exception as error:
            logger.error(f"Error executing agent: {error}", exc_info=True)
            # Send error event
