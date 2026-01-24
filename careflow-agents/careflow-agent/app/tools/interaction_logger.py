"""
CareFlow Pulse - Patient Interaction Logger
ADK Python tool to log interactions in Firestore subcollections.
"""
import logging
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def log_interaction_subcollection(
    patient_id: str,
    content: str,
    call_sid: Optional[str] = None,
    schedule_slot: Optional[str] = None,
    interaction_type: str = "call_summary"
) -> str:
    """
    Log a patient interaction to the interactions subcollection.
    
    This is CRITICAL for the retry system to work - it marks patients
    as "already contacted" for idempotency.
    
    Args:
        patient_id: Patient document ID (e.g., "p_h1_001")
        content: Summary of the interaction
        call_sid: Twilio Call SID (if applicable)
        schedule_slot: Slot identifier (e.g., "2026-01-23_08")
        interaction_type: Type of interaction ("call_summary", "analysis", etc.)
    
    Returns:
        Success/error message
    """
    try:
        from google.cloud.firestore import AsyncClient
        import os
        
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "careflow-478811")
        database_id = os.environ.get("FIRESTORE_DATABASE", "careflow-db")
        
        # Create AsyncClient (does NOT support 'async with')
        db = AsyncClient(project=project_id, database=database_id)
        
        # Reference to subcollection
        interactions_ref = db.collection("patients").document(patient_id).collection("interactions")
        
        # Build interaction document
        interaction_data = {
            "timestamp": datetime.now(timezone.utc),
            "type": interaction_type,
            "sender": "ai",
            "content": content,
        }
        
        if call_sid:
            interaction_data["callSid"] = call_sid
        
        if schedule_slot:
            interaction_data["scheduleSlot"] = schedule_slot
        
        # Add to subcollection (AsyncClient returns tuple: (update_time, doc_ref))
        update_time, doc_ref = await interactions_ref.add(interaction_data)
        
        logger.info(f"✅ Logged interaction for patient {patient_id} (Doc ID: {doc_ref.id}, Slot: {schedule_slot})")
        
        return f"SUCCESS: Interaction logged for patient {patient_id}. Document ID: {doc_ref.id}"
        
    except Exception as e:
        error_msg = f"ERROR: Failed to log interaction for patient {patient_id}: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)
        return error_msg


# Export for agent
interaction_tools = [log_interaction_subcollection]

