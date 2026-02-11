"""
CareFlow Pulse Server
A2A Protocol Backend Entry Point with Scheduler Support.
"""
import os
import logging
import httpx
import uvicorn
import argparse
import sys
import json
from fastapi import FastAPI, Request
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.tasks.inmemory_push_notification_config_store import InMemoryPushNotificationConfigStore
from a2a.server.tasks.base_push_notification_sender import BasePushNotificationSender
from a2a.types import Message, Role, Part, TextPart

# Modularized Imports
from app.app_utils.config_loader import PORT, AGENT_NAME
from app.app_utils.telemetry import setup_telemetry
from app.agent import root_agent
from app.app_utils.executor.careflow_executor import CareFlowAgentExecutor
from app.schemas.agent_card.v1.careflow_card import get_pulse_agent_card
from app.app_utils.run_patient_rounds import trigger_agent_rounds, schedule_retry_task
from app.app_utils.retry_utils import get_schedule_slot_key

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Main FastAPI App
app = FastAPI(title="CareFlow Pulse Agent", version="1.0.0")

def create_a2a_app():
    """
    Initializes and returns the A2A Starlette application.
    """
    # 1. Initialize Executor and Stores
    executor = CareFlowAgentExecutor(root_agent)
    task_store = InMemoryTaskStore()
    push_config_store = InMemoryPushNotificationConfigStore()
    
    # 2. Setup Push Notifications
    http_client = httpx.AsyncClient()
    push_sender = BasePushNotificationSender(http_client, push_config_store)
    
    # 3. Initialize Request Handler
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
        push_config_store=push_config_store,
        push_sender=push_sender
    )

    # 4. Create App with Agent Card
    a2a_app = A2AStarletteApplication(
        agent_card=get_pulse_agent_card(),
        http_handler=request_handler
    ).build()
    
    # 5. Configure Telemetry for A2A
    setup_telemetry(a2a_app, service_name=AGENT_NAME)

    return a2a_app

# Initialize A2A Sub-App
a2a_subapp = create_a2a_app()

# Mount A2A app at root (to preserve existing JSON-RPC behavior)
# Track already-triggered round slots to prevent Cloud Scheduler double-fires
_TRIGGERED_SLOTS: set[str] = set()

@app.post("/trigger-rounds")
async def trigger_rounds(request: Request):
    """
    Endpoint triggered by Cloud Scheduler for daily patient rounds.
    
    Pattern:
    1. Idempotency check — reject duplicate triggers for same slot
    2. Respond 200 OK immediately (don't block Scheduler)
    3. Trigger agent in background
    4. Schedule Cloud Task for retry safety net (15min later)
    
    Payload: { "scheduleHour": 8, "timezone": "...", "environment": "..." }
    """
    import asyncio
    
    try:
        payload = await request.json()
        schedule_hour = payload.get("scheduleHour", 8)
        environment = payload.get("environment", "prod")
        
        logger.info(f"⏰ Scheduler Trigger Received: {schedule_hour}:00 ({environment})")
        
        # Get schedule slot key for idempotency
        schedule_slot = get_schedule_slot_key(schedule_hour)
        
        # Idempotency guard: reject duplicate triggers for the same slot
        if schedule_slot in _TRIGGERED_SLOTS:
            logger.warning(f"⚠️ Duplicate trigger for slot {schedule_slot} — already in progress")
            return {
                "status": "already_triggered",
                "scheduleSlot": schedule_slot,
                "message": f"Rounds for {schedule_slot} already triggered — ignoring duplicate"
            }
        _TRIGGERED_SLOTS.add(schedule_slot)
        
        # Cleanup old slots (keep only today's)
        today_prefix = schedule_slot.split("_")[0]  # "2026-02-10"
        stale = [s for s in _TRIGGERED_SLOTS if not s.startswith(today_prefix)]
        for s in stale:
            _TRIGGERED_SLOTS.discard(s)
        
        # 1. Fire background task (non-blocking)
        asyncio.create_task(trigger_agent_rounds(
            root_agent,
            schedule_hour,
            schedule_slot
        ))
        
        # 2. Schedule retry Cloud Task (safety net)
        asyncio.create_task(schedule_retry_task(schedule_hour, schedule_slot))
        
        # 3. Respond immediately
        return {
            "status": "triggered",
            "scheduleHour": schedule_hour,
            "scheduleSlot": schedule_slot,
            "message": f"Rounds triggered for {schedule_hour}:00, retry scheduled for {schedule_slot}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing scheduler trigger: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@app.post("/retry-rounds")
@app.post("/retry-call")
async def retry_rounds(request: Request):
    """
    Endpoint triggered by Cloud Tasks for individual patient retry or slot safety net.
    Handles both /retry-rounds and /retry-call.
    
    Receives: {patientId, retryCount, scheduleSlot, reason, scheduleHour}
    """
    import asyncio
    
    try:
        payload = await request.json()
        logger.info(f"🔄 Retry Trigger Received: {json.dumps(payload)}")
        
        # Extract fields
        patient_id = payload.get("patientId")
        retry_count = payload.get("retryCount", 1)
        schedule_slot = payload.get("scheduleSlot")
        schedule_hour = payload.get("scheduleHour")
        reason = payload.get("reason", payload.get("action", "unknown"))
        
        # Case A: Safety net for the whole slot (no patientId)
        if not patient_id:
            logger.info(f"🛡️ Running safety net for slot {schedule_slot}")
            asyncio.create_task(trigger_agent_rounds(
                root_agent,
                schedule_hour or 8,
                schedule_slot,
                retry_mode=True
            ))
            return {"status": "safety_net_triggered", "scheduleSlot": schedule_slot}
        
        # Case B: Specific patient retry
        logger.info(f"📞 Retry for patient {patient_id} (attempt #{retry_count})")
        
        # Check retry limit
        MAX_RETRIES = 3
        if retry_count >= MAX_RETRIES:
            logger.warning(f"⚠️ Max retries ({MAX_RETRIES}) reached for {patient_id}")
            await _create_max_retry_alert(patient_id, schedule_slot, retry_count)
            return {
                "status": "max_retries_reached",
                "patientId": patient_id,
                "retryCount": retry_count,
                "action": "critical_alert_created"
            }
        
        # Trigger single patient call via agent
        prompt = (
            f"RETRY_PATIENT: Call patient ID {patient_id} now. "
            f"This is retry attempt #{retry_count}. Schedule slot: {schedule_slot}. "
            f"Previous failure reason: {reason}."
        )
        
        asyncio.create_task(_trigger_agent_with_prompt(prompt, f"retry-{patient_id}-{retry_count}"))
        
        return {
            "status": "retry_initiated",
            "patientId": patient_id,
            "retryCount": retry_count,
            "scheduleSlot": schedule_slot
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing retry trigger: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": AGENT_NAME}


# Mount A2A sub-app AFTER defining specialized routes to avoid shadowing
app.mount("/", a2a_subapp)


async def _create_max_retry_alert(patient_id: str, schedule_slot: str, retry_count: int):
    """Create a CRITICAL alert when max retries reached."""
    try:
        from google.cloud import firestore
        from datetime import datetime, timezone
        
        db = firestore.AsyncClient(
            project=os.environ.get("GOOGLE_CLOUD_PROJECT", "careflow-478811"),
            database=os.environ.get("FIRESTORE_DATABASE", "careflow-db")
        )
        
        # Get patient name for alert
        patient_ref = db.collection("patients").document(patient_id)
        patient_doc = await patient_ref.get()
        patient_name = patient_doc.to_dict().get("name", "Unknown") if patient_doc.exists else "Unknown"
        
        # Create CRITICAL alert
        alert_data = {
            "patientId": patient_id,
            "patientName": patient_name,
            "riskLevel": "RED",
            "priority": "critical",
            "trigger": f"Patient unreachable after {retry_count} attempts",
            "aiBrief": f"URGENT: Unable to reach {patient_name} after {retry_count} call attempts for schedule slot {schedule_slot}. Manual follow-up required immediately.",
            "status": "active",
            "createdAt": datetime.now(timezone.utc),
            "scheduleSlot": schedule_slot,
            "retryCount": retry_count,
            "hospitalId": os.environ.get("HOSPITAL_ID", "HOSP001"),
        }
        
        await db.collection("alerts").add(alert_data)
        logger.info(f"🚨 Created CRITICAL alert for unreachable patient {patient_id}")
        
        # Update patient risk level to RED
        await patient_ref.update({
            "riskLevel": "RED",
            "lastRetryCount": retry_count,
            "updatedAt": datetime.now(timezone.utc)
        })
        
    except Exception as e:
        logger.error(f"❌ Failed to create max retry alert: {e}", exc_info=True)


async def _trigger_agent_with_prompt(prompt: str, context_id: str):
    """Trigger the agent with a specific prompt."""
    try:
        import uuid
        from a2a.types import Message, Role, Part, TextPart
        from a2a.server.agent_execution import RequestContext
        from a2a.server.events import EventQueue
        from app.app_utils.executor.careflow_executor import CareFlowAgentExecutor
        
        message = Message(
            messageId=str(uuid.uuid4()),
            kind="message",
            role=Role.user,
            parts=[Part(root=TextPart(kind="text", text=prompt))]
        )
        
        context = RequestContext(
            request={"message": message},
            context_id=context_id,
            task_id=str(uuid.uuid4())
        )
        
        executor = CareFlowAgentExecutor(root_agent)
        
        class SimpleEventQueue(EventQueue):
            async def enqueue_event(self, event):
                pass
        
        await executor.execute(context, SimpleEventQueue())
        logger.info(f"✅ Agent execution completed for {context_id}")
        
    except Exception as e:
        logger.error(f"❌ Error triggering agent: {e}", exc_info=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CareFlow Pulse Agent Server')
    parser.add_argument('--port', type=int, help='Port to run the server on')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    args = parser.parse_args()

    # Priority: Command Line > Config > Default
    run_port = args.port or int(PORT)
    
    logger.info(f"Starting CareFlow Server (FastAPI + A2A) on port {run_port}")
    uvicorn.run(app, host="0.0.0.0", port=run_port, reload=False)
