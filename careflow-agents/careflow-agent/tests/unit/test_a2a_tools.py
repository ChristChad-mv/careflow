import pytest
import aiohttp
import json
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from app.tools.a2a_tools import list_remote_agents, send_remote_agent_task

# Helper for async context managers
class AsyncContextManager:
    def __init__(self, return_value=None):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

# --- Test list_remote_agents ---

@pytest.mark.asyncio
async def test_list_remote_agents_success():
    """Test successful retrieval of list_remote_agents."""
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json = AsyncMock(return_value={
        "name": "Caller Agent",
        "description": "Handles voice calls",
        "url": "http://localhost:8000",
        "version": "1.0.0",
        "skills": ["voice"],
        "capabilities": ["phone"]
    })
    
    # Mock the session: session.get() returns a CM that yields mock_response
    mock_session = MagicMock()
    mock_session.get.return_value = AsyncContextManager(return_value=mock_response)
    # Mock AgentCard to avoid strict validation issues during unit test
    mock_agent_card = MagicMock()
    mock_agent_card.name = "Caller Agent"
    mock_agent_card.url = "http://localhost:8000"
    mock_agent_card.description = "Handles voice calls"
    
    with patch("aiohttp.ClientSession", return_value=AsyncContextManager(return_value=mock_session)), \
         patch("app.tools.a2a_tools.AgentCard.model_validate", return_value=mock_agent_card):
        result = await list_remote_agents()
        assert "Caller Agent" in result
        assert "http://localhost:8000" in result

@pytest.mark.asyncio
async def test_list_remote_agents_failure():
    """Test failure when retrieving agents."""
    mock_response = MagicMock()
    mock_response.ok = False
    
    mock_session = MagicMock()
    mock_session.get.return_value = AsyncContextManager(return_value=mock_response)
    
    with patch("aiohttp.ClientSession", return_value=AsyncContextManager(return_value=mock_session)):
        result = await list_remote_agents()
        assert "No remote A2A servers are currently available" in result


# --- Test send_remote_agent_task ---

@pytest.mark.asyncio
async def test_send_remote_agent_task_success():
    """Test sending a task to remote agent and receiving streaming response."""
    
    # Mock the SSE Stream content
    sse_lines = [
        b"data: {\"result\": {\"text\": \"Task Completed\"}}\n\n"
    ]
    
    mock_response = MagicMock()
    mock_response.ok = True
    
    # Correctly mock async iterator for response.content
    async def async_iter():
        for line in sse_lines:
            yield line
            
    mock_response.content = AsyncMock()
    mock_response.content.__aiter__ = MagicMock(return_value=async_iter())
    
    mock_session = MagicMock()
    mock_session.post.return_value = AsyncContextManager(return_value=mock_response)
    
    with patch("aiohttp.ClientSession", return_value=AsyncContextManager(return_value=mock_session)):
        result = await send_remote_agent_task("Call patient", "http://fake-url")
        assert result == "Task Completed"

@pytest.mark.asyncio
async def test_send_remote_agent_task_failure():
    """Test handling of HTTP failure."""
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status = 500
    mock_response.reason = "Server Error"
    
    mock_session = MagicMock()
    mock_session.post.return_value = AsyncContextManager(return_value=mock_response)
    
    with patch("aiohttp.ClientSession", return_value=AsyncContextManager(return_value=mock_session)):
        result = await send_remote_agent_task("Call patient")
        assert "Error: HTTP 500 Server Error" in result
