"""
CareFlow Pulse - Twilio Call Tool

This module implements the Twilio phone call tool for the Caller Agent.
It handles outbound call initiation with deduplication logic.

Author: CareFlow Pulse Team
Version: 1.0.0
"""

import asyncio
import logging
import os
import time
from typing import Dict, Optional
from urllib.parse import quote

from langchain_core.tools import tool

from ..schemas.tool_schemas import CallPatientInput

logger = logging.getLogger(__name__)


# =============================================================================
# CALL DEDUPLICATION
# =============================================================================

# In-memory cache for call deduplication
_CALL_CACHE: Dict[str, float] = {}
_CALL_LOCK = asyncio.Lock()

# Deduplication window in seconds (configurable via env)
CALL_DEDUP_WINDOW = int(os.environ.get("CALL_DEDUP_WINDOW_SECONDS", "60"))


# =============================================================================
# TWILIO CALL TOOL
# =============================================================================

@tool("call_patient", args_schema=CallPatientInput)
async def call_patient(
    message: str,
    patient_name: str,
    patient_id: str,
    patient_phone: Optional[str] = None,
    expect_reply: bool = True
) -> str:
    """
    Initiate a phone call to a patient via Twilio.
    
    This tool creates a Twilio call that connects to our ConversationRelay
    WebSocket endpoint, enabling real-time voice conversation.
    
    Args:
        message: Context/instructions for the call
        patient_name: Patient's name for personalization
        patient_id: Patient's unique ID for tracking
        patient_phone: Phone number to call (falls back to TEST_PATIENT_PHONE)
        expect_reply: Whether this is an interactive call
    
    Returns:
        Status message indicating call result
    """
    try:
        from twilio.rest import Client
        
        # Get Twilio credentials
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        from_number = os.environ.get("TWILIO_PHONE_NUMBER")
        to_number = patient_phone or os.environ.get("TEST_PATIENT_PHONE")
        ngrok_url = os.environ.get("NGROK_URL")
        
        # Validate configuration
        missing = []
        if not account_sid:
            missing.append("TWILIO_ACCOUNT_SID")
        if not auth_token:
            missing.append("TWILIO_AUTH_TOKEN")
        if not from_number:
            missing.append("TWILIO_PHONE_NUMBER")
        if not ngrok_url:
            missing.append("NGROK_URL")
        if not to_number:
            missing.append("patient_phone/TEST_PATIENT_PHONE")
        
        if missing:
            return f"Error: Missing configuration: {', '.join(missing)}"
        
        # Deduplication check
        async with _CALL_LOCK:
            current_time = time.time()
            last_call_time = _CALL_CACHE.get(patient_id, 0)
            
            if current_time - last_call_time < CALL_DEDUP_WINDOW:
                elapsed = int(current_time - last_call_time)
                logger.info(f"Duplicate call blocked for {patient_name} ({elapsed}s ago)")
                return (
                    f"SUCCESS: Call to {patient_name} is ALREADY IN PROGRESS "
                    f"(initiated {elapsed}s ago). DO NOT call again. "
                    "Wait for patient response via WebSocket."
                )
            
            # Mark call as initiated
            _CALL_CACHE[patient_id] = current_time
        
        # Create Twilio call
        logger.info(f"Initiating call to {patient_name} ({to_number})")
        
        client = Client(account_sid, auth_token)
        
        # Build TwiML webhook URL with patient context
        twiml_url = (
            f"https://{ngrok_url}/twiml"
            f"?patient_name={quote(patient_name)}"
            f"&patient_id={quote(patient_id)}"
            f"&context={quote(message)}"
        )
        
        call = client.calls.create(
            to=to_number,
            from_=from_number,
            url=twiml_url
        )
        
        logger.info(f"Call created - SID: {call.sid}")
        
        return (
            f"SYSTEM: Call initiated (SID: {call.sid}). "
            "Phone is ringing. DO NOT GENERATE TEXT yet. "
            "Wait for ConversationRelay WebSocket connection."
        )
        
    except Exception as e:
        logger.error(f"Twilio call error: {e}")
        return f"Failed to initiate call: {str(e)}"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['call_patient']
