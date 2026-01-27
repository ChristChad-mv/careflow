"""CareFlow Pulse - Production Trigger Script

Purpose:
    Manually triggers a daily rounds job on the PRODUCTION CareFlow Pulse Agent.
    Simulates a Cloud Scheduler job by sending an A2A "start daily rounds" request.

Usage:
    python trigger_rounds_prod.py --hour 12
"""

import asyncio
import aiohttp
import uuid
import logging
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import subprocess

# PRODUCTION URL
CAREFLOW_AGENT_URL = "https://careflow-agent-gr2rcg7pca-uc.a.run.app"

def get_identity_token():
    try:
        token = subprocess.check_output(
            "gcloud auth print-identity-token", shell=True
        ).decode("utf-8").strip()
        return token
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get identity token: {e}")
        return None

async def trigger_rounds(schedule_hour: int = 8):
    logger.info(f"🚀 Triggering PRODUCTION daily rounds for {schedule_hour}:00...")
    logger.info(f"Target Agent: {CAREFLOW_AGENT_URL}")
    
    # Get OIDC Token
    token = get_identity_token()
    if not token:
        logger.error("❌ Could not get OIDC token. Make sure you are logged in with gcloud.")
        return

    request_id = int(uuid.uuid1().int >> 64)
    # Message format required by ADK/A2A protocol
    message_text = f"start daily rounds for {schedule_hour}:00"
    
    rpc_request = {
        "jsonrpc": "2.0",
        "method": "message/stream",
        "id": request_id,
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "kind": "message",
                "role": "user",
                "parts": [{"kind": "text", "text": message_text}]
            }
        }
    }
    
    try:
        # Standard timeout for HTTP request
        timeout = aiohttp.ClientTimeout(total=300) 
        
        headers = {
            "Content-Type": "application/json", 
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {token}"
        }

        async with aiohttp.ClientSession(timeout=timeout) as session:
            logger.info("📡 Sending authenticated request...")
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

                logger.info("✅ Trigger accepted! Streaming response logs from agent...")
                
                async for line in response.content:
                    decoded = line.decode('utf-8').strip()
                    if decoded:
                        logger.info(f"📩 Agent: {decoded}")
                        
    except Exception as e:
        logger.error(f"❌ Connection Error: {str(e)}")

    logger.info("👋 Trigger script finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Trigger CareFlow Production Rounds')
    parser.add_argument(
        '--hour',
        type=int,
        default=8,
        choices=[8, 12, 20],
        help='Schedule hour to trigger (8=morning, 12=noon, 20=evening)'
    )
    args = parser.parse_args()
    
    asyncio.run(trigger_rounds(args.hour))
