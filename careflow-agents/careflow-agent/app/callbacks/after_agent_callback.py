from google.adk.agents.callback_context import CallbackContext
from google.genai import types as genai_types
from ..core.security.model_armor import ModelArmorClient
import logging

logger = logging.getLogger(__name__)

# Global Model Armor Client
model_armor_client = ModelArmorClient()

async def sanitize_response_callback(callback_context: CallbackContext) -> genai_types.Content:
    """
    Callback that runs after the Pulse Agent generates a response.
    It scans the output for PII/PHI and applies redaction via Model Armor.
    """
    raw_response = callback_context.response.parts[0].text if callback_context.response and callback_context.response.parts else ""
    if not raw_response:
        return callback_context.response

    logger.info(f"Model Armor sanitizing response for agent: {callback_context.agent_name}")
    sanitize_result = await model_armor_client.sanitize_response(raw_response)
    
    if sanitize_result.get("is_blocked"):
        logger.warning(f"Model Armor BLOCKED response for agent {callback_context.agent_name}: {sanitize_result}")
        return genai_types.Content(
            role="model",
            parts=[genai_types.Part.from_text(
                text="[REDACTED] The system has detected sensitive information that cannot be shared."
            )]
        )
    
    return genai_types.Content(
        role="model",
        parts=[genai_types.Part.from_text(text=sanitize_result.get("sanitized_text", raw_response))]
    )