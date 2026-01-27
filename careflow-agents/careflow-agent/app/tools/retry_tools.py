"""
CareFlow Pulse - Retry Tools
Tools for intelligent patient retry management using Firestore SDK.
"""
import logging
import json
from typing import Optional

logger = logging.getLogger(__name__)


async def get_pending_patients(
    scheduleHour: int,
    hospitalId: str
) -> str:
    """
    Get ONLY patients who have NOT been successfully contacted yet for this schedule slot today.
    
    Uses Firestore SDK directly to:
    1. Query patients collection for the given schedule and hospital
    2. Check each patient's interactions subcollection
    3. Return only those without a logged interaction for today's slot
    
    Args:
        scheduleHour: The hour of the schedule (8, 12, or 20)
        hospitalId: The hospital ID to filter by
        
    Returns:
        JSON string containing the list of pending patients
    """
    from google.cloud.firestore import AsyncClient, Query
    from app.app_utils.retry_utils import get_schedule_slot_key
    import os
    
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "careflow-478811")
    database_id = os.environ.get("FIRESTORE_DATABASE", "careflow-db")
    
    try:
        # Initialize Firestore client
        db = AsyncClient(project=project_id, database=database_id)
        
        # Get today's schedule slot (e.g., "2026-01-23_08")
        schedule_slot = get_schedule_slot_key(scheduleHour)
        
        # Query patients collection
        patients_ref = db.collection("patients")
        query = patients_ref.where("hospitalId", "==", hospitalId) \
                            .where("status", "==", "active") \
                            .where("scheduleHour", "==", scheduleHour)
        
        # Fetch all matching patients
        patients_docs = query.stream()
        
        pending_patients = []
        skipped_count = 0
        
        async for patient_doc in patients_docs:
            patient_id = patient_doc.id
            patient_data = patient_doc.to_dict()
            
            # Check if this patient has an interaction for today's slot
            interactions_ref = db.collection(f"patients/{patient_id}/interactions")
            interaction_query = interactions_ref.where("scheduleSlot", "==", schedule_slot).limit(1)
            
            interaction_docs = [doc async for doc in interaction_query.stream()]
            
            if interaction_docs:
                # Patient already has an interaction logged - skip
                skipped_count += 1
                logger.info(f"⏭️ Skipping patient {patient_id} (already contacted in {schedule_slot})")
            else:
                # No interaction yet for THIS slot - fetch context from PAST slots
                recent_history = []
                try:
                    # Fetch last 3 interactions for context continuity
                    history_query = interactions_ref.order_by("timestamp", direction=Query.DESCENDING).limit(3)
                    async for hist_doc in history_query.stream():
                        h_data = hist_doc.to_dict()
                        # Format timestamp nicely if present
                        ts = h_data.get("timestamp")
                        date_str = ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)
                        
                        recent_history.append({
                            "date": date_str,
                            "brief": h_data.get("aiBrief", "No summary available"),
                            "risk": h_data.get("riskLevel", "UNKNOWN")
                        })
                except Exception as ex:
                    logger.warning(f"Failed to fetch history for {patient_id}: {ex}")

                # Add enriched patient data to pending list
                patient_info = {
                    "id": patient_id,
                    "preferredLanguage": patient_data.get("preferredLanguage", "en-US"), # Default to en-US
                    "recentHistory": recent_history,
                    **patient_data
                }
                pending_patients.append(patient_info)
        
        logger.info(f"📋 Found {len(pending_patients)} pending patients (skipped {skipped_count} already contacted)")
        
        return json.dumps(pending_patients)
        
    except Exception as e:
        logger.error(f"❌ Error in get_pending_patients: {e}", exc_info=True)
        return json.dumps({"error": str(e)})


# Export for agent
retry_tools = [get_pending_patients]
