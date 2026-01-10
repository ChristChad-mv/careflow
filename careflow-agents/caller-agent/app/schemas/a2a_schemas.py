"""
CareFlow Pulse - A2A Communication Schemas

Pydantic models for A2A protocol communication.

Author: CareFlow Pulse Team
Version: 1.0.0
"""

from pydantic import BaseModel, Field


class SubscribeInput(BaseModel):
    """Input schema for subscribing to A2A task updates."""
    
    server_url: str = Field(
        description="URL of the remote A2A server"
    )
    task_id: str = Field(
        description="Task ID to subscribe to"
    )


class WebhookInput(BaseModel):
    """Input schema for registering A2A webhooks."""
    
    server_url: str = Field(
        description="URL of the remote A2A server"
    )
    task_id: str = Field(
        description="Task ID"
    )
    webhook_url: str = Field(
        description="Webhook URL for notifications"
    )
