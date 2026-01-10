import logging
from toolbox_core import ToolboxSyncClient
from ..app_utils.config_loader import MCP_TOOLBOX_URL

logger = logging.getLogger(__name__)

# Shared state for toolbox client and tools
toolbox_client = None
all_tools = []

def init_mcp_tools():
    global toolbox_client, all_tools
    try:
        # Don't use 'with' - we need to keep the session open
        toolbox_client = ToolboxSyncClient(MCP_TOOLBOX_URL)
        # Load our custom toolset
        all_tools = toolbox_client.load_toolset("patient_tools")
        print(f"Total tools available: {len(all_tools)} MCP tools")
    except Exception as e:
        logger.warning(f"⚠️ Warning: Could not load MCP tools from {MCP_TOOLBOX_URL}. Is toolbox running? Error: {e}")
        logger.warning("Agent will run with internal tools only.")