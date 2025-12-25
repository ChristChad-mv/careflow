import os
import sys
from src.utils.config import OPENAI_API_KEY, TMDB_API_KEY, SUPPORTS_EXTENSION, SUPPORTS_LATENCY_TASK_UPDATES, get_env_int
import uuid
from typing import Set, Optional, Dict, List
from datetime import datetime
from a2a.server.agent_execution import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.apps import A2AStarletteApplication
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.agent_execution import RequestContext
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
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from src.server.agent import run_movie_agent_streaming, FinalState
from src.server.tools import latecy_by_tools

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables are now loaded from config module
# OPENAI_API_KEY and TMDB_API_KEY are validated during import

if SUPPORTS_EXTENSION:
    logger.info("Extensions support is enabled")
if SUPPORTS_LATENCY_TASK_UPDATES:
    logger.info("Latency task updates support is enabled")

# Simple store for contexts
MESSAGE_HISTORY_CACHE: Dict[str, List[Message]] = {}


class MovieAgentExecutor(AgentExecutor):
    """MovieAgentExecutor implements the agent's core logic."""

    def __init__(self):
        self.cancelled_tasks: Set[str] = set()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel a task by ID."""
        if context.task_id in self.cancelled_tasks:
            return
        if context.task_id:
            self.cancelled_tasks.add(context.task_id)
        logger.error(f"Cancelled task {context.task_id}")

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute the movie agent with the given request context."""
        logger.info("Executing agent")
        user_message: Optional[Message] = context.message
        currentTask = context.current_task
        if not user_message:
            logger.error("No user message provided")
            return

        # Determine IDs for the task and context
        taskId = (currentTask.id if currentTask else context.task_id) or str(uuid.uuid4())
        contextId = user_message.contextId or (currentTask.contextId if currentTask else context.context_id) or str(uuid.uuid4())
        messageId = user_message.messageId

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
                history=[user_message],  # Start history with the current user message
                metadata=user_message.metadata if user_message.metadata else {},  # Carry over metadata
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
                        Part(root=TextPart(kind="text", text="Processing your question, hang tight!"))
                    ],
                    taskId=taskId,
                    contextId=contextId,
                ),
                timestamp=datetime.now().isoformat(),
            ),
            final=False,
        )
        await event_queue.enqueue_event(working_status_update)

        # 3. Prepare messages for Langgraph agent
        history_for_agent = MESSAGE_HISTORY_CACHE.get(contextId, [])
        if not any(m.messageId == messageId for m in history_for_agent):
            history_for_agent.append(user_message)
        MESSAGE_HISTORY_CACHE[contextId] = history_for_agent

        # Convert A2A messages to Langgraph format
        message_history: List[BaseMessage] = []
        for m in history_for_agent[:-1]:
            text_content: str = ""
            for p in m.parts:
                if p.root.kind == "text" and hasattr(p.root, "text"):
                    text_content += p.root.text + "\n"

            if text_content.strip():  # Only add non-empty messages
                if m.role == Role.agent:
                    message_history.append(AIMessage(content=text_content))
                else:
                    message_history.append(HumanMessage(content=text_content))

        current_message_text = ""
        for p in user_message.parts:
            if p.root.kind == "text" and hasattr(p.root, "text"):
                current_message_text += p.root.text + "\n"
        current_message_text = current_message_text.strip()

        if not current_message_text:
            logger.info(f"No valid text message found for task {taskId}.")
            failure_update = TaskStatusUpdateEvent(
                kind="status-update",
                taskId=taskId,
                contextId=contextId,
                status=TaskStatus(
                    state=TaskState.failed,
                    message=Message(
                        kind="message",
                        role=Role.agent,
                        messageId=str(uuid.uuid4()),
                        parts=[Part(root=TextPart(kind="text", text="No message found to process."))],
                        taskId=taskId,
                        contextId=contextId,
                    ),
                    timestamp=datetime.now().isoformat(),
                ),
                final=True,
            )
            await event_queue.enqueue_event(failure_update)
            return

        # Get goal from metadata if available
        goal = (currentTask.metadata.get("goal") if currentTask and currentTask.metadata else None or
                user_message.metadata.get("goal") if user_message.metadata else None)

        try:
            # 4. Run the Langgraph agent with streaming
            agent_generator = run_movie_agent_streaming(
                current_message_text,
                goal,
                message_history,
            )
            final_response: Optional[str] = None
            final_state: Optional[FinalState] = None

            async for update in agent_generator:
                # Check if the request has been cancelled
                if taskId in self.cancelled_tasks:
                    logger.info(f"Request cancelled for task: {taskId}")
                    cancelled_update = TaskStatusUpdateEvent(
                        kind="status-update",
                        taskId=taskId,
                        contextId=contextId,
                        status=TaskStatus(
                            state=TaskState.canceled,
                            timestamp=datetime.now().isoformat(),
                        ),
                        final=True,
                    )
                    await event_queue.enqueue_event(cancelled_update)
                    return

                # Publish streaming update for tool calls
                if update.type == "tool_call":
                    # Only send tool update events if latency task updates are enabled
                    if SUPPORTS_LATENCY_TASK_UPDATES:
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
                                            "latency": latecy_by_tools.get(update.tool_name, 0)
                                        }
                                    ))],
                                    taskId=taskId,
                                    contextId=contextId,
                                    metadata={
                                        "toolName": update.tool_name
                                    } if update.tool_name else {}
                                ),
                                timestamp=datetime.now().isoformat(),
                            ),
                            final=False,
                        )
                        await event_queue.enqueue_event(tool_update_event)

                elif update.type == "final_response":
                    final_response = update.content
                    final_state = update.final_state

            # Check if the request has been cancelled after completion
            if taskId in self.cancelled_tasks:
                logger.info(f"Request cancelled for task: {taskId}")
                cancelled_update = TaskStatusUpdateEvent(
                    kind="status-update",
                    taskId=taskId,
                    contextId=contextId,
                    status=TaskStatus(
                        state=TaskState.canceled,
                        timestamp=datetime.now().isoformat(),
                    ),
                    final=True,
                )
                await event_queue.enqueue_event(cancelled_update)
                return

            final_a2a_state = TaskState.input_required if final_state == FinalState.input_required else TaskState.completed
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
            history_for_agent.append(agent_message)
            MESSAGE_HISTORY_CACHE[contextId] = history_for_agent

            final_update = TaskStatusUpdateEvent(
                kind="status-update",
                taskId=taskId,
                contextId=contextId,
                status=TaskStatus(
                    state=final_a2a_state,
                    message=agent_message,
                    timestamp=datetime.now().isoformat(),
                ),
                final=True,
            )
            await event_queue.enqueue_event(final_update)

            logger.info(f"Task {taskId} finished with state: {final_a2a_state}")

        except Exception as error:
            logger.info(f"Error processing task {taskId}:", error)
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
                        parts=[Part(root=TextPart(kind="text", text=f"Agent error: {str(error)}"))],
                        taskId=taskId,
                        contextId=contextId,
                    ),
                    timestamp=datetime.now().isoformat(),
                ),
                final=True,
            )
            await event_queue.enqueue_event(error_update)


# --- Server Setup ---

# Initialize extensions list
extensions: List[AgentExtension] = []

# Check for extension support
if SUPPORTS_EXTENSION:
    extension = AgentExtension(
        uri="https://github.com/twilio-labs/a2a-latency-extension",
        description="This extension provides latency updates for tasks. The server will send DataPart messages with latency information for each tool call.",
        required=True,
        params={
            "skillLatency": latecy_by_tools
        }
    )

    if SUPPORTS_LATENCY_TASK_UPDATES:
        if extension.params is None:
            extension.params = {}
        extension.params["supportsLatencyTaskUpdates"] = True

    extensions.append(extension)

# Create agent card
movie_agent_card = AgentCard(
    name="Movie Agent",
    description="An agent that can answer questions about movies and actors using TMDB.",
    url="http://localhost:41241/",
    provider=AgentProvider(
        organization="A2A Samples",
        url="https://example.com/a2a-samples",
    ),
    version="0.0.2",
    capabilities=AgentCapabilities(
        streaming=True,
        pushNotifications=False,
        stateTransitionHistory=True,
        extensions=extensions if extensions else None,
    ),
    securitySchemes=None,
    security=None,
    defaultInputModes=["text"],
    defaultOutputModes=["text", "task-status"],
    skills=[
        AgentSkill(
            id="general_movie_chat",
            name="General Movie Chat",
            description="Answer general questions or chat about movies, actors, directors.",
            tags=["movies", "actors", "directors"],
            examples=[
                "Tell me about the plot of Inception.",
                "Recommend a good sci-fi movie.",
                "Who directed The Matrix?",
                "What other movies has Scarlett Johansson been in?",
                "Find action movies starring Keanu Reeves",
                "Which came out first, Jurassic Park or Terminator 2?",
            ],
            inputModes=["text"],
            outputModes=["text", "task-status"],
        )
    ],
    supportsAuthenticatedExtendedCard=False,
)


def create_app():
    """Create and configure the FastAPI app"""
    task_store = InMemoryTaskStore()
    agent_executor = MovieAgentExecutor()
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=task_store

    )
    app = A2AStarletteApplication(
        agent_card=movie_agent_card,
        http_handler=request_handler
    )

    port = get_env_int("PORT", 41241)

    # Log startup information
    logger.info(f"[MovieAgent] Server ready to start on http://localhost:{port}")
    logger.info(f"[MovieAgent] Agent Card: http://localhost:{port}/.well-known/agent.json")
    logger.info("[MovieAgent] Press Ctrl+C to stop the server")

    return app.build()


# Create the app instance
app = create_app()

# If running directly
if __name__ == "__main__":
    import uvicorn
    port = get_env_int("PORT", 41241)
    uvicorn.run("src.server.app:app", host="0.0.0.0", port=port, reload=True)
