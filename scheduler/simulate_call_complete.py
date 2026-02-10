import asyncio
import aiohttp
import uuid
import logging
import os
import base64
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Target Pulse Agent
CAREFLOW_AGENT_URL = "http://localhost:8080"
CALL_SID = ""
PATIENT_NAME = ""
PATIENT_ID = ""


def fetch_twilio_audio(call_sid: str) -> str | None:
    """Fetch the call recording from Twilio and return base64-encoded audio."""
    acc_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not acc_sid or not auth_token:
        logger.warning("⚠️ Twilio credentials not set — audio will NOT be attached.")
        return None

    try:
        rec_url = f"https://api.twilio.com/2010-04-01/Accounts/{acc_sid}/Calls/{call_sid}/Recordings.json"
        r = requests.get(rec_url, auth=HTTPBasicAuth(acc_sid, auth_token), timeout=15)
        r.raise_for_status()
        recs = r.json().get("recordings", [])
        if not recs:
            logger.warning(f"⚠️ No recordings found for {call_sid}")
            return None

        aud_url = f"https://api.twilio.com/2010-04-01/Accounts/{acc_sid}/Recordings/{recs[0]['sid']}.wav"
        aud_r = requests.get(aud_url, auth=HTTPBasicAuth(acc_sid, auth_token), timeout=60)
        aud_r.raise_for_status()

        logger.info(f"🎙️ Downloaded {len(aud_r.content)} bytes of audio for {call_sid}")
        return base64.b64encode(aud_r.content).decode('utf-8')
    except Exception as e:
        logger.error(f"❌ Audio fetch failed: {e}")
        return None


async def simulate_call_complete():
    logger.info(f"🧪 Simulating CALL_COMPLETE for {PATIENT_NAME} (SID: {CALL_SID})...")
    
    instruction_text = (
        f"CALL_COMPLETE: Interview with patient {PATIENT_NAME} (ID: {PATIENT_ID}) finished. "
        f"Call SID: {CALL_SID}. Analyze the audio."
    )
    
    # Build message parts — text + inline audio (just like call-status now does)
    message_parts = [{"text": instruction_text, "kind": "text"}]
    
    audio_b64 = fetch_twilio_audio(CALL_SID)
    audio_attached = False
    if audio_b64:
        message_parts.append({
            "kind": "file",
            "file": {
                "bytes": audio_b64,
                "mimeType": "audio/wav"
            }
        })
        audio_attached = True
        logger.info("✅ Audio attached inline to A2A message")
    else:
        message_parts.append({"text": f"\n[AUDIO_UNAVAILABLE: Could not fetch recording for Call SID {CALL_SID}. Do NOT hallucinate an analysis — report that audio was unavailable.]", "kind": "text"})
        logger.warning("⚠️ Sending without audio — Pulse Agent should report audio unavailable")
    
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "message/stream",
        "id": f"sim-{CALL_SID}",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": message_parts,
                "metadata": {
                    "task": "analyze_call_audio",
                    "call_sid": CALL_SID,
                    "source": "simulation_script",
                    "audio_attached": audio_attached
                }
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json", 
        "Accept": "text/event-stream"
    }

    try:
        timeout = aiohttp.ClientTimeout(total=600) # Long timeout for multimodal analysis
        async with aiohttp.ClientSession(timeout=timeout) as session:
            logger.info(f"📡 Sending request to {CAREFLOW_AGENT_URL}...")
            async with session.post(
                CAREFLOW_AGENT_URL,
                headers=headers,
                json=rpc_request
            ) as response:
                if response.status != 200:
                    logger.error(f"❌ Error: Server returned status {response.status}")
                    text = await response.text()
                    logger.error(f"Response: {text}")
                    return

                logger.info("✅ Signal accepted! Waiting for multimodal analysis logs...")
                
                async for line in response.content:
                    decoded = line.decode('utf-8').strip()
                    if decoded:
                        # Clean up SSE formatting for readability
                        if decoded.startswith("data: "):
                            logger.info(f"📩 Agent Output: {decoded[6:]}")
                        else:
                            logger.info(f"📩 SSE: {decoded}")
                        
    except Exception as e:
        logger.error(f"❌ Connection Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(simulate_call_complete())
