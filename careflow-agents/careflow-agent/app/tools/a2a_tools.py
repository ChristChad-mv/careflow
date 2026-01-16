import os
import uuid
import json
import aiohttp
import logging
from traceloop.sdk.decorators import workflow, task
from a2a.types import AgentCard, Message, Role, Part, TextPart
from ..app_utils.config_loader import CAREFLOW_CALLER_URL

logger = logging.getLogger(__name__)

@task(name="list_remote_agents")
async def list_remote_agents() -> str:
    """
    List all remote agents available for A2A communication, returning their AgentCard
    metadata including capabilities, authentication, and provider information.
    """
    # Get A2A server URL from config
    a2a_servers = [CAREFLOW_CALLER_URL] 
    
    agent_cards = []
    async with aiohttp.ClientSession() as session:
        for server_url in a2a_servers:
            try:
                agent_card_url = f"{server_url}/.well-known/agent-card.json"
                async with session.get(agent_card_url, headers={"Accept": "application/json"}) as response:
                    if response.ok:
                        card_data = await response.json()
                        agent_cards.append(AgentCard.model_validate(card_data))
            except Exception as e:
                logger.error(f"Error fetching card from {server_url}: {e}")

    if not agent_cards:
        return "No remote A2A servers are currently available."

    formatted_cards = []
    for i, card in enumerate(agent_cards):
        formatted_cards.append(f"{i+1}. {card.name} ({card.url}) - {card.description}")
    
    return "Available remote agents:\n" + "\n".join(formatted_cards)


@workflow(name="send_remote_agent_task")
async def send_remote_agent_task(task: str, server_url: str = None) -> str:
    """
    Send a task to a specified remote agent for processing using SSE streaming.
    The tool waits for the complete response and only returns the final result.
    If server_url is not provided, it defaults to the CAREFLOW_CALLER_URL.
    """
    try:
        if not server_url:
            # Use the imported CAREFLOW_CALLER_URL which correctly points to localhost:8000
            server_url = CAREFLOW_CALLER_URL

        # Generate IDs
        request_id = int(uuid.uuid1().int >> 64)
        task_id = f"task_{int(uuid.uuid1().int >> 64)}_{uuid.uuid4().hex[:9]}"

        rpc_request = {
            "jsonrpc": "2.0",
            "method": "message/stream",
            "id": request_id,
            "params": {
                "message": {
                    "messageId": task_id,
                    "kind": "message",
                    "role": "user",
                    "parts": [{"kind": "text", "text": task}]
                }
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                server_url,
                headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
                json=rpc_request
            ) as response:
                if not response.ok:
                    return f"Error: HTTP {response.status} {response.reason}"

                final_text = ""
                print(f"\n[CAREFLOW -> CALLER]: Task sent: {task}")
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)
                            if data.get("result"):
                                res = data["result"]
                                if isinstance(res, dict):
                                    if res.get("status", {}).get("message", {}).get("parts"):
                                        parts = res["status"]["message"]["parts"]
                                        if parts and parts[0].get("text"):
                                            final_text = parts[0]["text"]
                                    elif res.get("text"):
                                        final_text = res["text"]
                                    elif res.get("message", {}).get("text"):
                                        final_text = res["message"]["text"]
                                elif isinstance(res, str):
                                    final_text = res
                        except:
                            pass
                
                    if final_text:
                        print(f"[CALLER -> CAREFLOW]: Response: {final_text}\n")
                        return final_text
                    
                print(f"[CALLER -> CAREFLOW]: No text response received.\n")
                return "ERROR: Patient Unreachable - No response text received from Caller Agent."

    except Exception as e:
        return f"ERROR: Connection Failed - {str(e)}"

a2a_tools = [list_remote_agents, send_remote_agent_task]