"""
CareFlow Pulse - Patient Rounds Orchestration
Handles scheduling triggers and retry logic for patient rounds.
"""
import os
import json
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from a2a.types import Message, Role, Part, TextPart
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue

logger = logging.getLogger(__name__)


async def trigger_agent_rounds(
    root_agent,
    schedule_hour: int,
    schedule_slot: str,
    retry_mode: bool = False,
    pending_patients: Optional[list] = None
):
    """
    Background task to trigger the agent to start patient rounds.
    
    Args:
        root_agent: The CareFlowAgent instance
        schedule_hour: The hour of rounds (8, 12, 20)
        schedule_slot: The slot key (e.g., "2026-01-23_08")
        retry_mode: If True, this is a retry call
        pending_patients: Optional list of specific patients to call (for retries)
    """
    try:
        # Construct the trigger message
        if retry_mode:
            prompt_text = f"RETRY TRIGGER: {schedule_hour}:00 AM rounds. Call only pending patients from slot {schedule_slot}."
        else:
            prompt_text = f"start daily rounds for {schedule_hour}:00"
        
        logger.info(f"🚀 Triggering Agent: {prompt_text}")
        
        # Create A2A message
        message = Message(
            messageId=str(uuid.uuid4()),
            kind="message",
            role=Role.user,
            parts=[Part(root=TextPart(kind="text", text=prompt_text))]
        )
        
        # Create request context
        context = RequestContext(
            request={"message": message},
            context_id=f"rounds-{schedule_slot}",
            task_id=str(uuid.uuid4())
        )
        
        # Use the executor
        from app.app_utils.executor.careflow_executor import CareFlowAgentExecutor
        executor = CareFlowAgentExecutor(root_agent)
        
        class SimpleEventQueue(EventQueue):
            async def enqueue_event(self, event):
                pass
        
        event_queue = SimpleEventQueue()
        
        # Execute (this will run the agent)
        await executor.execute(context, event_queue)
        
        logger.info(f"✅ Agent execution completed for {schedule_slot}")
        
    except Exception as e:
        logger.error(f"❌ Error triggering agent rounds: {e}", exc_info=True)


async def schedule_retry_task(schedule_hour: int, schedule_slot: str):
    """
    Schedule a Cloud Task to call /retry-rounds in 15 minutes.
    
    This is the safety net that catches patients who were unreachable.
    """
    try:
        from google.cloud import tasks_v2
        from google.protobuf import timestamp_pb2
        
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "careflow-478811")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        queue_name = os.environ.get("CLOUD_TASKS_QUEUE", "patient-retries")
        service_url = os.environ.get("SERVICE_URL", "http://localhost:8080")
        
        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project_id, location, queue_name)
        
        # Schedule for 15 minutes from now
        scheduled_time = datetime.now(timezone.utc) + timedelta(minutes=15)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(scheduled_time)
        
        # Build task payload
        payload = {
            "scheduleHour": schedule_hour,
            "scheduleSlot": schedule_slot,
            "triggeredAt": datetime.now(timezone.utc).isoformat()
        }
        
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{service_url}/retry-rounds",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode(),
            },
            "schedule_time": timestamp,
        }
        
        # Add OIDC token for authenticated Cloud Run
        service_account = os.environ.get("SCHEDULER_SERVICE_ACCOUNT")
        if service_account:
            task["http_request"]["oidc_token"] = {
                "service_account_email": service_account,
                "audience": service_url,
            }
        
        response = client.create_task(parent=parent, task=task)
        logger.info(f"✅ Scheduled retry task for {schedule_slot} at {scheduled_time.strftime('%H:%M')}. Task: {response.name}")
        
    except ImportError:
        logger.warning("⚠️ google-cloud-tasks not available. Retry scheduling disabled (dev mode).")
    except Exception as e:
        logger.error(f"❌ Failed to schedule retry task: {e}", exc_info=True)
