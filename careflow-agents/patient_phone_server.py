import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Patient Phone Simulator")

class IncomingCall(BaseModel):
    message: str
    patient_name: str
    patient_id: str

@app.post("/incoming_call")
async def incoming_call(call: IncomingCall):
    """
    Receives a "call" (text message) from the Caller Agent.
    Prints it to the terminal and waits for user input to reply.
    """
    print("\n" + "="*50)
    print(f"📞 INCOMING CALL FROM CAREFLOW PULSE")
    print(f"For Patient: {call.patient_name} (ID: {call.patient_id})")
    print("-" * 50)
    print(f"🤖 Agent: {call.message}")
    print("="*50 + "\n")

    # Get user input (simulating voice/text reply)
    # We use asyncio.to_thread to not block the event loop if we were handling multiple requests,
    # though for this single-user sim it's fine.
    user_reply = await asyncio.to_thread(input, "👤 You: ")
    
    print("\n" + "-"*50)
    print("✅ Reply sent.")
    print("-" * 50 + "\n")

    return {"response": user_reply}

if __name__ == "__main__":
    print("📱 Patient Phone Simulator started on http://localhost:9000")
    print("Waiting for incoming calls...")
    uvicorn.run(app, host="0.0.0.0", port=9000)
