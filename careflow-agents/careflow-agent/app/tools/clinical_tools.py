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
    Internal helper to create or update an active alert for a patient.
    Instead of duplicate alerts, it finds the active one and updates it.
    """
    try:
        db = get_db()
        
        # Check for existing active alert for this patient
        alerts_ref = db.collection("alerts")
        query = alerts_ref.where("patientId", "==", patientId).where("status", "==", "active").limit(1)
        active_alerts = await query.get()
        
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
            "updatedAt": datetime.now(timezone.utc)
        }
        
        if active_alerts:
            # Update existing alert
            doc_id = active_alerts[0].id
            await alerts_ref.document(doc_id).update(alert_doc)
            logger.info(f"✅ Clinical alert updated: {doc_id} for {patientName}")
            return f"SUCCESS: Alert {doc_id} updated for {patientName}. Priority: {priority}."
        else:
            # Create new alert
            alert_doc["createdAt"] = datetime.now(timezone.utc)
            _, doc_ref = await alerts_ref.add(alert_doc)
            logger.info(f"✅ New clinical alert created: {doc_ref.id} for {patientName}")
            return f"SUCCESS: New Alert {doc_ref.id} created for {patientName}. Priority: {priority}."
            
    except Exception as e:
        logger.error(f"❌ Error managing alert: {str(e)}", exc_info=True)
        return f"ERROR: Failed to handle alert: {str(e)}"

async def update_patient_risk(
    patientId: str,
    riskLevel: str,
    aiBrief: str,
    trigger: Optional[str] = None,
    callSid: Optional[str] = None
) -> str:
    """
    The MASTER clinical update tool.
    1. Updates the patient document risk and summary.
    2. Automatically manages clinical ALERTS:
       - GREEN: Resolves any active alerts.
       - YELLOW/RED: Creates or updates an active alert.
    
    Args:
        patientId: ID of the patient.
        riskLevel: 'GREEN', 'YELLOW', or 'RED'.
        aiBrief: Detailed summary of current clinical status.
        trigger: (Required for Yellow/Red) One-line summary for the alert dashboard.
        callSid: Optional Twilio Call SID.
    """
    try:
        db = get_db()
        
        # 1. Fetch patient to get hospitalId and Name for the alert sync
        patient_ref = db.collection("patients").document(patientId)
        patient_snap = await patient_ref.get()
        
        if not patient_snap.exists:
            return f"ERROR: Patient {patientId} not found."
            
        patient_data = patient_snap.to_dict()
        patient_name = patient_data.get("name", "Unknown Patient")
        hospital_id = patient_data.get("hospitalId", "UNKNOWN")
        
        # 2. Update Patient Record
        update_data = {
            "riskLevel": riskLevel.upper(),
            "aiBrief": aiBrief,
            "lastAssessedAt": datetime.now(timezone.utc)
        }
        if callSid:
            update_data["lastCallSid"] = callSid
            
        await patient_ref.update(update_data)
        logger.info(f"✅ Patient {patientId} risk updated to {riskLevel}")
        
        # 3. Handle Alerts (Automatic Orchestration)
        if riskLevel.upper() in ["YELLOW", "RED", "WARNING", "CRITICAL"]:
            # Priority mapping
            priority = "critical" if riskLevel.upper() in ["RED", "CRITICAL"] else "warning"
            # Effective trigger fallback
            effective_trigger = trigger if trigger else f"Risk increased to {riskLevel}: {aiBrief[:50]}..."
            
            alert_response = await create_alert(
                hospitalId=hospital_id,
                patientId=patientId,
                patientName=patient_name,
                priority=priority,
                trigger=effective_trigger,
                brief=aiBrief,
                callSid=callSid
            )
            return f"SUCCESS: Risk updated to {riskLevel}. Alert synced: {alert_response}"
            
        elif riskLevel.upper() == "GREEN":
            # Auto-resolve active alerts if state is now SAFE
            alerts_ref = db.collection("alerts")
            query = alerts_ref.where("patientId", "==", patientId).where("status", "==", "active")
            active_alerts = await query.get()
            
            resolved_count = 0
            for doc in active_alerts:
                await doc.reference.update({
                    "status": "resolved",
                    "resolvedAt": datetime.now(timezone.utc),
                    "resolutionNote": f"Auto-resolved by Pulse Agent (Risk set to GREEN). Brief: {aiBrief}"
                })
                resolved_count += 1
            
            msg = f"SUCCESS: Patient {patientId} risk updated to GREEN."
            if resolved_count > 0:
                msg += f" {resolved_count} alert(s) auto-resolved."
            return msg
            
        return f"SUCCESS: Patient {patientId} risk updated to {riskLevel}."
        
    except Exception as e:
        logger.error(f"❌ Error in clinical update: {str(e)}", exc_info=True)
        return f"ERROR: Failed to update clinical status: {str(e)}"

# Collection for agent tools
clinical_tools = [update_patient_risk]
