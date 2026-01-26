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
import re
import time
from typing import Dict, Optional
from urllib.parse import quote

from langchain_core.tools import tool

from ..config import PUBLIC_URL
from ..schemas.tool_schemas import CallPatientInput, EndCallInput

logger = logging.getLogger(__name__)


# =============================================================================
# CALL DEDUPLICATION
# =============================================================================

# In-memory cache for call deduplication
_CALL_CACHE: Dict[str, float] = {}
_CALL_LOCK = asyncio.Lock()

# Deduplication window in seconds (configurable via env)
CALL_DEDUP_WINDOW = int(os.environ.get("CALL_DEDUP_WINDOW_SECONDS", "60"))


def _extract_retry_count(message: str) -> int:
    """
    Extract retry count from message if it contains "attempt #N" or "retry attempt #N".
    Returns 0 for initial calls, 1+ for retries.
    """
    # Look for patterns like "attempt #2" or "retry attempt #1"
    match = re.search(r'attempt\s*#(\d+)', message, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Also check for "This is retry #N"
    match = re.search(r'retry\s*#(\d+)', message, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    return 0  # Initial call, not a retry


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
        
        # Use unified PUBLIC_URL from config
        public_url = PUBLIC_URL
        
        # Validate configuration
        missing = []
        if not account_sid:
            missing.append("TWILIO_ACCOUNT_SID")
        if not auth_token:
            missing.append("TWILIO_AUTH_TOKEN")
        if not from_number:
            missing.append("TWILIO_PHONE_NUMBER")
        if not public_url:
            missing.append("PUBLIC_URL/NGROK_URL")
        if not to_number:
            missing.append("patient_phone/TEST_PATIENT_PHONE")
        
        if missing:
            return f"Error: Missing configuration: {', '.join(missing)}"
        
        # Extract retry count from message context
        retry_count = _extract_retry_count(message)
        if retry_count > 0:
            logger.info(f"📞 This is retry attempt #{retry_count} for {patient_name}")
        
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
        
        # Build TwiML URL. Note: we ensure it starts with https:// if not present
        base_url = public_url if public_url.startswith("http") else f"https://{public_url}"
        
        twiml_url = (
            f"{base_url}/twiml"
            f"?patient_name={quote(patient_name)}"
            f"&patient_id={quote(patient_id)}"
            f"&context={quote(message)}"
        )
        
        # Build status callback URL with retry_count for tracking
        status_callback_url = (
            f"{base_url}/call-status"
            f"?patient_id={quote(patient_id)}"
            f"&patient_name={quote(patient_name)}"
            f"&retry_count={retry_count}"  # Include current retry count!
        )
        
        # Initialize the Client (using synchronous client as in reference for stability)
        client = Client(account_sid, auth_token)
        
        # Execute the synchronous call in a separate thread to avoid blocking the event loop
        call = await asyncio.to_thread(
            client.calls.create,
            to=to_number,
            from_=from_number,
            url=twiml_url,
            record=True, # Enable Recording for Audio-First Reporting
            status_callback=status_callback_url,
            status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
            machine_detection='Enable', # Detect if it's a human or a machine
            async_amd='true', # Don't block call creation for AMD
            timeout=20 # Faster no-answer detection
        )
        
        logger.info(f"Call created asynchronously - SID: {call.sid} (Recording: Enabled)")
        
        return (
            f"SYSTEM: Call initiated (SID: {call.sid}). "
            "Phone is ringing. DO NOT GENERATE TEXT yet. "
            "Wait for ConversationRelay WebSocket connection."
        )
        
    except Exception as e:
        logger.error(f"Twilio async call error: {e}")
        return f"Failed to initiate call: {str(e)}"

@tool("end_call", args_schema=EndCallInput)
def end_call(reason: Optional[str] = "Conversation finished") -> str:
    """
    Terminates the active call. 
    Use this tool ONLY after saying goodbye and when the patient has finished speaking.
    
    Args:
        reason: Optional reason for ending the call.
        
    Returns:
        A signal to the system to terminate the call.
    """
    logger.info(f"🛑 Agent requested call termination. Reason: {reason}")
    # We return a special token that the WebSocket handler will intercept
    return "[[END_CALL_SIGNAL]]"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['call_patient', 'end_call']
