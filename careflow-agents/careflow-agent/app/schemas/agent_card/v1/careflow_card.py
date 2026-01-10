"""
CareFlow Pulse Agent Card (v1)
A2A Protocol discovery metadata definition.
"""
from a2a.types import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    AgentProvider
)
from app.app_utils.config_loader import SERVICE_URL

def get_pulse_agent_card() -> AgentCard:
    """
    Returns the AgentCard metadata for the CareFlow Pulse Agent.
    """
    return AgentCard(
        name="CareFlow Pulse Agent",
        description="Post-hospitalization patient monitoring agent. Can access patient data and generate alerts.",
        url=SERVICE_URL,
        provider=AgentProvider(
            organization="CareFlow",
            url="https://careflow.example.com",
        ),
        version="1.0.0",
        capabilities=AgentCapabilities(
            streaming=True,
            pushNotifications=True,
            stateTransitionHistory=True,
        ),
        defaultInputModes=["text"],
        defaultOutputModes=["text", "task-status"],
        skills=[
            AgentSkill(
                id="patient_monitoring",
                name="Patient Monitoring",
                description="Check patient status, symptoms, and alerts.",
                tags=["health", "patient", "monitoring"],
                examples=[
                    "Check status of patient P001",
                    "Are there any critical alerts?",
                    "Analyze symptoms for Sarah Jones"
                ],
                inputModes=["text"],
                outputModes=["text", "task-status"],
            )
        ],
    )
