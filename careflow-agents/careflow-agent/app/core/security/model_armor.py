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
    
    This client provides two layers of protection:
    1. Input scanning: Detects prompt injection, jailbreak attempts, and adversarial inputs
    2. Output sanitization: Redacts PII/PHI and filters harmful content
    
    Template Configuration:
    - Uses MODEL_ARMOR_TEMPLATE from environment (e.g., projects/.../locations/us/templates/careflow-hipaa-prod)
    - Automatically handles regional endpoints (e.g., modelarmor.us.rep.googleapis.com)
    """
    def __init__(self, template_path: Optional[str] = None):
        """
        Initialize Model Armor client with template.
        
        Args:
            template_path: Full template path (e.g., projects/X/locations/us/templates/Y)
                          If None, reads from MODEL_ARMOR_TEMPLATE env var
        """
        # Get template path from env or parameter
        self.template_name = template_path or os.environ.get("MODEL_ARMOR_TEMPLATE")
        
        if not self.template_name:
            # Fallback: construct from individual components
            self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
            location = os.environ.get("MODEL_ARMOR_LOCATION", "us")
            policy_id = os.environ.get("MODEL_ARMOR_POLICY_ID", "default")
            
            if self.project_id:
                self.template_name = f"projects/{self.project_id}/locations/{location}/templates/{policy_id}"
                logger.warning(f"MODEL_ARMOR_TEMPLATE not set. Using fallback: {self.template_name}")
            else:
                logger.error("Neither MODEL_ARMOR_TEMPLATE nor GOOGLE_CLOUD_PROJECT is set")
                self.template_name = None
        
        # Initialize client
        if modelarmor_v1 and self.template_name:
            try:
                # Construct regional endpoint (e.g., modelarmor.us.rep.googleapis.com)
                # This is critical for discovering templates in specific regions
                location = os.environ.get("MODEL_ARMOR_LOCATION", "us")
                endpoint = f"modelarmor.{location}.rep.googleapis.com" if location != "global" else "modelarmor.googleapis.com"
                
                client_options = {"api_endpoint": endpoint}
                self.client = modelarmor_v1.ModelArmorClient(client_options=client_options)
                logger.info(f"✅ ModelArmorClient initialized with template: {self.template_name} (Endpoint: {endpoint})")
            except Exception as e:
                logger.error(f"Failed to initialize ModelArmorClient: {e}")
                self.client = None
        else:
            self.client = None
            if not modelarmor_v1:
                logger.error("google-cloud-modelarmor package not found. Install with: pip install google-cloud-modelarmor")
            else:
                logger.error("Model Armor template not configured")

    async def scan_prompt(self, text: str) -> Dict[str, Any]:
        """
        Scan user prompt for prompt injection, jailbreak attempts, and adversarial inputs.
        
        This is the INPUT PROTECTION layer.
        
        Returns:
            Dict with:
                - is_blocked (bool): Whether the prompt was blocked
                - invocation_result (str): Result status from Model Armor
                - error (str): Error message if scan failed
        """
        if not self.client or not self.template_name:
            logger.error("Model Armor client not available - Fail-Closed: Blocking prompt")
            return {"is_blocked": True, "error": "Model Armor client not initialized"}
        
        try:
            # Create DataItem with text field
            data_item = modelarmor_v1.DataItem(text=text)
            
            request = modelarmor_v1.SanitizeUserPromptRequest(
                name=self.template_name,
                user_prompt_data=data_item
            )
            
            response = self.client.sanitize_user_prompt(request=request)
            sanitization_result = response.sanitization_result
            
            # Check for API success
            if sanitization_result.invocation_result != modelarmor_v1.InvocationResult.SUCCESS:
                logger.error(f"Model Armor API error (Code: {sanitization_result.invocation_result}) - Fail-Closed: Blocking prompt")
                return {"is_blocked": True, "error": f"API Error: {sanitization_result.invocation_result}"}

            # Check if any filter matched (MATCH_FOUND = 2)
            is_blocked = sanitization_result.filter_match_state == modelarmor_v1.FilterMatchState.MATCH_FOUND
            
            result = {
                "is_blocked": is_blocked,
                "invocation_result": sanitization_result.invocation_result.name,
            }
            
            if is_blocked:
                logger.warning(f"🚨 Model Armor BLOCKED prompt")
            else:
                logger.debug(f"✅ Model Armor prompt scan passed")
            
            return result
            
        except Exception as e:
            logger.error(f"Model Armor Prompt Scan Error: {e} - Fail-Closed: Blocking prompt", exc_info=True)
            return {"is_blocked": True, "error": str(e)}

    async def sanitize_response(self, text: str) -> Dict[str, Any]:
        """
        Sanitize model response for PII/PHI and harmful content.
        
        This is the OUTPUT PROTECTION layer.
        
        Returns:
            Dict with:
                - is_blocked (bool): Whether the response was completely blocked
                - sanitized_text (str): Text with PII/PHI redacted
                - invocation_result (str): Result status
                - redactions_applied (list): List of filter names that matched
        """
        if not self.client or not self.template_name:
            logger.error("Model Armor client not available - Fail-Closed: Blocking response")
            return {"is_blocked": True, "sanitized_text": "[REDACTED]", "error": "Model Armor client not initialized"}
        
        try:
            # Create DataItem with text field
            data_item = modelarmor_v1.DataItem(text=text)
            
            request = modelarmor_v1.SanitizeModelResponseRequest(
                name=self.template_name,
                model_response_data=data_item
            )
            
            response = self.client.sanitize_model_response(request=request)
            sanitization_result = response.sanitization_result
            
            # Check for API success
            if sanitization_result.invocation_result != modelarmor_v1.InvocationResult.SUCCESS:
                logger.error(f"Model Armor API error - Fail-Closed: Blocking response")
                return {"is_blocked": True, "sanitized_text": "[REDACTED]", "error": f"API Error: {sanitization_result.invocation_result}"}

            # Check for matches
            is_blocked = sanitization_result.filter_match_state == modelarmor_v1.FilterMatchState.MATCH_FOUND
            
            sanitized_text = text
            redactions_applied = []
            
            # Extract redacted text if available
            if hasattr(response, 'model_response_data') and response.model_response_data:
                if response.model_response_data.text:
                    sanitized_text = response.model_response_data.text
            
            # Extract matching filters
            if is_blocked and hasattr(sanitization_result, 'filter_results'):
                for filter_name, filter_res in sanitization_result.filter_results.items():
                    # Check individual match state if we want more detail
                    redactions_applied.append(filter_name)
            
            result = {
                "is_blocked": is_blocked,
                "sanitized_text": sanitized_text,
                "invocation_result": sanitization_result.invocation_result.name,
                "redactions_applied": redactions_applied,
            }
            
            if is_blocked:
                logger.warning(f"🚨 Model Armor BLOCKED response entirely")
            elif redactions_applied:
                logger.info(f"🔒 Model Armor redacted: {', '.join(redactions_applied)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Model Armor Response Sanitize Error: {e} - Fail-Closed: Blocking response", exc_info=True)
            return {"is_blocked": True, "sanitized_text": "[REDACTED]", "error": str(e)}
