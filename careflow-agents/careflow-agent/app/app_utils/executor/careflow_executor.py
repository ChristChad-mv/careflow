import uuid
"""
CareFlow Pulse A2A Executor
Handles execution requests from remote agents via A2A protocol.
"""
import logging
import base64
from datetime import datetime
from typing import Optional, Set

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    Task,
    TaskStatus,
    TaskState,
    TaskStatusUpdateEvent,
    Message,
    Role,
    Part,
    TextPart,
)
from google.genai import types as genai_types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts import InMemoryArtifactService

from ...agent import root_agent, CareFlowAgent
from ...core.security.model_armor import ModelArmorClient
from ...plugins.model_armor_plugin import ModelArmorPlugin

logger = logging.getLogger(__name__)

class CareFlowAgentExecutor(AgentExecutor):
    """
    Executes tasks using the CareFlow Pulse Agent.
    """
    def __init__(self, agent: CareFlowAgent):
        self.agent = agent
        self.cancelled_tasks: Set[str] = set()
        
        # Initialize ADK Runner once for the executor lifetime
        model_armor_client = ModelArmorClient()
        model_armor_plugin = ModelArmorPlugin(client=model_armor_client)

        self.runner = Runner(
            app_name=self.agent.name,
            agent=self.agent,
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
            artifact_service=InMemoryArtifactService(),
            plugins=[model_armor_plugin]
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.task_id:
            self.cancelled_tasks.add(context.task_id)
        logger.info(f"Cancelled task {context.task_id}")

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info("Executing CareFlow Agent Task")
        user_message: Optional[Message] = context.message
        currentTask = context.current_task

        if not user_message:
            logger.error("No user message provided")
            return

        # Determine IDs
        msg_context_id = getattr(user_message, 'contextId', None) or getattr(user_message, 'context_id', None)
        msg_message_id = getattr(user_message, 'messageId', None) or getattr(user_message, 'message_id', None)
        
        task_context_id = getattr(currentTask, 'contextId', None) or getattr(currentTask, 'context_id', None) if currentTask else None
        req_context_id = getattr(context, 'context_id', None)

        taskId = (getattr(currentTask, 'id', None) if currentTask else getattr(context, 'task_id', None)) or str(uuid.uuid4())
        contextId = msg_context_id or task_context_id or req_context_id or str(uuid.uuid4())
        messageId = msg_message_id

        logger.info(f"[{contextId}] Processing message {messageId} for task {taskId}")

        # 1. Publish initial Task event if new
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

        # 2. Publish "working" status
        working_status = TaskStatusUpdateEvent(
            kind="status-update",
            taskId=taskId,
            contextId=contextId,
            status=TaskStatus(
                state=TaskState.working,
                message=Message(
                    kind="message",
                    role=Role.agent,
                    messageId=str(uuid.uuid4()),
                    parts=[Part(root=TextPart(kind="text", text="Pulse Agent received task, processing..."))],
                    taskId=taskId,
                    contextId=contextId,
                ),
                timestamp=datetime.now().isoformat(),
            ),
            final=False,
        )
        await event_queue.enqueue_event(working_status)

        try:
            session = await self.runner.session_service.get_session(
                session_id=contextId,
                user_id="a2a_caller",
                app_name=self.agent.name
            )
            
            if not session:
                logger.info(f"Creating session for context {contextId}")
                session = await self.runner.session_service.create_session(
                    session_id=contextId, 
                    user_id="a2a_caller",
                    app_name=self.agent.name,
                    state={}
                )

            # 4. Extract all parts (text and multimodal) and run the agent
            gemini_parts = []
            for part in user_message.parts:
                if part.root.kind == "text" and hasattr(part.root, "text"):
                    gemini_parts.append(genai_types.Part.from_text(text=part.root.text))
                elif part.root.kind == "file":
                    file_data = part.root.file
                    if hasattr(file_data, "bytes"):
                        # Inline audio/file data (base64) — sent by Caller Agent or eval
                        gemini_parts.append(genai_types.Part.from_bytes(
                            data=base64.b64decode(file_data.bytes),
                            mime_type=file_data.mime_type or "application/octet-stream"
                        ))
            
            if not gemini_parts:
                gemini_parts = [genai_types.Part.from_text(text="Please check the patient status.")]

            input_content = genai_types.Content(
                role="user",
                parts=gemini_parts
            )
            
            response_text = ""
            thought_text = ""
            
            async for event in self.runner.run_async(
                user_id="a2a_caller",
                session_id=session.id,
                new_message=input_content
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    # Collect regular text
                    response_text = "\n".join([p.text for p in event.content.parts if p.text and not getattr(p, 'thought', False)])
                    # Collect thinking/reflection
                    thought_text = "\n".join([p.text for p in event.content.parts if p.text and getattr(p, 'thought', False)])

            final_text = response_text or "Task completed (no text response)."

            # 5. Publish final success status
            # We include thoughts in metadata for transparency/evals
            final_message = Message(
                kind="message",
                role=Role.agent,
                messageId=str(uuid.uuid4()),
                parts=[Part(root=TextPart(kind="text", text=final_text.strip()))],
                taskId=taskId,
                contextId=contextId,
                metadata={
                    "reflection": thought_text.strip(),
                    "has_thoughts": bool(thought_text.strip())
                }
            )
            
            final_update = TaskStatusUpdateEvent(
                kind="status-update",
                taskId=taskId,
                contextId=contextId,
                status=TaskStatus(
                    state=TaskState.working,
                    message=final_message,
                    timestamp=datetime.now().isoformat(),
                ),
                final=True,
            )
            await event_queue.enqueue_event(final_update)

        except Exception as e:
            logger.error(f"Error executing agent: {e}", exc_info=True)
            error_update = TaskStatusUpdateEvent(
                kind="status-update",
                taskId=taskId,
                contextId=contextId,
                status=TaskStatus(
                    state=TaskState.failed,
                    message=Message(
                        kind="message",
                        role=Role.agent,
                        messageId=str(uuid.uuid4()),
                        parts=[Part(root=TextPart(kind="text", text=f"Error: {str(e)}"))],
                        taskId=taskId,
                        contextId=contextId,
                    ),
                    timestamp=datetime.now().isoformat(),
                ),
                final=True,
            )
            await event_queue.enqueue_event(error_update)
