"""
CareFlow Caller Agent Card (v1)
A2A Protocol discovery metadata definition.
"""
from a2a.types import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    AgentProvider
)
import os

# Service URL from environment (for Cloud Run deployment)
SERVICE_URL = os.environ.get("SERVICE_URL", "http://localhost:8080/")

caller_card = AgentCard(
    name="CareFlow Caller Agent",
    description=(
        "Voice interface for CareFlow Pulse. Handles phone calls with patients "
        "and relays information to the Healthcare Agent via A2A protocol."
    ),
    url=SERVICE_URL,
    provider=AgentProvider(
        organization="CareFlow Pulse",
        url="https://careflow-pulse.com",
    ),
    version="1.0.0",
    capabilities=AgentCapabilities(
        streaming=True,
        pushNotifications=False,
        stateTransitionHistory=True,
    ),
    securitySchemes=None,
    security=None,
    defaultInputModes=["text"],
    defaultOutputModes=["text", "task-status"],
    skills=[
        AgentSkill(
            id="voice_call_handling",
            name="Voice Call Handling",
            description=(
                "Handle voice calls with patients, conduct wellness interviews, "
                "and relay information to Healthcare Agent"
            ),
            tags=["voice", "healthcare", "patient-communication"],
            examples=[
                "Call patient about medication",
                "Follow up on patient symptoms",
                "Conduct wellness check",
                "follow-up calls"
            ],
            inputModes=["text"],
            outputModes=["text", "task-status"],
        )
    ],
    supportsAuthenticatedExtendedCard=False,
)
