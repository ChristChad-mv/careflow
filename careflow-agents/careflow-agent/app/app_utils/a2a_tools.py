"""
A2A Tools for CareFlow-Main Agent
Communication avec Twilio-Agent via A2A Protocol
"""
import json
import httpx
from typing import Optional, AsyncGenerator
from google.adk.streaming import StreamingOptions

# Configuration Twilio-Agent
TWILIO_AGENT_URL = "http://localhost:5001"  # URL du service Twilio-Agent
TWILIO_AGENT_CARD_URL = f"{TWILIO_AGENT_URL}/.well-known/agent-card.json"


async def list_remote_agents() -> list[dict]:
    """
    Liste les agents distants disponibles (ici juste Twilio-Agent)
    
    Returns:
        Liste des agent cards
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(TWILIO_AGENT_CARD_URL)
        agent_card = response.json()
        return [agent_card]


async def initiate_call(
    phone_number: str,
    patient_name: str,
    patient_id: str,
    call_context: dict
) -> dict:
    """
    Initie un appel téléphonique via Twilio-Agent
    
    Args:
        phone_number: Numéro du patient (format E.164: +33612345678)
        patient_name: Nom du patient
        patient_id: ID Firestore du patient
        call_context: Context médical (symptômes à surveiller, etc.)
    
    Returns:
        {
            "call_sid": "CAxxxx",
            "status": "initiated",
            "agent_task_id": "task_xxx"
        }
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TWILIO_AGENT_URL}/a2a/message/send",
            json={
                "jsonrpc": "2.0",
                "method": "agent/task/invoke",
                "id": f"call_{patient_id}",
                "params": {
                    "task": {
                        "action": "initiate_call",
                        "phone_number": phone_number,
                        "patient_name": patient_name,
                        "patient_id": patient_id,
                        "context": call_context
                    }
                }
            }
        )
        return response.json()


async def send_instruction_to_patient(
    call_sid: str,
    instruction: str,
    stream: bool = True
) -> AsyncGenerator[str, None]:
    """
    Envoie une instruction à Twilio-Agent pour qu'il la dise au patient
    
    Args:
        call_sid: ID de l'appel Twilio
        instruction: Ce que l'agent doit dire (ex: "Demander niveau de douleur")
        stream: Si True, stream la réponse
    
    Yields:
        Chunks de la réponse du patient
    """
    endpoint = "/a2a/message/stream" if stream else "/a2a/message/send"
    
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{TWILIO_AGENT_URL}{endpoint}",
            json={
                "jsonrpc": "2.0",
                "method": "agent/task/invoke",
                "id": call_sid,
                "params": {
                    "task": {
                        "action": "speak_to_patient",
                        "call_sid": call_sid,
                        "instruction": instruction
                    }
                }
            }
        ) as response:
            # Stream les événements SSE
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    
                    if data.get("method") == "agent/message":
                        # Message du patient
                        content = data.get("params", {}).get("content", "")
                        yield content
                    
                    elif data.get("method") == "agent/task/result":
                        # Fin de la tâche
                        result = data.get("params", {}).get("result", {})
                        yield f"\n[TASK COMPLETED: {result.get('status')}]"
                        break


async def end_call(call_sid: str) -> dict:
    """
    Termine un appel
    
    Args:
        call_sid: ID de l'appel Twilio
    
    Returns:
        Status de fin d'appel
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TWILIO_AGENT_URL}/a2a/message/send",
            json={
                "jsonrpc": "2.0",
                "method": "agent/task/invoke",
                "id": call_sid,
                "params": {
                    "task": {
                        "action": "end_call",
                        "call_sid": call_sid
                    }
                }
            }
        )
        return response.json()
