import asyncio
import aiohttp
import uuid
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CAREFLOW_AGENT_URL = "http://localhost:8000"

async def trigger_and_disconnect(schedule_hour: int = 8):
    """
    Triggers the job, waits 10 seconds, then disconnects.
    """
    logger.info(f"🧪 TESTING DISCONNECT RESILIENCE")
    logger.info(f"⏰ Triggering Daily Patient Rounds...")
    
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
        # We set a very short timeout or just cancel manually
        timeout = aiohttp.ClientTimeout(total=10) # 10 seconds lifespan
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            logger.info(f"🚀 Sending trigger...")
            try:
                async with session.post(
                    CAREFLOW_AGENT_URL,
                    headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
                    json=rpc_request
                ) as response:
                    logger.info("✅ Trigger sent! Receiving stream for 10 seconds...")
                    
                    start_time = asyncio.get_event_loop().time()
                    async for line in response.content:
                        logger.info(f"📩 Server replied: {line.decode('utf-8').strip()[:50]}...")
                        # Just consume a bit
                        if asyncio.get_event_loop().time() - start_time > 10:
                            logger.info("⏱️ 10 seconds reached. Cutting connection!")
                            break
                            
            except asyncio.TimeoutError:
                logger.info("⏰ Timeout reached (Intentional). Connection closed.")
            except Exception as e:
                 logger.info(f"💥 Disconnect Event: {e}")
                 
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")

    logger.info("👋 Script exiting. Check AGENT SERVER logs to see if calls continue!")

if __name__ == "__main__":
    asyncio.run(trigger_and_disconnect())
