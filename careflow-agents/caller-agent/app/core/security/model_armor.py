import os
import logging
from typing import Optional, Dict, Any, List
# Ensure google-cloud-modelarmor is installed
try:
    from google.cloud import modelarmor_v1
except ImportError:
    modelarmor_v1 = None

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
            logger.warning("GOOGLE_CLOUD_PROJECT not set. ModelArmorClient will fail.")
            
        if modelarmor_v1:
            self.client = modelarmor_v1.ModelArmorClient()
            self.template_name = f"projects/{self.project_id}/locations/{self.location}/templates/{self.policy_id}"
            logger.info(f"Initialized ModelArmorClient with template: {self.template_name}")
        else:
            self.client = None
            logger.error("google-cloud-modelarmor package not found.")

    async def scan_prompt(self, text: str) -> Dict[str, Any]:
        if not self.client:
            return {"is_blocked": False, "error": "Model Armor client not initialized"}
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
            return {"is_blocked": False, "error": str(e)}

    async def sanitize_response(self, text: str) -> Dict[str, Any]:
        if not self.client:
            return {"is_blocked": False, "sanitized_text": text, "error": "Model Armor client not initialized"}
        try:
            request = modelarmor_v1.SanitizeModelResponseRequest(
                name=self.template_name,
                model_response_data=modelarmor_v1.ModelResponseData(
                    text=text
                )
            )
            response = self.client.sanitize_model_response(request=request)
            is_blocked = response.invocation_result != modelarmor_v1.SanitizeModelResponseResponse.InvocationResult.SUCCESS
            # In a real implementation, we would extract sanitized text from metadata if configured in the policy
            return {
                "is_blocked": is_blocked,
                "sanitized_text": text, 
                "invocation_result": response.invocation_result.name,
                "metadata": response.sanitization_metadata
            }
        except Exception as e:
            logger.error(f"Model Armor Response Sanitize Error: {e}")
            return {"is_blocked": False, "sanitized_text": text, "error": str(e)}
