#!/usr/bin/env python3
"""
CareFlow Pulse - Simulated Patient (WebSocket Console)

This script acts as a simulated patient "handset". It connects to the 
Caller Agent server via WebSocket and simulates the Twilio ConversationRelay
protocol.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sim_patient")

async def simulated_patient(url, patient_name, patient_id, context):
    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url) as websocket:
            print("✅ Connected to Caller Agent Server")
            
            # 1. Send Setup Message
            setup = {
                "type": "setup",
                "sessionId": f"sim-session-{datetime.now().strftime('%H%M%S')}",
                "callSid": f"CA{datetime.now().strftime('%f')}",
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
            print(f"Sent setup for {patient_name}")

            # 2. Listen loop
            async def receive_messages():
                full_agent_msg = ""
                while True:
                    try:
                        msg_str = await websocket.recv()
                        msg = json.loads(msg_str)
                        
                        if msg.get("type") == "text":
                            token = msg.get("token", "")
                            if token:
                                print(f"{token}", end="", flush=True)
                                full_agent_msg += token
                            if msg.get("last"):
                                print("\n") # End of agent turn
                                full_agent_msg = ""
                        elif msg.get("type") == "play":
                            print(f"\n[🎵 Agent plays audio: {msg.get('source')}]")
                        
                    except websockets.exceptions.ConnectionClosed:
                        print("\n❌ Connection closed by server")
                        break
                    except Exception as e:
                        print(f"\n❌ Error receiving: {e}")
                        break

            # Start receiver task
            receiver_task = asyncio.create_task(receive_messages())

            # 3. Input loop
            print("\nConversation started! Type your reply and press Enter.")
            print("-" * 60)
            
            while not receiver_task.done():
                try:
                    # Use run_in_executor to avoid blocking the event loop with input()
                    loop = asyncio.get_event_loop()
                    user_input = await loop.run_in_executor(None, sys.stdin.readline)
                    user_input = user_input.strip()
                    
                    if user_input.lower() in ('exit', 'quit'):
                        break
                    
                    if not user_input:
                        continue

                    # Send prompt message
                    prompt = {
                        "type": "prompt",
                        "voicePrompt": user_input,
                        "lang": "en-US",
                        "last": True
                    }
                    await websocket.send(json.dumps(prompt))
                    print(f"👤 Patient: {user_input}")
                    print("🤖 Assistant: ", end="", flush=True)

                except EOFError:
                    break
            
            receiver_task.cancel()
            
    except Exception as e:
        print(f"❌ Failed to connect: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Simulated Patient Console")
    parser.add_argument("--url", default="ws://localhost:8000/ws", help="WebSocket URL")
    parser.add_argument("--name", default="John Doe", help="Patient Name")
    parser.add_argument("--id", default="P001", help="Patient ID")
    parser.add_argument("--context", default="Initial greeting", help="Call Context")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(simulated_patient(args.url, args.name, args.id, args.context))
    except KeyboardInterrupt:
        pass
