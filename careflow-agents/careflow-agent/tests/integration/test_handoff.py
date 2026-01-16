
import asyncio
import aiohttp
import sys
import os
import uuid

# Configuration
CAREFLOW_URL = "http://localhost:8080"
CALL_SID = "CAfb07f8e4a54f6b8be7b03bd7a18cae99"  # Le SID récupéré de tes logs
PATIENT_NAME = "James Wilson"

async def send_handoff():
    """
    Triggers a manual handoff for call analysis using the same message schema
    as the trigger_and_disconnect function.
    """
    print(f"🚀 Sending Manual Handoff for {PATIENT_NAME}...")
    print(f"📞 Call SID: {CALL_SID}")
    request_id = int(uuid.uuid1().int >> 64)
    message_text = f"CALL_COMPLETE: Interview finished with {PATIENT_NAME}. Call SID: {CALL_SID}"
    
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
            async with session.post(
                CAREFLOW_URL,
                headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
                json=rpc_request
            ) as response:
                print(f"📡 Status Code: {response.status}")
                
                async for line in response.content:
                    if line:
                        decoded_line = line.decode('utf-8').strip()
                        if decoded_line:
                            print(f"📩 Server replied: {decoded_line[:100]}...")
                            
                if response.status == 200:
                    print("✅ Handoff Sent Successfully!")
                else:
                    error_text = await response.text()
                    print(f"❌ Error: {error_text}")

    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(send_handoff())
