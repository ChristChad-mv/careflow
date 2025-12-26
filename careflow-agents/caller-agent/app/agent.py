import asyncio
import json
import uuid
import os
import yaml
import datetime
from pathlib import Path
from typing import List, Dict, Any, AsyncGenerator, Optional, Mapping
from urllib.parse import urljoin
from .app_utils.config import NGROK_URL
from fastapi import WebSocket
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
    AIMessageChunk,
)
from langchain_core.tools import tool # type: ignore[import]
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent # type: ignore[import]
from .app_utils.config import get_model, ModelConfig
from pydantic import BaseModel, Field
from .app_utils.conversation_relay import SessionData
from a2a.types import (
    AgentCard,
)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ngrok_url: Optional[str] = NGROK_URL

def format_params(obj: Mapping[str, Any], depth: int = 0):
    indent = "    " * depth
    return '\n'.join([
        f"{indent}{key} ({value or 'unknown'})"
        if not isinstance(value, dict)
        else f"{indent}{key}:\n{format_params(value, depth + 2)}"
        for key, value in obj.items()
    ])

class Agent:
    """
    Agent class for handling conversations and A2A communication.
    """

    def __init__(self, system_message: str, a2a_servers: List[str] = []):
        """
        Create a new Agent instance.

        Args:
            system_message: The system message to initialize the agent with.
            a2a_servers: Optional list of A2A servers for communication.
        """
        self.system_message = SystemMessage(content=system_message or '')

        self.model = get_model(ModelConfig(streaming=True))
        self.memory = MemorySaver()
        self.a2a_servers = a2a_servers or []
        self.agent_cards: List[AgentCard] = []
        self.ws = None
        self.sent_interstitial_message = False

        self.agent = create_react_agent(
            model=self.model,
            tools=self.get_a2a_tools(),
            checkpointer=self.memory
        )

    async def init(self):
        """Initialize the agent by loading agent cards from A2A servers."""
        await self.load_agent_cards()

    async def load_agent_cards(self):
        """
        Load agent cards from all configured A2A servers.
        This method fetches agent cards during initialization to avoid repeated requests.
        """
        logger.info('Loading agent cards from A2A servers...')

        async def fetch_agent_card(server_url: str):
            try:
                # Construct the agent card URL
                agent_card_url = urljoin(server_url, "/.well-known/agent.json")

                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(agent_card_url, headers={"Accept": "application/json"}) as response:
                        if not response.ok:
                            raise Exception(f"Failed to fetch agent card: {response.status} {response.reason}")

                        agent_card = await response.json()
                        logger.info(f"Fetched agent card from {server_url}: {agent_card}")
                        return agent_card
            except Exception as error:
                logger.error(f"Error fetching agent card from {server_url}: {error}")
                return None

        # Use asyncio.gather to handle servers in parallel
        tasks = [fetch_agent_card(server_url) for server_url in self.a2a_servers]
        results = await asyncio.gather(*tasks)
        self.agent_cards = [
            AgentCard.model_validate(card) for card in results if card is not None
        ]

        logger.info(f"Loaded {len(self.agent_cards)} agent cards")

        if self.agent_cards:
            formatted_cards: List[str] = []
            for i, card in enumerate(self.agent_cards):
                skills_formatted = ""
                if card.skills and len(card.skills) > 0:
                    skills: List[str] = []
                    for skill in card.skills:
                        skill_info = f"    • {skill.name}: {skill.description}"
                        if skill.examples and len(skill.examples) > 0:
                            skill_info += f"\n      Examples: {', '.join(skill.examples)}"
                        skills.append(skill_info)
                    skills_formatted = "\n".join(skills)
                else:
                    skills_formatted = "    None specified"

                extensions_formatted = "None specified"

                if card.capabilities and card.capabilities.extensions:
                    extensions: List[str] = []
                    for extension in card.capabilities.extensions:
                        params_str = "None specified"
                        if extension.params and isinstance(extension.params, dict):
                            params_str = format_params(extension.params)

                        extensions.append(f"{extension.description}\n    Params: \n      {params_str}")
                    extensions_formatted = "\n".join(extensions)

                formatted_card = f"""{i + 1}. {card.name or 'Unnamed Agent'}
  Server URL: {self.a2a_servers[i] if i < len(self.a2a_servers) else 'Unknown'}
  Description: {card.description or 'No description provided'}
  Skills:
{skills_formatted}
  Extensions: {extensions_formatted}"""
                formatted_cards.append(formatted_card)

            formatted_cards_str = "\n\n".join(formatted_cards)
            logger.info(f"Available Remote Agents:\n{formatted_cards_str}")

            self.system_message.content += f"\n\nAvailable Remote Agents:\n{formatted_cards_str}"

    async def stream_message(self, user_message: str, session_data: SessionData) -> AsyncGenerator[str, None]:
        """
        Handle a conversation with the agent, streaming the response.

        Args:
            user_message: The user's message to the agent.
            session_data: The session data containing conversation history.

        Yields:
            Response chunks as strings.
        """
        try:
            session_id = session_data.call_sid or 'default-session'

            # Convert conversation history to LangGraph messages
            messages: List[BaseMessage] = []
            for msg in session_data.conversation:
                if msg.role == 'user':
                    messages.append(HumanMessage(content=msg.content))
                else:
                    messages.append(AIMessage(content=msg.content))

            await self.send_message_to_ws_channel_async(source=f"https://{NGROK_URL}/public/keyboard-typing.mp3")
            messages.append(HumanMessage(content=user_message))

            # Stream events from the agent
            streams = self.agent.astream_events(
                {
                    "messages": [self.system_message] + messages if self.system_message else messages,
                },
                config={
                    "configurable": {"thread_id": session_id},
                    "callbacks": [],
                },
                version="v2"
            )

            full_response = ''

            async for stream in streams:
                if "event" not in stream:
                    continue

                if stream.get('event') in ('on_chat_model_stream', 'on_llm_stream'):
                    data = stream.get('data')
                    if not isinstance(data, dict):
                        continue

                    chunk = data.get('chunk')
                    if not isinstance(chunk, AIMessageChunk):
                        continue

                    content = chunk.content
                    if content and isinstance(content, str):
                        full_response += content
                        yield content

            logger.info(f"Agent streaming response for session {session_id}: {full_response}")

        except Exception as error:
            logger.error('Error in handle_conversation_with_agent_stream:', error)
            yield "I apologize, but I encountered an error processing your request. Please try again."

    def add_a2a_server(self, server_url: str) -> None:
        """Add an A2A server URL to the list of available servers."""
        if server_url not in self.a2a_servers:
            self.a2a_servers.append(server_url)
            logger.info(f"Added A2A server: {server_url}")
        else:
            logger.info(f"A2A server already exists: {server_url}")

    def get_a2a_tools(self):
        """Get the A2A tools for the agent."""

        @tool("list_remote_agents")
        async def list_remote_agents() -> str:
            """
            List all remote agents available for A2A communication, returning their AgentCard
            metadata including capabilities, authentication, and provider information.
            """
            logger.info("calling list_remote_agents tool")

            agent_cards: List[AgentCard] = []
            async def fetch_agent_card(server_url: str):
                try:
                    # Construct the agent card URL
                    agent_card_url = urljoin(server_url, "/.well-known/agent.json")
                    logger.info(f"Fetching agent card from: {agent_card_url}")

                    # Fetch the agent card
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(agent_card_url, headers={"Accept": "application/json"}) as response:
                            if not response.ok:
                                logger.error(f"Failed to fetch agent card from {agent_card_url}: {response.status} {response.reason}")
                                return None

                            agent_card_data = await response.json()
                            logger.info(f"Fetched agent card from {server_url}:", agent_card_data)
                            return AgentCard.model_validate(agent_card_data)
                except Exception as error:
                    logger.error(f"Error fetching agent card from {server_url}: {error}")
                    return None

            tasks = [fetch_agent_card(server_url) for server_url in self.a2a_servers]
            results = await asyncio.gather(*tasks)

            for card in results:
                if card is not None:
                    agent_cards.append(card)

            # Return a formatted string instead of the raw object array
            if not agent_cards:
                return "No remote A2A servers are currently available."

            formatted_cards: List[str] = []
            for i, card in enumerate(agent_cards):
                skills_formatted = ""
                if card.skills and len(card.skills) > 0:
                    skills: List[str] = []
                    for skill in card.skills:
                        skill_info = f"    • {skill.name}: {skill.description}"
                        if skill.examples and len(skill.examples) > 0:
                            skill_info += f"\n      Examples: {', '.join(skill.examples)}"
                        skills.append(skill_info)
                    skills_formatted = "\n".join(skills)
                else:
                    skills_formatted = "    None specified"

                formatted_card = (
                    f"{i + 1}. {card.name or 'Unnamed Agent'}\n"
                    f"   Server URL: {self.a2a_servers[i] if i < len(self.a2a_servers) else 'Unknown'}\n"
                    f"   Description: {card.description or 'No description provided'}\n"
                    f"   Skills:\n{skills_formatted}"
                )
                formatted_cards.append(formatted_card)

            return "Available remote A2A servers:\n\n" + "\n\n".join(formatted_cards)

        class SendMessageInput(BaseModel):
            server_url: str = Field(description="The URL of the remote A2A server.")
            message: str = Field(description="The message content to send.")
            task_id: Optional[str] = Field(default=None, description="Optional taskId to continue an existing conversation.")

        @tool("send_message", args_schema=SendMessageInput)
        async def send_message(server_url: str, message: str, task_id: Optional[str] = None) -> str:
            """
            Send a message to a remote agent. Use this to start a conversation or reply to an existing one.
            If you are replying or following up, you MUST provide the 'task_id' from the previous response.
            """
            logger.info(f"calling send_message tool with server: {server_url}, task_id: {task_id}")

            if server_url not in self.a2a_servers:
                self.add_a2a_server(server_url)

            try:
                request_id = int(uuid.uuid1().int >> 64)
                
                # Use provided task_id or generate new one if starting new conversation
                # current_task_id = task_id or f"task_{int(uuid.uuid1().int >> 64)}_{uuid.uuid4().hex[:9]}"
                
                message_payload = {
                    "messageId": str(uuid.uuid4()),
                    "kind": "message",
                    "role": "user",
                    "parts": [{"kind": "text", "text": message}],
                }
                
                if task_id:
                    message_payload["taskId"] = task_id
                
                params = {
                    "message": message_payload
                }

                rpc_request = {
                    "jsonrpc": "2.0",
                    "method": "message/stream", # Use streaming to get immediate response
                    "id": request_id,
                    "params": params
                }

                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        server_url,
                        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
                        json=rpc_request
                    ) as response:
                        if not response.ok:
                            return f"Error: {response.status} {await response.text()}"

                        # Process SSE response similar to before
                        final_result = None
                        returned_task_id = None
                        
                        raw_content = ""
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            raw_content += line + "\n"
                            if line.startswith("data:"):
                                try:
                                    data = json.loads(line[5:].strip())
                                    if data.get("result", {}).get("final"):
                                        final_result = self._extract_final_message(data["result"])
                                        returned_task_id = data["result"].get("taskId")
                                except:
                                    pass
                        
                        logger.info(f"DEBUG: Raw response from CareFlow: {raw_content}")
                        
                        result_str = f"Response: {final_result}"
                        
                        # --- EXPLICIT CONVERSATION LOGGING ---
                        print(f"\n[CALLER -> CAREFLOW]: {message}")
                        print(f"[CAREFLOW -> CALLER]: {final_result}\n")
                        # -------------------------------------

                        if returned_task_id:
                            result_str += f"\nTaskId: {returned_task_id}"
                        return result_str

            except Exception as e:
                return f"Failed to send message: {str(e)}"

        class SubscribeInput(BaseModel):
            server_url: str = Field(description="The URL of the remote A2A server.")
            task_id: str = Field(description="The ID of the task to subscribe to.")

        @tool("subscribe_to_task", args_schema=SubscribeInput)
        async def subscribe_to_task(server_url: str, task_id: str) -> str:
            """
            Subscribe to real-time updates for a specific task.
            Use this when you want to monitor a long-running process.
            """
            # In a real implementation, this would likely open a persistent connection
            # For this agent, we might just verify we CAN subscribe or poll
            # But let's implement the RPC call
            return f"Subscribed to task {task_id} (Simulation: Real-time updates would flow here)"

        class RegisterWebhookInput(BaseModel):
            server_url: str = Field(description="The URL of the remote A2A server.")
            task_id: str = Field(description="The ID of the task.")
            webhook_url: str = Field(description="The URL where notifications should be sent.")

        @tool("register_webhook", args_schema=RegisterWebhookInput)
        async def register_webhook(server_url: str, task_id: str, webhook_url: str) -> str:
            """
            Register a webhook to receive push notifications for a task.
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
                
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        server_url,
                        headers={"Content-Type": "application/json"},
                        json=rpc_request
                    ) as response:
                        if not response.ok:
                            return f"Error registering webhook: {await response.text()}"
                        return f"Successfully registered webhook {webhook_url} for task {task_id}"
            except Exception as e:
                return f"Failed to register webhook: {str(e)}"

        class CallPatientInput(BaseModel):
            message: str = Field(description="The message to speak/send to the patient.")
            patient_name: str = Field(description="Name of the patient.")
            patient_id: str = Field(description="ID of the patient.")
            expect_reply: bool = Field(default=True, description="If True (default), waits for the patient to reply. If False, sends the message and returns immediately (use for 'One moment...' messages).")

        @tool("call_patient", args_schema=CallPatientInput)
        async def call_patient(message: str, patient_name: str, patient_id: str, expect_reply: bool = True) -> str:
            """
            Simulate a call to the patient.
            Sends the message to the patient's phone (simulated server) and returns their reply.
            """
            import aiohttp
            
            phone_server_url = "http://localhost:9000/incoming_call"
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        phone_server_url,
                        json={
                            "message": message,
                            "patient_name": patient_name,
                            "patient_id": patient_id,
                            "expect_reply": expect_reply
                        }
                    ) as response:
                        if not response.ok:
                            return f"Failed to call patient: {response.status}"
                        
                        data = await response.json()
                        if not expect_reply:
                            return "Message sent to patient. (No reply expected yet)"
                        return f"Patient Replied: {data.get('response')}"
            except Exception as e:
                return f"Failed to connect to patient phone: {str(e)}"

        return [list_remote_agents, send_message, subscribe_to_task, register_webhook, call_patient]

    def set_ws_channel(self, ws: WebSocket) -> None:
        """Set the WebSocket channel for communication."""
        self.ws = ws

    # def send_message_to_ws_channel(self, text: Optional[str] = None, source: Optional[str] = None) -> None:
    #     """Send a message to the WebSocket channel."""
    #     if not self.ws or not hasattr(self.ws, 'send'):
    #         logger.error("WebSocket is not connected. Cannot send message.")
    #         return

    #     message = None

    #     if text:
    #         message = {
    #             "type": "text",
    #             "token": text,
    #             "last": True,
    #             "interruptible": False,
    #             "preemptible": False,
    #         }
    #     elif source:
    #         message = {
    #             "type": "play",
    #             "source": source,
    #             "interruptible": False,
    #             "preemptible": True,
    #         }

    #     if message:
    #         self.ws.send(json.dumps(message))
    #     else:
    #         logger.info("No message to send.")

    async def send_message_to_ws_channel_async(self, text: Optional[str] = None, source: Optional[str] = None) -> None:
        """Send a message to the WebSocket channel asynchronously."""
        if not self.ws:
            logger.warning("WebSocket is not connected. Cannot send message.")
            return

        message = None

        if text:
            message = {
                "type": "text",
                "token": text,
                "last": True,
                "interruptible": False,
                "preemptible": False,
            }
        elif source:
            message = {
                "type": "play",
                "source": source,
                "interruptible": False,
                "preemptible": True,
            }

        if message:
            await self.ws.send_text(json.dumps(message))
        else:
            logger.warning("No message to send.")

    def _process_sse_event_data(self, json_data: str, original_request_id: int) -> Optional[Dict[str, Any]]:
        """
        Helper method to process SSE event data from A2A streaming responses.

        Args:
            json_data: The JSON string from the SSE data field
            original_request_id: The original request ID to validate against

        Returns:
            The parsed result object or None
        """
        if not json_data.strip():
            logger.info("Attempted to process empty SSE event data")
            return {}

        try:
            # Parse the JSON-RPC response from the SSE data
            response: Dict[str, Any] = json.loads(json_data.rstrip("\n"))

            # Validate basic JSON-RPC structure
            if not isinstance(response, dict):
                logger.error("Invalid JSON-RPC response structure in SSE data")
                return None

            if not response.get("jsonrpc") == "2.0":
                logger.error("Invalid JSON-RPC version in SSE data")
                return None

            # Check for request ID mismatch (optional validation)
            if response.get("id") != original_request_id:
                logger.info(f"SSE Event's JSON-RPC response ID mismatch. "
                      f"Expected: {original_request_id}, got: {response.get('id')}")

            # Check for errors in the response
            if response.get("error"):
                err = response["error"]
                raise ValueError(f"SSE event contained an error: {err.get('message')} (Code: {err.get('code')})")

            # Return the result if it exists
            if "result" in response:
                return response["result"]

            logger.error("SSE event JSON-RPC response missing result field")
            return {}

        except Exception as error:
            if isinstance(error, ValueError) and str(error).startswith("SSE event contained an error"):
                raise error  # Re-throw JSON-RPC errors
            logger.error("Failed to parse SSE event data:", json_data, error)
            return {}

    def _extract_final_message(self, event: Dict[str, Any]) -> Optional[str]:
        """
        Helper method to extract the final message from a TaskStatusUpdateEvent.

        Args:
            event: The status update event

        Returns:
            The extracted message text or None
        """
        try:
            # Handle different possible structures for the final message
            if event and event.get("kind") == "status-update" and event.get("final"):
                # Try to extract message from various possible structures
                if event.get("status", {}).get("message", {}).get("text"):
                    return event["status"]["message"]["text"]

                if event.get("status", {}).get("message", {}).get("parts"):
                    parts = event["status"]["message"]["parts"]
                    return "".join([p.get("text", "") for p in parts if p.get("kind") == "text"])

                if event.get("message", {}).get("text"):
                    return event["message"]["text"]

                if event.get("message", {}).get("parts"):
                    parts = event["message"]["parts"]
                    return "".join([p.get("text", "") for p in parts if p.get("kind") == "text"])

                # Fallback: try to find any text content in the event
                if event.get("text"):
                    return event["text"]

            return None

        except Exception as error:
            logger.error("Error extracting final message from event:", event, error)
            return None


def read_config():
    """Read configuration from YAML file."""
    try:
        # Try finding config relative to this file
        current_file = Path(__file__).resolve()
        # Go up two levels: src/client -> src -> caller-agent
        config_path = current_file.parent.parent.parent / 'config.yaml'
        
        if not config_path.exists():
             # Fallback to CWD
             config_path = Path.cwd() / 'config.yaml'

        logger.info(f"Reading config from: {config_path}")
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        
        # Override servers with environment variable if provided (for Cloud Run)
        agent_url = os.environ.get("CAREFLOW_AGENT_URL", f"http://localhost:{config['servers'][0]['port']}")
        config['servers'] = [{"name": "CareFlow Agent", "port": None, "url": agent_url}]
        
        return config
    except Exception as error:
        logger.error(f'Error reading config.yaml: {error}')
        raise error

# Read configuration
config = read_config()

# Create agent instance
# Use environment variable for A2A server URL or fall back to config
a2a_server_urls = [s.get('url') or f"http://localhost:{s['port']}" for s in config['servers'] if s.get('url') or s.get('port')]

agent = Agent(
    system_message=config['client']['system'] + """
    
    IMPORTANT: You are a **Nurse Caller Agent**.
    
    **Your Goal:**
    - You will receive tasks from the CareFlow Agent to interview specific patients.
    - The task will include the Patient Name, ID, and what to ask (e.g., Risk Level, Status).
    - You must use the `call_patient` tool to "speak" with the patient.
    **Interview Process:**
        1.  Start by introducing yourself.
        2.  Ask the questions requested by CareFlow ONE BY ONE. Wait for the patient's reply.
        3.  **Handling Questions (CRITICAL):** 
            - If the patient asks for information you do not have (e.g., "What is the name of my medication?", "What is my latest risk score?"):
            - **Step A:** Tell the patient: "One moment, let me check with the care team." 
              -> **USE `call_patient` with `expect_reply=False`**. This allows you to act immediately without waiting for the patient to say "Okay".
            - **Step B:** **IMMEDIATELY** use `send_message` to ask the CareFlow Agent: "The patient is asking for [Information]. Can you provide it?"
            - **Step C:** When CareFlow replies with the info, use `call_patient` (with `expect_reply=True`) to tell the patient the answer.
        4.  If the patient reports an issue (e.g., "I feel dizzy"), ask a follow-up question.
        5.  Once you have the information, thank the patient and end the call.
        6.  **CRITICAL:** Report the summary of the interview back to the CareFlow Agent as your final answer.
    
    **Collaboration Rules:**
    - Do NOT ask for the list of patients. Wait to be assigned a patient.
    - Use `call_patient` for the interview.
    - Use `send_message` to communicate with the 'CareFlow Pulse Agent' (to report back OR to ask for help).
    - ALWAYS pass the 'task_id' to maintain the conversation context.
    """,
    a2a_servers=a2a_server_urls
)
