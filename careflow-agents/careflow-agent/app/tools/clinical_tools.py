"""
CareFlow Pulse - Clinical Tools
Native ADK tools for medical database operations (Alerts & Risk Assessment).
Uses Firestore SDK directly to avoid format issues with general MCP tools.
"""
import logging
import os
from datetime import datetime, timezone
from typing import Optional
from google.cloud.firestore import AsyncClient

logger = logging.getLogger(__name__)

# Cache for Firestore client
_db_client: Optional[AsyncClient] = None

def get_db():
    global _db_client
    if _db_client is None:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "careflow-478811")
        database_id = os.environ.get("FIRESTORE_DATABASE", "careflow-db")
        _db_client = AsyncClient(project=project_id, database=database_id)
    return _db_client

async def create_alert(
    hospitalId: str,
    patientId: str,
    patientName: str,
    priority: str,
    trigger: str,
    brief: str,
    callSid: Optional[str] = None
) -> str:
    """
    Creates a high-level clinical alert for nurses.
    Use this when a patient's call analysis indicates YELLOW or RED risk.
    
    Args:
        hospitalId: ID of the hospital (e.g., HOSP001)
        patientId: ID of the patient (e.g., p_h1_001)
        patientName: Full name of the patient
        priority: Alert severity: 'critical' (RED) or 'warning' (YELLOW)
        trigger: One-line summary of what triggered the alert
        brief: Detailed AI clinical analysis (2-4 sentences)
        callSid: Optional Twilio Call SID for audio reference
    """
    try:
        db = get_db()
        
        # Build document data
        alert_doc = {
            "hospitalId": hospitalId,
            "patientId": patientId,
            "patientName": patientName,
            "priority": priority, # 'critical' or 'warning'
            "status": "active",
            "trigger": trigger,
            "aiBrief": brief,
            "brief": brief, 
            "callSid": callSid,
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        }
        
        # Write directly to Firestore 
        _, doc_ref = await db.collection("alerts").add(alert_doc)
        
        logger.info(f"✅ Clinical alert created: {doc_ref.id} for {patientName}")
        return f"SUCCESS: Alert {doc_ref.id} created for {patientName}. Priority: {priority}."
        
    except Exception as e:
        logger.error(f"❌ Error creating alert: {str(e)}", exc_info=True)
        return f"ERROR: Failed to create alert: {str(e)}"

async def update_patient_risk(
    patientId: str,
    riskLevel: str,
    aiBrief: str,
    callSid: Optional[str] = None
) -> str:
    """
    Updates the overall risk level and brief of a patient document.
    
    Args:
        patientId: ID of the patient (e.g., p_h1_001)
        riskLevel: The new risk level: 'GREEN', 'YELLOW', or 'RED'
        aiBrief: A 1-2 sentence summary of why this risk was assigned
        callSid: Optional Twilio Call SID for the latest interaction
    """
    try:
        db = get_db()
        
        patient_ref = db.collection("patients").document(patientId)
        
        update_data = {
            "riskLevel": riskLevel,
            "aiBrief": aiBrief,
            "lastAssessedAt": datetime.now(timezone.utc)
        }
        
        if callSid:
            update_data["lastCallSid"] = callSid
        
        await patient_ref.update(update_data)
        
        logger.info(f"✅ Patient {patientId} risk updated to {riskLevel}")
        return f"SUCCESS: Patient {patientId} risk level updated to {riskLevel}."
        
    except Exception as e:
        logger.error(f"❌ Error updating risk: {str(e)}", exc_info=True)
        return f"ERROR: Failed to update patient risk: {str(e)}"

# Collection for agent tools
clinical_tools = [create_alert, update_patient_risk]
