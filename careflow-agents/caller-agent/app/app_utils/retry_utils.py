"""
CareFlow Caller Agent - Retry Utilities
Handles retry scheduling for failed calls (busy/no-answer).
"""
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)


def get_schedule_slot_key(schedule_hour: int) -> str:
    """
    Generate a unique key for the current schedule slot.
    Format: YYYY-MM-DD_HH (e.g., "2026-01-21_08")
    """
    now = datetime.now(timezone.utc)
    return f"{now.strftime('%Y-%m-%d')}_{schedule_hour:02d}"


async def schedule_patient_retry(
    patient_id: str,
    reason: str,
    schedule_slot: Optional[str] = None,
    delay_seconds: int = 900,  # 15 minutes default
) -> bool:
    """
    Schedule a delayed retry for a patient call using Google Cloud Tasks.
    
    Args:
        patient_id: The patient document ID to retry.
        reason: Why the retry is needed (e.g., "busy", "no_answer").
        schedule_slot: The original schedule slot.
        delay_seconds: How long to wait before retrying (default 15 min).
    
    Returns:
        True if task was successfully scheduled, False otherwise.
    """
    try:
        from google.cloud import tasks_v2
        from google.protobuf import timestamp_pb2
        import json
        
        # Configuration from environment
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "careflow-478811")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        queue_name = os.environ.get("CLOUD_TASKS_QUEUE", "patient-retries")
        
        # Target is the Pulse Agent's retry endpoint
        pulse_agent_url = os.environ.get("CAREFLOW_AGENT_URL", "http://localhost:8080")
        
        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project_id, location, queue_name)
        
        # Calculate scheduled time
        scheduled_time = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(scheduled_time)
        
        # Build task payload - this will trigger /retry-rounds on Pulse Agent
        payload = {
            "action": "retry_patient_call",
            "patientId": patient_id,
            "reason": reason,
            "scheduleSlot": schedule_slot,
            "scheduledAt": datetime.now(timezone.utc).isoformat(),
        }
        
        # Extract schedule hour from slot if available
        if schedule_slot:
            schedule_hour = int(schedule_slot.split("_")[-1])
            payload["scheduleHour"] = schedule_hour
        
        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{pulse_agent_url}/retry-rounds",
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
                "audience": pulse_agent_url,
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
