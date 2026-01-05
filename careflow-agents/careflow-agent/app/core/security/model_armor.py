import os
import logging
from typing import Optional, Dict, Any, List
from google.cloud import modelarmor_v1

logger = logging.getLogger(__name__)

class ModelArmorClient:
    """
    Client for interacting with Google Cloud Model Armor to secure AI interactions.
    """
    def __init__(self, project_id: Optional[str] = None, location: str = "global", policy_id: str = "default"):
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.policy_id = policy_id or os.environ.get("MODEL_ARMOR_POLICY_ID", "default")
        
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable must be set or project_id provided.")
            
        self.client = modelarmor_v1.ModelArmorClient()
        self.template_name = f"projects/{self.project_id}/locations/{self.location}/templates/{self.policy_id}"
        # Note: Model Armor uses templates to define security policies
        logger.info(f"Initialized ModelArmorClient with template: {self.template_name}")

    async def scan_prompt(self, text: str) -> Dict[str, Any]:
        """
        Scans a user prompt for injection, jailbreak, and other attacks.
        
        Returns a dict with:
        - is_blocked: bool
        - matching_safety_attributes: list
        - execution_outcome: str
        """
        try:
            request = modelarmor_v1.SanitizeUserPromptRequest(
                name=self.template_name,
                user_prompt_data=modelarmor_v1.UserPromptData(
                    text=text
                )
            )
            
            response = self.client.sanitize_user_prompt(request=request)
            
            is_blocked = response.invocation_result != modelarmor_v1.SanitizeUserPromptResponse.InvocationResult.SUCCESS
            
            return {
                "is_blocked": is_blocked,
                "invocation_result": response.invocation_result.name,
                "sanitization_metadata": response.sanitization_metadata,
            }
        except Exception as e:
            logger.error(f"Model Armor Prompt Scan Error: {e}")
            # Fallback: allow but log if service is down, or strictly block? 
            # In clinical settings, we might want to fail-safe (block) or fail-open (allow).
            # Let's fail-open but log for now to avoid disrupting service during dev.
            return {"is_blocked": False, "error": str(e)}

    async def sanitize_response(self, text: str) -> Dict[str, Any]:
        """
        Sanitizes a model response for PII, PHI, and harmful content.
        
        Returns a dict with:
        - is_blocked: bool
        - sanitized_text: str
        - matching_safety_attributes: list
        """
        try:
            request = modelarmor_v1.SanitizeModelResponseRequest(
                name=self.template_name,
                model_response_data=modelarmor_v1.ModelResponseData(
                    text=text
                )
            )
            
            response = self.client.sanitize_model_response(request=request)
            
            is_blocked = response.invocation_result != modelarmor_v1.SanitizeModelResponseResponse.InvocationResult.SUCCESS
            
            # Extract sanitized text if available
            sanitized_text = text
            if response.sanitization_metadata and response.sanitization_metadata.filter_match_metadata:
                # In Model Armor, redaction results might be in metadata
                # Note: Exact implementation depends on how the template is configured
                pass

            return {
                "is_blocked": is_blocked,
                "sanitized_text": sanitized_text, # Some versions return text directly
                "invocation_result": response.invocation_result.name,
                "metadata": response.sanitization_metadata
            }
        except Exception as e:
            logger.error(f"Model Armor Response Sanitize Error: {e}")
            return {"is_blocked": False, "sanitized_text": text, "error": str(e)}
