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
app.mount("/", a2a_subapp)

@app.post("/trigger-rounds")
async def trigger_rounds(request: Request):
    """
    Endpoint triggered by Cloud Scheduler for daily patient rounds.
    
    Pattern:
    1. Respond 200 OK immediately (don't block Scheduler)
    2. Trigger agent in background
    3. Schedule Cloud Task for retry safety net (15min later)
    
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
async def retry_rounds(request: Request):
    """
    Endpoint triggered by Cloud Tasks for retry logic.
    
    This endpoint is called 15 minutes after initial trigger to catch patients
    who were unreachable (busy/no-answer).
    
    Uses get_pending_patients to find only those not yet contacted.
    """
    import asyncio
    
    try:
        payload = await request.json()
        schedule_hour = payload.get("scheduleHour")
        schedule_slot = payload.get("scheduleSlot")
        
        logger.info(f"🔄 Retry Trigger Received for slot {schedule_slot}")
        
        # Use get_pending_patients to find who's missing
        from app.tools.retry_tools import get_pending_patients
        from app.app_utils.config_loader import HOSPITAL_ID
        
        pending_json = await get_pending_patients(schedule_hour, HOSPITAL_ID)
        pending_data = json.loads(pending_json)
        
        if isinstance(pending_data, dict) and "error" in pending_data:
            logger.error(f"❌ Error fetching pending patients: {pending_data['error']}")
            return {"status": "error", "message": pending_data["error"]}
        
        pending_count = len(pending_data) if isinstance(pending_data, list) else 0
        
        if pending_count == 0:
            logger.info("✅ No pending patients. All successfully contacted!")
            return {"status": "complete", "pending": 0}
        
        logger.info(f"📋 Found {pending_count} pending patients. Triggering retry rounds...")
        
        # Trigger agent with RETRY context
        asyncio.create_task(trigger_agent_rounds(
            root_agent,
            schedule_hour, 
            schedule_slot, 
            retry_mode=True,
            pending_patients=pending_data
        ))
        
        return {
            "status": "retry_triggered",
            "pending": pending_count,
            "scheduleSlot": schedule_slot
        }
        
    except Exception as e:
        logger.error(f"❌ Error processing retry trigger: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CareFlow Pulse Agent Server')
    parser.add_argument('--port', type=int, help='Port to run the server on')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    args = parser.parse_args()

    # Priority: Command Line > Config > Default
    run_port = args.port or int(PORT)
    
    logger.info(f"Starting CareFlow Server (FastAPI + A2A) on port {run_port}")
    uvicorn.run(app, host="0.0.0.0", port=run_port, reload=False)
