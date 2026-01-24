"""
CareFlow Pulse - Retry Utilities

Provides retry decorators and Cloud Tasks integration for robust
patient round orchestration.

Author: CareFlow Engineering Team
Version: 1.0.0
"""

import os
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import aiohttp

logger = logging.getLogger(__name__)

# =============================================================================
# RETRY DECORATORS
# =============================================================================

# Retry for A2A network calls (connection errors, 5xx responses)
a2a_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((aiohttp.ClientError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)


# =============================================================================
# CLOUD TASKS SCHEDULER (Delayed Retries)
# =============================================================================

async def schedule_patient_retry(
    patient_id: str,
    reason: str,
    schedule_slot: Optional[str] = None,
    delay_seconds: int = 900,  # 15 minutes default
    pulse_agent_url: Optional[str] = None,
) -> bool:
    """
    Schedule a delayed retry for a patient call using Google Cloud Tasks.
    
    Args:
        patient_id: The patient document ID to retry.
        reason: Why the retry is needed (e.g., "busy", "no_answer").
        schedule_slot: The original schedule slot.
        delay_seconds: How long to wait before retrying (default 15 min).
        pulse_agent_url: The URL of the Pulse Agent to trigger.
    
    Returns:
        True if task was successfully scheduled, False otherwise.
    """
    try:
        from google.cloud import tasks_v2
        from google.protobuf import timestamp_pb2
        
        # Configuration from environment
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "careflow-478811")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        queue_name = os.environ.get("CLOUD_TASKS_QUEUE", "patient-retries")
        target_url = pulse_agent_url or os.environ.get("SERVICE_URL", "http://localhost:8080")
        
        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project_id, location, queue_name)
        
        # Calculate scheduled time
        scheduled_time = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(scheduled_time)
        
        # Build task payload
        payload = {
            "action": "retry_patient_call",
            "patientId": patient_id,
            "reason": reason,
            "scheduleSlot": schedule_slot,
            "scheduledAt": datetime.now(timezone.utc).isoformat(),
        }
        
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{target_url}/retry-call",
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
                "audience": target_url,
            }
        
        response = client.create_task(parent=parent, task=task)
        logger.info(f"✅ Scheduled retry for patient {patient_id} in {delay_seconds}s. Task: {response.name}")
        return True
        
    except ImportError:
        logger.warning("⚠️ google-cloud-tasks not available. Retry scheduling disabled.")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to schedule retry for {patient_id}: {e}")
        return False


# =============================================================================
# IDEMPOTENCY CHECK
# =============================================================================

def get_schedule_slot_key(schedule_hour: int) -> str:
    """
    Generate a unique key for the current schedule slot.
    Format: YYYY-MM-DD_HH (e.g., "2026-01-21_08")
    """
    now = datetime.now(timezone.utc)
    return f"{now.strftime('%Y-%m-%d')}_{schedule_hour:02d}"


async def check_patient_already_called(
    patient_id: str,
    schedule_slot: str,
    mcp_client=None,
) -> bool:
    """
    Check if a patient has already been called in the given schedule slot.
    Uses the interactions subcollection to verify.
    
    Args:
        patient_id: The patient document ID.
        schedule_slot: The slot key (e.g., "2026-01-21_08").
        mcp_client: Optional MCP toolbox client (for future direct query).
    
    Returns:
        True if patient was already called, False otherwise.
    """
    # For now, we'll use Firestore directly since MCP doesn't have a 
    # subcollection query tool yet. This can be migrated to MCP later.
    try:
        from google.cloud import firestore
        
        db = firestore.AsyncClient(database="careflow-db")
        interactions_ref = db.collection("patients").document(patient_id).collection("interactions")
        
        # Query for an interaction with this schedule slot
        query = interactions_ref.where("scheduleSlot", "==", schedule_slot).limit(1)
        docs = [doc async for doc in query.stream()]
        
        if docs:
            logger.info(f"⏭️ Patient {patient_id} already called in slot {schedule_slot}. Skipping.")
            return True
        return False
        
    except Exception as e:
        logger.warning(f"⚠️ Could not check idempotency for {patient_id}: {e}. Proceeding with call.")
        return False


async def mark_patient_call_initiated(
    patient_id: str,
    schedule_slot: str,
    call_sid: Optional[str] = None,
) -> bool:
    """
    Mark that a patient call has been initiated for a schedule slot.
    This is the "checkpoint" that enables idempotency.
    
    Args:
        patient_id: The patient document ID.
        schedule_slot: The slot key.
        call_sid: Optional Twilio Call SID if available.
    
    Returns:
        True if marked successfully.
    """
    try:
        from google.cloud import firestore
        
        db = firestore.AsyncClient(database="careflow-db")
        interactions_ref = db.collection("patients").document(patient_id).collection("interactions")
        
        await interactions_ref.add({
            "type": "call_attempt",
            "scheduleSlot": schedule_slot,
            "status": "initiated",
            "callSid": call_sid,
            "timestamp": firestore.SERVER_TIMESTAMP,
        })
        
        logger.info(f"📝 Marked call initiated for patient {patient_id} in slot {schedule_slot}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to mark call initiated for {patient_id}: {e}")
        return False


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'a2a_retry',
    'schedule_patient_retry',
    'get_schedule_slot_key',
    'check_patient_already_called',
    'mark_patient_call_initiated',
]
