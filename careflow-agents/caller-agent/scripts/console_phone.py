#!/usr/bin/env python3
"""
CareFlow Pulse - Console Phone Listener (Port 8002)

This script acts as a 'Virtual Handset'. 
1. It listens on port 8002 for 'RING' signals from the Caller Agent.
2. It notifies the user of an incoming call.
3. Upon answering, it connects to the Caller Agent WebSocket (8000) for the chat.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
import websockets
from fastapi import FastAPI, BackgroundTasks
import uvicorn
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("console_phone")

app = FastAPI()
incoming_call_data = None
is_active = False

@app.post("/ring")
async def ring_phone(data: dict, background_tasks: BackgroundTasks):
    global incoming_call_data
    incoming_call_data = data
    print("\n" + "🔔" * 20)
    print(f"📞 INCOMING CALL: {data.get('patient_name')} (ID: {data.get('patient_id')})")
    print(f"📝 Context: {data.get('message')}")
    print("👉 Press ENTER in this console to ANSWER.")
    print("🔔" * 20 + "\n")
    return {"status": "ringing"}

async def start_chat(url, patient_name, patient_id, context):
    global is_active
    is_active = True
    print(f"\n[SYSTEM] Answering call... Connecting to {url}")
    
    try:
        async with websockets.connect(url) as websocket:
            # 1. Send Setup Message (to match server expectations)
            setup = {
                "type": "setup",
                "sessionId": f"console-phone-{datetime.now().strftime('%H%M%S')}",
                "callSid": f"CONSOLE-{datetime.now().strftime('%f')}",
                "from": "+15550000000",
                "to": "+15551111111",
                "direction": "outbound-api",
                "customParameters": {
                    "patient_name": patient_name,
                    "patient_id": patient_id,
                    "context": context
                }
            }
            await websocket.send(json.dumps(setup))
            
            # Receiver loop
            async def receive():
                while True:
                    try:
                        resp = await websocket.recv()
                        msg = json.loads(resp)
                        if msg.get("type") == "text":
                            token = msg.get("token", "")
                            if token:
                                print(f"{token}", end="", flush=True)
                            if msg.get("last"):
                                print("\n")
                    except Exception:
                        break

            recv_task = asyncio.create_task(receive())
            
            # Input loop
            while not recv_task.done():
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(None, sys.stdin.readline)
                user_input = user_input.strip()
                
                if user_input.lower() in ('hangup', 'exit', 'quit'):
                    break
                
                if not user_input:
                    continue

                prompt = {
                    "type": "prompt",
                    "voicePrompt": user_input,
                    "lang": "en-US",
                    "last": True
                }
                await websocket.send(json.dumps(prompt))
                print("🤖 Assistant: ", end="", flush=True)
            
            recv_task.cancel()

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        is_active = False
        print("\n📴 Call ended.")
        print("\n👂 Waiting for next call on port 8002...")

async def input_monitor():
    global incoming_call_data, is_active
    while True:
        if incoming_call_data and not is_active:
            # Wait for Enter
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, sys.stdin.readline)
            
            data = incoming_call_data
            incoming_call_data = None
            
            await start_chat(
                "ws://localhost:8000/ws",
                data.get('patient_name'),
                data.get('patient_id'),
                data.get('message')
            )
        await asyncio.sleep(0.1)

async def main():
    print("=" * 60)
    print("  💻 CareFlow Console Phone Listener")
    print("  Listening on port 8002...")
    print("=" * 60)
    
    config = uvicorn.Config(app, host="0.0.0.0", port=8002, log_level="warning")
    server = uvicorn.Server(config)
    
    await asyncio.gather(
        server.serve(),
        input_monitor()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
