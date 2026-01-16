import base64
import logging
from typing import Dict, Any, Optional
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types as genai_types

logger = logging.getLogger(__name__)

def audio_handoff_callback(
    tool: BaseTool, 
    args: Dict[str, Any], 
    tool_context: ToolContext, 
    tool_response: Dict
) -> Optional[Dict]:
    """
    Multimodal Handoff: Converts base64 audio data from the fetch_call_audio tool 
    into a native Gemini audio part so the model can 'listen' directly to the recording.
    
    This callback follows the standard ADK 'after_tool_callback' signature.
    """
    if tool.name == "fetch_call_audio" and tool_response.get("success"):
        file_path = tool_response.get("local_file_path")
        if file_path:
            try:
                logger.info(f"📤 Uploading audio file '{file_path}' to Google File API...")
                
                # We need an API client. ADK context doesn't expose it easily, 
                # but we can instantiate a temporary one or rely on default credentials.
                from google.genai import Client
                client = Client(http_options={'api_version': 'v1alpha'}) # Alpha needed for some file ops, or beta
                
                # Upload the file
                # Note: 'file' argument is expected for local path in some SDK versions
                uploaded_file = client.files.upload(file=file_path)
                
                logger.info(f"✅ File uploaded: {uploaded_file.name} (URI: {uploaded_file.uri})")
                
                # Create a Part referencing the uploaded file URI
                file_part = genai_types.Part.from_uri(
                    file_uri=uploaded_file.uri,
                    mime_type="audio/mpeg"
                )
                
                # Inject into conversation history
                invocation = getattr(tool_context, 'invocation_context', None)
                if invocation and invocation.contents:
                    last_content = invocation.contents[-1]
                    last_content.parts.append(file_part)
                    logger.info(f"🎙️ Multimodal Handoff: Injected File URI reference for '{tool.name}' result.")

                # Cleanup: Remove the temporary file to keep /tmp clean
                import os
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"🧹 Temporary audio file deleted: {file_path}")
                    
            except Exception as e:
                logger.error(f"Failed to upload/inject audio file: {e}")
                # Try to clean up even on error
                import os
                if file_path and os.path.exists(file_path):
                    os.remove(file_path) 
                
    return None
