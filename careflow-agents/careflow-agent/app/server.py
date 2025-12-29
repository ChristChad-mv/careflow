import os
import sys
import uuid
import logging
from datetime import datetime
from typing import Optional, Set, List

from a2a.server.apps import A2AStarletteApplication
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.tasks.inmemory_push_notification_config_store import InMemoryPushNotificationConfigStore
from a2a.server.tasks.base_push_notification_sender import BasePushNotificationSender
from a2a.server.events import EventQueue
import httpx
from a2a.types import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    AgentProvider,
    Task,
    TaskStatus,
    TaskState,
    TaskStatusUpdateEvent,
    Message,
    Role,
    Part,
    TextPart,
)
from google.adk.agents import LlmAgent
from google.genai import types as genai_types

# OpenTelemetry Imports
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.starlette import StarletteInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Import the existing agent configuration
from agent import root_agent, CareFlowAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CareFlowAgentExecutor(AgentExecutor):
    """
    Executes tasks using the CareFlow Custom Agent.
    """
    def __init__(self, agent: CareFlowAgent):
        self.agent = agent
        self.cancelled_tasks: Set[str] = set()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.task_id:
            self.cancelled_tasks.add(context.task_id)
        logger.info(f"Cancelled task {context.task_id}")

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.info("Executing CareFlow Agent")
        user_message: Optional[Message] = context.message
        currentTask = context.current_task

        if not user_message:
            logger.error("No user message provided")
            return

        # Determine IDs
        logger.info(f"User Message: {user_message}")
        
        # Try to get contextId/taskId safely (handle snake_case vs camelCase)
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
                    parts=[Part(root=TextPart(kind="text", text="CareFlow Agent is analyzing..."))],
                    taskId=taskId,
                    contextId=contextId,
                ),
                timestamp=datetime.now().isoformat(),
            ),
            final=False,
        )
        await event_queue.enqueue_event(working_status)

        try:
            # 3. Run the Custom Agent using ADK Runner
            # Since CareFlowAgent implements _run_async_impl, we must use the Runner to execute it.
            
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
            from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
            from google.adk.artifacts import InMemoryArtifactService
            
            # Initialize Runner with our Custom Agent
            runner = Runner(
                app_name=self.agent.name,
                agent=self.agent,
                session_service=InMemorySessionService(),
                memory_service=InMemoryMemoryService(),
                artifact_service=InMemoryArtifactService(),
            )
            
            # Create a session
            session = await runner.session_service.create_session(
                app_name=self.agent.name,
                user_id="a2a_caller",
                state={},
                session_id=contextId
            )
            
            # Extract user text
            user_text = ""
            for part in user_message.parts:
                if part.root.kind == "text" and hasattr(part.root, "text"):
                    user_text += part.root.text + "\n"
            
            if not user_text.strip():
                user_text = "Please check the patient status."

            # Prepare input content
            input_content = genai_types.Content(
                role="user",
                parts=[genai_types.Part.from_text(text=user_text)]
            )
            
            response_text = ""
            logger.info("Starting runner.run_async...")
            
            # Execute the agent via Runner
            async for event in runner.run_async(
                user_id="a2a_caller",
                session_id=session.id,
                new_message=input_content
            ):
                logger.info(f"Received event: {event}")
                # Capture the final response text from the event stream
                if event.is_final_response():
                    if event.content and event.content.parts:
                        response_text = "\n".join([p.text for p in event.content.parts if p.text])
                        logger.info(f"Final response text: {response_text}")

            logger.info(f"Runner finished. Agent response: {response_text}")
            
            final_text = response_text
            if not final_text:
                final_text = "Task completed (no text response)."

            # 4. Publish final success status
            final_message = Message(
                kind="message",
                role=Role.agent,
                messageId=str(uuid.uuid4()),
                parts=[Part(root=TextPart(kind="text", text=final_text.strip()))],
                taskId=taskId,
                contextId=contextId,
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


def create_app():
    # Define the Agent Card
    # Get the service URL from environment (Cloud Run provides this as SERVICE_URL)
    service_url = os.environ.get("SERVICE_URL", "http://localhost:8000/")
    
    careflow_card = AgentCard(
        name="CareFlow Pulse Agent",
        description="Post-hospitalization patient monitoring agent. Can access patient data and generate alerts.",
        url=service_url,
        provider=AgentProvider(
            organization="CareFlow",
            url="https://careflow.example.com",
        ),
        version="1.0.0",
        capabilities=AgentCapabilities(
            streaming=True,
            pushNotifications=True,
            stateTransitionHistory=True,
        ),
        defaultInputModes=["text"],
        defaultOutputModes=["text", "task-status"],
        skills=[
            AgentSkill(
                id="patient_monitoring",
                name="Patient Monitoring",
                description="Check patient status, symptoms, and alerts.",
                tags=["health", "patient", "monitoring"],
                examples=[
                    "Check status of patient P001",
                    "Are there any critical alerts?",
                    "Analyze symptoms for Sarah Jones"
                ],
                inputModes=["text"],
                outputModes=["text", "task-status"],
            )
        ],
    )

    # Initialize Executor and Handler
    executor = CareFlowAgentExecutor(root_agent)
    task_store = InMemoryTaskStore()
    push_config_store = InMemoryPushNotificationConfigStore()
    
    # Create HTTP client for push notifications
    # Note: In a real app, you might want to manage the client lifecycle better
    http_client = httpx.AsyncClient()
    push_sender = BasePushNotificationSender(http_client, push_config_store)
    
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
        push_config_store=push_config_store,
        push_sender=push_sender
    )

    # Create App
    app = A2AStarletteApplication(
        agent_card=careflow_card,
        http_handler=request_handler
    )
    
    starlette_app = app.build()

    # --- Telemetry Configuration ---
    logger.info("Configuring Telemetry (OpenTelemetry + Jaeger)")
    resource = Resource(attributes={
        "service.name": "careflow-pulse-agent",
        "service.version": "1.0.0",
        "deployment.environment": os.environ.get("DEPLOYMENT_ENV", "development")
    })
    
    # Create and register TracerProvider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # Configure Jaeger Exporter (OTLP gRPC)
    # Default to localhost:4317, or use OTLP_ENDPOINT env var
    otlp_endpoint = os.environ.get("OTLP_ENDPOINT", "http://localhost:4317")
    try:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        logger.info(f"Telemetry enabled. Exporting to {otlp_endpoint}")
    except Exception as e:
        logger.error(f"Failed to initialize OTLP exporter: {e}")

    # Instrument the Starlette app
    StarletteInstrumentor().instrument_app(starlette_app)

    return starlette_app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description='CareFlow Pulse Agent Server')
    parser.add_argument('--port', type=int, help='Port to run the server on')
    args = parser.parse_args()

    # Priority: Command Line > Environment Variable > Default 8000
    port = args.port or int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting CareFlow A2A Server on port {port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
