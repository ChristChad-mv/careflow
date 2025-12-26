import asyncio
import json
import uuid
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, AsyncGenerator, Optional, Mapping
from urllib.parse import urljoin
from utils.config import NGROK_URL
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
from utils.llm import get_model, ModelConfig
from pydantic import BaseModel, Field
from utils.conversation_relay import SessionData
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

        class SendRemoteAgentTaskInput(BaseModel):
            server_url: str = Field(description="The URL of the remote A2A server to send the task to.")
            task: str = Field(description="The task message to send to the remote agent. This should be a clear and concise description of the task.")

        @tool("send_remote_agent_task", args_schema=SendRemoteAgentTaskInput)
        async def send_remote_agent_task(server_url: str, task: str) -> str:
            """
            Send a task to a specified remote agent for processing using SSE streaming.
            The tool waits for the complete response and only returns the final result.
            Requires serverUrl and task parameters.
            """
            logger.info(f"calling send_remote_agent_task tool with server: {server_url}, task: {task}")

            if server_url not in self.a2a_servers:
                self.add_a2a_server(server_url)

            try:
                # Generate a unique request ID for this RPC call
                request_id = int(uuid.uuid1().int >> 64)

                # Generate a unique task ID
                task_id = f"task_{int(uuid.uuid1().int >> 64)}_{uuid.uuid4().hex[:9]}"

                # Prepare the JSON-RPC request for message/stream
                rpc_request = {
                    "jsonrpc": "2.0",
                    "method": "message/stream",
                    "id": request_id,
                    "params": {
                        "message": {
                            "messageId": task_id,
                            "kind": "message",
                            "role": "user",
                            "parts": [
                                {
                                    "kind": "text",
                                    "text": task,
                                }
                            ],
                        }
                    }
                }

                # Send the streaming request
                import aiohttp

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        server_url,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "text/event-stream, application/json",  # Accept both SSE and JSON
                        },
                        json=rpc_request
                    ) as response:
                        if not response.ok:
                            error_body = await response.text()
                            try:
                                error_json = json.loads(error_body)
                                if error_json.get("error"):
                                    raise ValueError(f"A2A Server Error: {error_json['error'].get('message')} "
                                                    f"(Code: {error_json['error'].get('code')})")
                            except json.JSONDecodeError:
                                pass
                            raise ValueError(f"HTTP error {response.status}: {response.reason}. "
                                           f"Response: {error_body or '(empty)'}")

                        # Check content type and handle accordingly
                        content_type = response.headers.get("Content-Type", "")
                        is_sse = content_type.startswith("text/event-stream")
                        is_json = content_type.startswith("application/json")

                        logger.info(f"Response Content-Type: {content_type}, isSSE: {is_sse}, isJSON: {is_json}")

                        if not is_sse and not is_json:
                            logger.warning(f"Unexpected Content-Type: {content_type}. Attempting to process as JSON.")

                        final_result = None

                        if is_sse:
                            event_data_buffer = ""

                            async for line in response.content:
                                line = line.decode('utf-8')
                                if line.strip() == "":
                                    # Empty line signifies end of an event
                                    if event_data_buffer:
                                        result = self._process_sse_event_data(event_data_buffer, request_id)

                                        logger.info(f"SSE event: {result}")

                                        if result and result.get("kind") == "status-update":
                                            # Handle latency task updates
                                            if (result.get("status", {}).get("message", {}).get("parts", [{}])[0].get("kind") == "data" and
                                                result["status"]["message"]["parts"][0].get("data", {}).get("latency") and
                                                os.environ.get("SUPPORTS_LATENCY_TASK_UPDATES") and
                                                not self.sent_interstitial_message):

                                                latency = result["status"]["message"]["parts"][0]["data"]["latency"]
                                                logger.info(f"Received latency update: {latency}ms")

                                                if latency > 3000:
                                                    await self.send_message_to_ws_channel_async(text=f"Processing your request, this should take about {latency // 1000} seconds...")
                                                elif latency > 1000:
                                                    await self.send_message_to_ws_channel_async(text="Please hold for just a couple of seconds while I process your request..")

                                                if NGROK_URL:
                                                    await self.send_message_to_ws_channel_async(source=f"https://{NGROK_URL}/keyboard-typing.mp3")

                                                self.sent_interstitial_message = True

                                            if result.get("final"):
                                                final_result = self._extract_final_message(result)
                                                self.sent_interstitial_message = False
                                                break

                                        event_data_buffer = ""
                                elif line.startswith("data:"):
                                    event_data_buffer += line[5:].strip() + "\n"

                            # Process any final buffered event data
                            if event_data_buffer.strip():
                                result = self._process_sse_event_data(event_data_buffer, request_id)
                                if (result and result.get("kind") == "status-update" and result.get("final")):
                                    final_result = self._extract_final_message(result)
                        else:
                            # Handle regular JSON response
                            json_response = await response.json()

                            logger.info('Received JSON response:', json.dumps(json_response, indent=2))

                            # Validate JSON-RPC response structure
                            if json_response.get("jsonrpc") != "2.0":
                                raise ValueError("Invalid JSON-RPC response format")

                            # Check for JSON-RPC errors
                            if json_response.get("error"):
                                raise ValueError(f"A2A Server Error: {json_response['error'].get('message')} "
                                              f"(Code: {json_response['error'].get('code')})")

                            # Extract the result
                            if json_response.get("result"):
                                logger.info('Processing result:', json.dumps(json_response["result"], indent=2))

                                # Try to extract message from various possible structures
                                if json_response["result"].get("message", {}).get("text"):
                                    final_result = json_response["result"]["message"]["text"]
                                elif json_response["result"].get("message", {}).get("parts"):
                                    parts = json_response["result"]["message"]["parts"]
                                    text_parts = [p.get("text") for p in parts if p.get("kind") == "text" and p.get("text")]
                                    final_result = "".join(text_parts)
                                elif json_response["result"].get("text"):
                                    final_result = json_response["result"]["text"]
                                elif isinstance(json_response["result"], str):
                                    final_result = json_response["result"]
                                else:
                                    # Fallback: stringify the result
                                    final_result = json.dumps(json_response["result"])
                            else:
                                final_result = "Task completed but no result was returned."

                # Return the final result
                if final_result is not None:
                    return f"A2A task completed successfully. Response: {final_result}"
                return "A2A task completed but no final message was received."

            except Exception as error:
                logger.error(f"Error sending task to A2A server {server_url}:", error)
                return f"Failed to send task to A2A server at {server_url}: {str(error)}"

        return [list_remote_agents, send_remote_agent_task]

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
        return config
    except Exception as error:
        logger.error(f'Error reading config.yaml: {error}')
        raise error

# Read configuration
config = read_config()

# Create agent instance
agent = Agent(
    system_message=config['client']['system'],
    a2a_servers=[f"http://localhost:{server['port']}" for server in config['servers']]
)
