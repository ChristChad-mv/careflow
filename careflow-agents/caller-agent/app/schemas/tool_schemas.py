"""
CareFlow Pulse - Tool Input Schemas

Pydantic models defining input schemas for LangChain tools.
Separated from tool implementations for better maintainability.

Author: CareFlow Pulse Team
Version: 1.0.0
"""

from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# TWILIO TOOL SCHEMAS
# =============================================================================

class CallPatientInput(BaseModel):
    """Input schema for the call_patient tool."""
    
    message: str = Field(
        description="The context/instructions for the call."
    )
    patient_name: str = Field(
        description="Name of the patient to call."
    )
    patient_id: str = Field(
        description="Unique identifier of the patient."
    )
    patient_phone: Optional[str] = Field(
        default=None,
        description="Patient's phone number (e.g., +1555123456). Required for outbound calls."
    )
    expect_reply: bool = Field(
        default=True,
        description="Whether to wait for patient reply. Set False for interstitial messages."
    )


# =============================================================================
# A2A TOOL SCHEMAS
# =============================================================================

class SendMessageInput(BaseModel):
    """Input schema for the send_message A2A tool."""
    
    server_url: str = Field(
        description="URL of the remote A2A server"
    )
    message: str = Field(
        description="Message content to send"
    )
    task_id: Optional[str] = Field(
        default=None,
        description="TaskId for continuing existing conversation"
    )


class SubscribeInput(BaseModel):
    """Input schema for the subscribe_to_task A2A tool."""
    
    server_url: str = Field(
        description="URL of the remote A2A server"
    )
    task_id: str = Field(
        description="Task ID to subscribe to"
    )


class WebhookInput(BaseModel):
    """Input schema for the register_webhook A2A tool."""
    
    server_url: str = Field(
        description="URL of the remote A2A server"
    )
    task_id: str = Field(
        description="Task ID"
    )
    webhook_url: str = Field(
        description="Webhook URL for notifications"
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'CallPatientInput',
    'SendMessageInput',
    'SubscribeInput',
    'WebhookInput',
]
