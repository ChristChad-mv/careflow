import asyncio
import aiohttp
import uuid
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Target the CareFlow Agent (Orchestrator)
CAREFLOW_AGENT_URL = "http://localhost:8000"

async def trigger_daily_job(schedule_hour: int = 8):
    """
    Simulates a Cloud Scheduler job triggering the CareFlow Agent.
    Sends a message to start the daily rounds for a specific medication schedule hour.
    
    Args:
        schedule_hour: The medication schedule hour (8 for morning, 12 for noon, 20 for evening)
    """
    logger.info(f"⏰ Starting Daily Patient Rounds Job for {schedule_hour}:00...")
    
    request_id = int(uuid.uuid1().int >> 64)
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
        async with aiohttp.ClientSession() as session:
            logger.info(f"🚀 Sending trigger to CareFlow Agent at {CAREFLOW_AGENT_URL}...")
            async with session.post(
                CAREFLOW_AGENT_URL,
                headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
                json=rpc_request
            ) as response:
                if not response.ok:
                    logger.error(f"❌ Failed to trigger job: {response.status} {await response.text()}")
                    return

                logger.info("✅ Job triggered successfully! Listening for orchestrator status...")
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data:"):
                        try:
                            data = json.loads(line[5:].strip())
                            if data.get("result"):
                                # Just log activity to show it's working
                                res = data["result"]
                                if isinstance(res, dict) and res.get("status", {}).get("state") == "working":
                                    logger.info("Orchestrator is working...")
                                if data.get("result", {}).get("final"):
                                    logger.info("Daily rounds completed.")
                                    break
                        except:
                            pass
                            
    except Exception as e:
        logger.error(f"❌ Error triggering job: {str(e)}")

if __name__ == "__main__":
    import sys
    # Allow specifying schedule hour from command line: python run_daily_job.py 8
    schedule_hour = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    asyncio.run(trigger_daily_job(schedule_hour))
