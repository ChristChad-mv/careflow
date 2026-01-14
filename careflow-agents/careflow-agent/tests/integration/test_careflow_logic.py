
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk import runners
from google.genai import types

# Import the actual agent to test its configuration
from app.agent import root_agent

@pytest.fixture
def mock_model():
    """Mock the GenerativeModel to avoid real API calls."""
    mock = MagicMock()
    return mock

# Helper for async context managers (Same as unit test)
class AsyncContextManager:
    def __init__(self, return_value=None):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

def test_pulse_agent_tool_selection():
    """
    Test that the Pulse Agent selects the correct tools given a specific prompt.
    """
    # 1. Verify Tools are attached
    # Helper to get name whether it's a FunctionTool or raw function
    def get_name(t):
        if hasattr(t, 'name'): return t.name
        if hasattr(t, '__name__'): return t.__name__
        return str(t)

    tools_list = root_agent.assistant.tools if hasattr(root_agent, 'assistant') else root_agent.tools
    tool_names = [get_name(t) for t in tools_list]
    
    assert "send_remote_agent_task" in tool_names
    assert "list_remote_agents" in tool_names

    # 2. Verify System Instruction
    instruction = root_agent.assistant.instruction if hasattr(root_agent, 'assistant') else root_agent.instruction
    assert "CareFlow Pulse" in instruction
    assert "medical" in instruction

@pytest.mark.asyncio
async def test_agent_run_simulated():
    """
    Simulate a run where we mock the LLM's decision to call a tool.
    """
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test", app_name="test")
    
    from app.tools.a2a_tools import send_remote_agent_task
    
    # Mock Response
    mock_response = MagicMock()
    mock_response.ok = True
    async def async_iter():
         yield b"data: {\"result\": {\"text\": \"Call Initiated\"}}\n\n"
    mock_response.content = AsyncMock()
    mock_response.content.__aiter__ = MagicMock(return_value=async_iter())

    # Mock Session with our Helper
    mock_session = MagicMock()
    mock_session.post.return_value = AsyncContextManager(return_value=mock_response)

    # Patch ClientSession to return our mock session
    with patch("aiohttp.ClientSession", return_value=AsyncContextManager(return_value=mock_session)):
        result = await send_remote_agent_task("Check on patient", "http://mock-url")
        assert result == "Call Initiated"
