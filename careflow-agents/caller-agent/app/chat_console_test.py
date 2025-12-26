import asyncio
import uuid
import sys
import os
from datetime import datetime
from typing import List

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from agent import Agent
from utils.conversation_relay import SessionData, ConversationMessage
from utils.config import NGROK_URL

class MockWebSocket:
    """Mocks the WebSocket to print agent responses to the console."""
    async def send_text(self, data: str):
        import json
        try:
            message = json.loads(data)
            if message.get("type") == "text":
                print(f"\n🤖 Agent: {message.get('token')}", end="", flush=True)
            elif message.get("type") == "play":
                print(f"\n[Audio Playback: {message.get('source')}]")
        except Exception as e:
            print(f"Error parsing message: {e}")

async def main():
    print("🚀 Starting CareFlow Caller Agent (Terminal Mode)")
    print("Type 'quit' or 'exit' to stop.\n")

    # Initialize Agent
    # We need to read config manually or rely on the agent's internal config reading
    # The Agent class reads config internally upon instantiation if we don't pass everything
    
    # However, Agent.__init__ takes system_message and a2a_servers.
    # Let's import the config object from agent.py or config.py to be safe, 
    # but agent.py already does `config = read_config()` at module level.
    # We can just instantiate Agent with the values from that global config if we import it,
    # or let's just use the Agent class and let it use its internal logic if possible.
    
    # Actually, src.client.agent instantiates `agent` globally at the end of the file.
    # We can import that instance!
    from agent import agent
    
    # Initialize the agent (loads A2A cards)
    await agent.init()
    
    # Mock WebSocket
    mock_ws = MockWebSocket()
    agent.set_ws_channel(mock_ws)
    
    # Session Data
    session_id = str(uuid.uuid4())
    conversation_history: List[ConversationMessage] = []
    
    print("✅ Agent initialized. You can start chatting.")
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
        except EOFError:
            break
            
        if user_input.lower() in ('quit', 'exit'):
            break
            
        if not user_input:
            continue
            
        # Update session data
        # We pass empty conversation history because the Agent class uses MemorySaver
        # and passing history explicitly causes duplication/conflicts in LangGraph state.
        session_data = SessionData(
            connected_at=datetime.now().isoformat(),
            call_sid=session_id,
            conversation=[] 
        )
        
        # Stream response
        print("", end="", flush=True) # Newline handled by MockWebSocket
        async for _ in agent.stream_message(user_input, session_data):
            pass # The agent sends to websocket inside stream_message
            
        # Add to history (simplified, ideally we'd capture the full response)
        conversation_history.append(ConversationMessage(
            role='user',
            content=user_input,
            timestamp=datetime.now().isoformat()
        ))
        # We should also append agent response to history for context, 
        # but in this simple mock we might miss the exact full text unless we capture it from the stream.
        # For now, let's rely on the agent's internal memory (LangGraph checkpointer) which handles context.

if __name__ == "__main__":
    # Set environment variables if needed
    if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY or GEMINI_API_KEY not found in environment.")
        print("Run: set -a; source ../../../.env; set +a; python3 chat_console.py")
        sys.exit(1)
        
    asyncio.run(main())
