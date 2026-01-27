"""
CareFlow Pulse - Schedule Tools
Native ADK tools for retrieving scheduled patients with enriched context (History, Language).
Replaces limited MCP tools for complex join operations.
"""
import logging
import json
import os
from datetime import datetime, timezone
from google.cloud.firestore import AsyncClient, Query
from app.app_utils.retry_utils import get_schedule_slot_key

logger = logging.getLogger(__name__)

async def fetch_daily_schedule(
    scheduleHour: int,
    hospitalId: str
) -> str:
    """
    Retrieves ALL patients active and scheduled for a specific hour.
    Enriches each patient record with:
    1. 'completionStatus': 'completed' or 'pending' (based on today's interactions)
    2. 'preferredLanguage': Patient's preferred language (default: en-US)
    3. 'recentHistory': Summary of last 3 interactions for context awareness.
    
    Args:
        scheduleHour: The hour slot (8, 12, 20)
        hospitalId: The hospital ID
        
    Returns:
        JSON string list of enriched patient objects.
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "careflow-478811")
    database_id = os.environ.get("FIRESTORE_DATABASE", "careflow-db")
    
    try:
        db = AsyncClient(project=project_id, database=database_id)
        
        # Get today's schedule slot key (e.g., "2026-01-27_08")
        schedule_slot = get_schedule_slot_key(scheduleHour)
        logger.info(f"📅 Fetching schedule for slot: {schedule_slot} (Hospital: {hospitalId})")
        
        # Query active patients for this slot
        patients_ref = db.collection("patients")
        query = patients_ref.where("hospitalId", "==", hospitalId) \
                            .where("status", "==", "active") \
                            .where("scheduleHour", "==", scheduleHour)
        
        patients_docs = query.stream()
        
        enriched_patients = []
        
        async for patient_doc in patients_docs:
            p_data = patient_doc.to_dict()
            p_id = patient_doc.id
            
            # 1. Check Completion Status
            interactions_ref = db.collection(f"patients/{p_id}/interactions")
            # Check for interaction with same scheduleSlot
            todays_interaction = await interactions_ref.where("scheduleSlot", "==", schedule_slot).limit(1).get()
            
            status = "completed" if todays_interaction else "pending"
            
            # 2. Fetch Recent History (Last 3 interactions)
            recent_history = []
            try:
                # Order by timestamp desc
                history_query = interactions_ref.order_by("timestamp", direction=Query.DESCENDING).limit(3)
                async for hist_doc in history_query.stream():
                    h_data = hist_doc.to_dict()
                    ts = h_data.get("timestamp")
                    date_str = ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)
                    
                    recent_history.append({
                        "date": date_str,
                        "brief": h_data.get("aiBrief", "No summary available"),
                        "risk": h_data.get("riskLevel", "UNKNOWN"),
                        "type": h_data.get("type", "unknown")
                    })
            except Exception as ex:
                logger.warning(f"Failed to fetch history for {p_id}: {ex}")
            
            # 3. Build Enriched Object (Unified Structure)
            enriched_p = {
                "id": p_id,
                "name": p_data.get("name"),
                "preferredLanguage": p_data.get("preferredLanguage", "en-US"),
                "completionStatus": status,
                "riskLevel": p_data.get("riskLevel", "GREEN"),
                "contact": {
                    "phone": p_data.get("contact", {}).get("phone"),
                    "preferredMethod": p_data.get("contact", {}).get("preferredMethod", "phone")
                },
                "dischargePlan": {
                    "diagnosis": p_data.get("dischargePlan", {}).get("diagnosis"),
                    "medications": p_data.get("dischargePlan", {}).get("medications", []),
                    "criticalSymptoms": p_data.get("dischargePlan", {}).get("criticalSymptoms", []),
                    "warningSymptoms": p_data.get("dischargePlan", {}).get("warningSymptoms", [])
                },
                "nextAppointment": p_data.get("nextAppointment", {}),
                "assignedNurse": p_data.get("assignedNurse", {}),
                "recentHistory": recent_history
            }
            
            enriched_patients.append(enriched_p)
            
        logger.info(f"✅ Found {len(enriched_patients)} patients for schedule {scheduleHour} ({hospitalId})")
        return json.dumps(enriched_patients)
        
    except Exception as e:
        logger.error(f"❌ Error in get_patients_for_schedule: {e}", exc_info=True)
        return json.dumps({"error": str(e)})

# Export
schedule_tools = [fetch_daily_schedule]
