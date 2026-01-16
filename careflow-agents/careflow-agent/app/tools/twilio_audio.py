"""
Twilio Audio Fetching Tool for CareFlow Pulse Agent.

This tool ONLY fetches the raw audio from Twilio. The analysis is performed
natively by the Gemini 3 model using its multimodal capabilities.
"""
import os
import logging
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

# Twilio Credentials
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")


def fetch_call_audio(call_sid: str) -> dict:
    """
    Fetches the call recording audio from Twilio for a given Call SID.
    
    Returns the raw audio data and metadata so the LLM can analyze it directly.
    The audio is returned as base64-encoded data that Gemini 3 can process natively.
    
    Args:
        call_sid: The Twilio Call SID (e.g., 'CA123...').
        
    Returns:
        A dictionary containing:
        - success: bool
        - call_sid: The original call_sid (for reference)
        - audio_data: base64-encoded audio bytes (if successful)
        - mime_type: The audio MIME type
        - duration_seconds: Recording duration
        - error: Error message (if failed)
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        return {
            "success": False,
            "call_sid": call_sid,
            "error": "Twilio credentials not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN."
        }
    
    try:
        # Step 1: Get the recording SID from the Call SID
        recordings_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls/{call_sid}/Recordings.json"
        
        response = requests.get(
            recordings_url,
            auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            timeout=30
        )
        response.raise_for_status()
        
        recordings = response.json().get("recordings", [])
        if not recordings:
            return {
                "success": False,
                "call_sid": call_sid,
                "error": f"No recordings found for Call SID {call_sid}. The call may still be in progress or recording was not enabled."
            }
        
        recording = recordings[0]  # Get the first (usually only) recording
        recording_sid = recording["sid"]
        duration = int(recording.get("duration", 0))
        
        # Step 2: Download the audio file
        audio_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Recordings/{recording_sid}.mp3"
        
        audio_response = requests.get(
            audio_url,
            auth=HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            timeout=120
        )
        audio_response.raise_for_status()
        
        # Save to temporary file
        import tempfile
        temp_file = os.path.join(tempfile.gettempdir(), f"{call_sid}.mp3")
        with open(temp_file, "wb") as f:
            f.write(audio_response.content)
            
        logger.info(f"Successfully downloaded audio to {temp_file}")
        
        # Return a special marker that the Agent Callback can intercept
        return {
            "success": True,
            "call_sid": call_sid,
            "recording_sid": recording_sid,
            "local_file_path": temp_file,  # Critical for callback injection
            "mime_type": "audio/mpeg",
            "duration_seconds": duration,
            "message": f"Audio file downloaded to {temp_file}. The system will now inject this audio for analysis."
        }
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching audio for {call_sid}")
        return {
            "success": False,
            "call_sid": call_sid,
            "error": "Request timed out while fetching audio from Twilio."
        }
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching audio: {e}")
        return {
            "success": False,
            "call_sid": call_sid,
            "error": f"Twilio API error: {e.response.status_code} - {e.response.text}"
        }
    except Exception as e:
        logger.error(f"Error fetching audio: {e}", exc_info=True)
        return {
            "success": False,
            "call_sid": call_sid,
            "error": f"Unexpected error: {str(e)}"
        }
