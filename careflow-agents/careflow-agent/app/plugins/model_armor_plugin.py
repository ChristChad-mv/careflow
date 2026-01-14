import logging
from typing import Optional
from google.adk.plugins import BasePlugin
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types as genai_types

from app.core.security.model_armor import ModelArmorClient

logger = logging.getLogger(__name__)

class ModelArmorPlugin(BasePlugin):
    """
    ADK Plugin that integrates Google Cloud Model Armor for global input protection.
    """
    def __init__(self, client: ModelArmorClient):
        super().__init__(name="model_armor_security")
        self.client = client

    async def before_model_callback(self, callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
        """
        Intercepts LLM requests to scan the last user message for injection or other attacks.
        """
        # Get the latest user message from the request contents
        if not llm_request.contents:
            return None
            
        last_content = llm_request.contents[-1]
        if last_content.role != "user":
            return None
            
        # Combine text parts for scanning
        text_to_scan = ""
        for part in last_content.parts:
            if hasattr(part, 'text') and part.text:
                text_to_scan += part.text + "\n"
        
        if not text_to_scan.strip():
            return None

        # BYPASS: Allow management triggers to skip scanning to avoid false positives
        management_triggers = ["start daily rounds", "check daily patient status"]
        if any(trigger in text_to_scan.lower() for trigger in management_triggers):
            logger.info(f"🛡️ Model Armor BYPASS for management command: {text_to_scan.strip()}")
            return None

        logger.info(f"Model Armor scanning prompt for agent: {callback_context.agent_name}. Text: {text_to_scan.strip()}")
        
        scan_result = await self.client.scan_prompt(text_to_scan)
        
        if scan_result.get("is_blocked"):
            logger.warning(f"Model Armor BLOCKED prompt for agent {callback_context.agent_name}: {scan_result}")
            
            # Return a canned safety response that overrides the model call
            return LlmResponse(
                content=genai_types.Content(
                    role="model",
                    parts=[genai_types.Part.from_text(
                        text="I'm sorry, but I cannot process this request due to security and safety policies."
                    )]
                )
            )
            
        return None

    async def after_model_callback(self, callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
        """
        Intercepts model responses to scan for PII/PHI and apply redaction.
        """
        if not llm_response.content or not llm_response.content.parts:
            return None
            
        raw_response = "".join([p.text for p in llm_response.content.parts if hasattr(p, 'text') and p.text])
        if not raw_response.strip():
            return None

        logger.info(f"Model Armor sanitizing response for agent: {callback_context.agent_name}")
        sanitize_result = await self.client.sanitize_response(raw_response)
        
        if sanitize_result.get("is_blocked"):
            logger.warning(f"Model Armor BLOCKED response for agent {callback_context.agent_name}: {sanitize_result}")
            return LlmResponse(
                content=genai_types.Content(
                    role="model",
                    parts=[genai_types.Part.from_text(
                        text="[REDACTED] The system has detected sensitive information that cannot be shared."
                    )]
                )
            )
        
        # If redacted, return a new response with the sanitized text
        if sanitize_result.get("sanitized_text") != raw_response:
             return LlmResponse(
                content=genai_types.Content(
                    role="model",
                    parts=[genai_types.Part.from_text(text=sanitize_result.get("sanitized_text"))]
                )
            )

        return None
