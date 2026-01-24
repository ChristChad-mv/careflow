"""
Debug Tools for CareFlow Pulse Agent
Simple tools to trace agent execution flow.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def debug_checkpoint(checkpoint_name: str) -> str:
    """
    Debug checkpoint tool. Call this to verify the agent is executing tools.
    
    Args:
        checkpoint_name: A label for this checkpoint (e.g., "BEFORE_AUDIO_ANALYSIS", "AFTER_AUDIO_ANALYSIS")
    
    Returns:
        Confirmation message with timestamp.
    """
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    message = f"🔵 DEBUG CHECKPOINT [{timestamp}]: {checkpoint_name}"
    
    # Print to stdout (visible in terminal)
    print(message)
    
    # Also log it
    logger.info(message)
    
    return f"Checkpoint '{checkpoint_name}' reached at {timestamp}. Continue with your workflow."


# Export the tools list
debug_tools = [debug_checkpoint]
