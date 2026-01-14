"""
CareFlow Pulse - Caller Agent Tools

This module exports all LangChain tools used by the Caller Agent.

Tools:
    - call_patient: Initiate phone calls via Twilio
    - A2A tools: Inter-agent communication tools
"""

import os

# Toggle between real Twilio tool and Console Mock tool
if os.environ.get("USE_CONSOLE_TOOL", "false").lower() == "true":
    from .console_call_tool import call_patient
    print("⚠️  Using CONSOLE_MOCK for call_patient tool")
else:
    from .twilio_tool import call_patient

from .a2a_tools import create_a2a_tools

__all__ = ['call_patient', 'create_a2a_tools']
