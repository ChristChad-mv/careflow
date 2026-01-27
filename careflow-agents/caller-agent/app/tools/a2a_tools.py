"""
CareFlow Pulse - A2A Communication Tools

This module implements A2A (Agent-to-Agent) protocol tools for
inter-agent communication with the CareFlow Pulse medical agent.

Author: CareFlow Pulse Team
Version: 1.0.0
"""

import json
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional

import aiohttp
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from a2a.types import AgentCard
from langchain_core.tools import tool

from ..schemas.tool_schemas import SendMessageInput, SubscribeInput, WebhookInput
from ..core.security.model_armor import ModelArmorClient

logger = logging.getLogger(__name__)

# Initialize Model Armor client for security scanning
model_armor_client = ModelArmorClient()


# =============================================================================
# A2A TOOLS FACTORY
# =============================================================================

def create_a2a_tools(
    agent_cards: List[AgentCard],
    a2a_servers: List[str],
    extract_response_fn: Callable[[Dict[str, Any]], Optional[str]]
) -> list:
    """
    Create A2A communication tools for the agent.
    
    This factory function creates tools that are bound to the agent's
    context (agent_cards, servers, etc.) without requiring class methods.
    
    Args:
        agent_cards: List of loaded AgentCard metadata
        a2a_servers: List of A2A server URLs
        extract_response_fn: Function to extract text from A2A response
    
    Returns:
        List of LangChain tools for A2A communication
    """
    
    @tool("list_remote_agents")
    async def list_remote_agents() -> str:
        """
        List all available remote A2A agents with their capabilities.
        
        Returns:
            Formatted list of available agents
        """
        logger.info("Listing remote agents")
        
        if not agent_cards:
            return "No remote A2A servers are currently available."
        
        formatted = []
        for i, card in enumerate(agent_cards):
            skills_str = "    None specified"
            if card.skills:
                skills = [f"    • {s.name}: {s.description}" for s in card.skills]
                skills_str = "\n".join(skills)
            
            server_url = a2a_servers[i] if i < len(a2a_servers) else 'Unknown'
            formatted.append(
                f"{i + 1}. {card.name or 'Unnamed'}\n"
                f"   URL: {server_url}\n"
                f"   Description: {card.description or 'No description'}\n"
                f"   Skills:\n{skills_str}"
            )
        
        return "Available remote A2A servers:\n\n" + "\n\n".join(formatted)
    
    @tool("send_message", args_schema=SendMessageInput)
    async def send_message(
        server_url: str,
        message: str,
        task_id: Optional[str] = None
    ) -> str:
        """
        Send a message to a remote A2A agent.
        
        Use this to communicate with CareFlow Pulse Agent for medical
        context, patient lookups, and clinical guidance.
        
        Args:
            server_url: Target A2A server URL
            message: Message to send
            task_id: Optional task ID for conversation continuity
        
        Returns:
            Agent response
        """
        # --- MODEL ARMOR INPUT SCAN ---
        logger.info(f"Model Armor scanning A2A prompt to {server_url}")
        input_scan = await model_armor_client.scan_prompt(message)
        if input_scan.get("is_blocked"):
            logger.warning(f"Model Armor BLOCKED A2A message to {server_url}")
            return "Error: Security policy blocked this request."
        # ------------------------------

        logger.info(f"Sending A2A message to {server_url}")
        
        # Track new servers dynamically
        if server_url not in a2a_servers:
            a2a_servers.append(server_url)
        
        try:
            request_id = int(uuid.uuid1().int >> 64)
            
            message_payload = {
                "messageId": str(uuid.uuid4()),
                "kind": "message",
                "role": "user",
                "parts": [{"kind": "text", "text": message}],
            }
            
            if task_id:
                message_payload["taskId"] = task_id
            
            rpc_request = {
                "jsonrpc": "2.0",
                "method": "message/stream",
                "id": request_id,
                "params": {"message": message_payload}
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
            
            # --- OIDC AUTHENTICATION ---
            if "run.app" in server_url:
                try:
                    auth_req = GoogleRequest()
                    # Determine audience (remove /rpc suffix if present)
                    audience = server_url[:-4] if server_url.endswith("/rpc") else server_url
                    # Remove trailing slash if present for cleaner audience match
                    if audience.endswith("/"): audience = audience[:-1]
                    
                    token = id_token.fetch_id_token(auth_req, audience)
                    headers["Authorization"] = f"Bearer {token}"
                except Exception as e:
                    logger.warning(f"Failed to generate OIDC token for {server_url}: {e}")
            # ---------------------------

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    server_url,
                    headers=headers,
                    json=rpc_request
                ) as response:
                    if not response.ok:
                        return f"Error: {response.status} {await response.text()}"
                    
                    # Process SSE response
                    final_result = None
                    returned_task_id = None
                    
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith("data:"):
                            try:
                                data = json.loads(line[5:].strip())
                                if data.get("result", {}).get("final"):
                                    final_result = extract_response_fn(data["result"])
                                    returned_task_id = data["result"].get("taskId")
                            except json.JSONDecodeError:
                                pass
                    
                    print(f"\n[CALLER -> CAREFLOW]: {message}")
                    print(f"[CAREFLOW -> CALLER]: {final_result}\n")
                    
                    # --- MODEL ARMOR OUTPUT SCAN ---
                    if final_result:
                        logger.info(f"Model Armor scanning A2A response from {server_url}")
                        output_scan = await model_armor_client.sanitize_response(final_result)
                        if output_scan.get("is_blocked"):
                            final_result = "[REDACTED] Clinical data blocked by security policy."
                        else:
                            final_result = output_scan.get("sanitized_text", final_result)
                    # -------------------------------

                    result = f"Response: {final_result}"
                    if returned_task_id:
                        result += f"\nTaskId: {returned_task_id}"
                    return result
                    
        except Exception as e:
            return f"Failed to send message: {str(e)}"
    
    @tool("subscribe_to_task", args_schema=SubscribeInput)
    async def subscribe_to_task(server_url: str, task_id: str) -> str:
        """
        Subscribe to real-time updates for a task.
        
        Args:
            server_url: Target A2A server URL
            task_id: Task ID to subscribe to
        
        Returns:
            Subscription confirmation
        """
        return f"Subscribed to task {task_id}"
    
    @tool("register_webhook", args_schema=WebhookInput)
    async def register_webhook(
        server_url: str,
        task_id: str,
        webhook_url: str
    ) -> str:
        """
        Register a webhook for push notifications.
        
        Args:
            server_url: Target A2A server URL
            task_id: Task ID
            webhook_url: Webhook URL for notifications
        
        Returns:
            Registration confirmation
        """
        try:
            request_id = int(uuid.uuid1().int >> 64)
            rpc_request = {
                "jsonrpc": "2.0",
                "method": "tasks/pushNotificationConfig/set",
                "id": request_id,
                "params": {
                    "taskId": task_id,
                    "pushNotificationConfig": {
                        "url": webhook_url,
                        "format": "json"
                    }
                }
            }
            
            headers = {"Content-Type": "application/json"}
             
            # --- OIDC AUTHENTICATION ---
            if "run.app" in server_url:
                try:
                    auth_req = GoogleRequest()
                    audience = server_url[:-4] if server_url.endswith("/rpc") else server_url
                    if audience.endswith("/"): audience = audience[:-1]
                    token = id_token.fetch_id_token(auth_req, audience)
                    headers["Authorization"] = f"Bearer {token}"
                except Exception as e:
                    logger.warning(f"Failed to generate OIDC token for {server_url}: {e}")
            # ---------------------------

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    server_url,
                    headers=headers,
                    json=rpc_request
                ) as response:
                    if not response.ok:
                        return f"Error: {await response.text()}"
                    return f"Webhook registered for task {task_id}"
        except Exception as e:
            return f"Failed to register webhook: {str(e)}"
    
    return [list_remote_agents, send_message, subscribe_to_task, register_webhook]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = ['create_a2a_tools']
