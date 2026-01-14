"""
CareFlow Pulse - Console Call Tool (MOCK)

This tool mimics the Twilio call tool but routes output to the console
for local testing without a Twilio account.
"""

import logging
import httpx
from typing import Optional
from langchain_core.tools import tool
from ..schemas.tool_schemas import CallPatientInput

logger = logging.getLogger(__name__)

@tool("call_patient", args_schema=CallPatientInput)
async def call_patient(
    message: str,
    patient_name: str,
    patient_id: str,
    patient_phone: Optional[str] = None,
    expect_reply: bool = True
) -> str:
    """
    (MOCK) Initiate a call by signaling the local console phone on port 8002.
    """
    print("\n" + "="*50)
    print("📞 INITIATING CONSOLE CALL...")
    print(f"👤 Patient: {patient_name} (ID: {patient_id})")
    print("="*50 + "\n")
    
    # Try to signal the console phone on port 8002
    try:
        async with httpx.AsyncClient() as client:
            await client.post("http://localhost:8002/ring", json={
                "message": message,
                "patient_name": patient_name,
                "patient_id": patient_id
            }, timeout=2.0)
            status = "SIGNAL SENT TO PORT 8002"
    except Exception as e:
        status = f"PORT 8002 NOT LISTENING ({str(e)})"
        print(f"⚠️ Warning: {status}")

    return (
        f"CONSOLE_MOCK: {status}. "
        f"Call to {patient_name} is 'ringing' on port 8002. "
        "The agent is now waiting for the WebSocket connection to proceed."
    )

__all__ = ['call_patient']
