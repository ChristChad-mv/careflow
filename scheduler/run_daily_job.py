"""CareFlow Pulse - Disconnect Resilience Test Script

⚠️ THIS IS A TESTING SCRIPT - NOT FOR PRODUCTION USE ⚠️

Purpose:
    Tests the CareFlow Pulse Agent's ability to handle network disconnections
    during ongoing patient calls. Simulates a Cloud Scheduler job that 
    disconnects after 10 seconds.

Usage:
    # Start CareFlow Pulse Agent locally on port 8001
    python run_daily_job.py
    
    # With custom schedule hour
    python run_daily_job.py --hour 12

Production Scheduler:
    For production deployment, use Cloud Scheduler (see terraform/ directory)
    which provides:
    - OIDC authentication
    - Retry mechanisms
    - Multi-environment support (staging/prod)
    - Proper monitoring and alerting

Author: CareFlow Team
Last Updated: January 2026
"""

import asyncio
import aiohttp
import uuid
import logging
import sys
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CAREFLOW_AGENT_URL = "http://localhost:8080"  # Local development only

async def trigger_and_disconnect(schedule_hour: int = 8):
    """
    Triggers a daily rounds job and intentionally disconnects after 10 seconds
    to test the agent's resilience to network failures.
    
    Args:
        schedule_hour: Hour of the day to simulate (8, 12, or 20)
    
    Flow:
        1. Sends A2A JSON-RPC request to local agent
        2. Begins consuming SSE stream
        3. After 10 seconds, forcefully closes connection
        4. Agent should continue processing calls despite disconnect
    
    Expected Behavior:
        The agent should detect the disconnect, log it, but continue
        making patient calls that were already queued.
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
    parser = argparse.ArgumentParser(
        description='Test CareFlow Agent disconnect resilience',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test morning rounds (8 AM)
  python run_daily_job.py --hour 8
  
  # Test noon rounds (12 PM)
  python run_daily_job.py --hour 12
  
  # Test evening rounds (8 PM)
  python run_daily_job.py --hour 20

Note: This script only works with a locally running agent on port 8001.
      For production, use Cloud Scheduler (see terraform/ directory).
        """
    )
    parser.add_argument(
        '--hour',
        type=int,
        default=8,
        choices=[8, 12, 20],
        help='Schedule hour to test (8=morning, 12=noon, 20=evening)'
    )
    args = parser.parse_args()
    
    logger.info(f"🧪 Testing disconnect resilience for {args.hour}:00 rounds")
    asyncio.run(trigger_and_disconnect(args.hour))
