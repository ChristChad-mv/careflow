#!/usr/bin/env python3
"""
CareFlow Pulse - Caller Agent Chat Console

This script allows direct interaction with the CallerAgent via the console,
bypassing Twilio and voice synthesis. It's used for rapid local testing
and debugging of the agent's logic and tools.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Set environment variable to use mock tools
os.environ["USE_CONSOLE_TOOL"] = "true"

# Add the current directory to path to find app module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agent import agent
from app.app_utils.conversation_relay import SessionData, ConversationMessage

# Configure logging
logging.basicConfig(
    level=logging.WARNING, # Keep console clean
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chat_console")

async def run_console():
    print("=" * 60)
    print("  🏥 CareFlow Caller Agent - Local Chat Console")
    print("=" * 60)
    print("Type 'exit' or 'quit' to stop.")
    print("Type 'system: message' to inject a system instruction.")
    print("-" * 60)

    # Initialize agent
    print("Initializing agent (loading tools and cards)...")
    await agent.init()
    print("✅ Agent ready!")

    # Setup local session
    session_data = SessionData(
        connected_at=datetime.now().isoformat(),
        call_sid='console-session-' + datetime.now().strftime("%H%M%S"),
        conversation=[]
    )

    # Initial context (optional)
    patient_name = "John Doe"
    patient_id = "P001"
    
    print(f"\n[SYSTEM] Starting session for patient: {patient_name} (ID: {patient_id})")
    
    # Simulate setup injection like in server.py
    initial_msg = (
        f"URGENT CONTEXT: You are now connected with patient {patient_name} (ID: {patient_id}).\n"
        "The patient has just picked up. Start the interview."
    )
    session_data.conversation.append(ConversationMessage(
        role='system',
        content=initial_msg,
        timestamp=datetime.now().isoformat()
    ))

    # First greeting
    print("\n🤖 Assistant: ", end="", flush=True)
    async for chunk in agent.stream_message("", session_data):
        print(chunk, end="", flush=True)
        # Append to history for the agent to have context in next turn
        # (In real server, this is done by SessionData management)
    
    # We need to manually update conversation history for the agent to remember its own words
    # The stream_message function doesn't update session_data.conversation internally to keep it stateless-ish
    # In server.py, the MessageHandler handles this.
    
    while True:
        try:
            print("\n" + "-" * 30)
            user_input = input("👤 Patient: ").strip()
            
            if user_input.lower() in ('exit', 'quit'):
                break
            
            if not user_input:
                continue

            if user_input.startswith("system:"):
                sys_msg = user_input[7:].strip()
                session_data.conversation.append(ConversationMessage(
                    role='system',
                    content=sys_msg,
                    timestamp=datetime.now().isoformat()
                ))
                print(f"✅ System instruction added: {sys_msg}")
                continue

            # Add human message to history
            session_data.conversation.append(ConversationMessage(
                role='user',
                content=user_input,
                timestamp=datetime.now().isoformat()
            ))

            print("\n🤖 Assistant: ", end="", flush=True)
            full_reply = ""
            async for chunk in agent.stream_message(user_input, session_data):
                print(chunk, end="", flush=True)
                full_reply += chunk
            
            # Add assistant message to history
            session_data.conversation.append(ConversationMessage(
                role='assistant',
                content=full_reply,
                timestamp=datetime.now().isoformat()
            ))
            print() # Final newline

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            logger.exception("Error in console loop")

    print("\n" + "=" * 60)
    print(" 👋 Console session ended.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_console())
