"""
CareFlow Pulse - Conversation Relay Message Types

Data classes and message types for Twilio ConversationRelay WebSocket
communication. These types represent the messages exchanged between
Twilio and our voice server.

Reference: https://www.twilio.com/docs/voice/twiml/connect/conversationrelay

Author: CareFlow Pulse Team
Version: 1.0.0
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


# =============================================================================
# SESSION DATA
# =============================================================================

@dataclass
class ConversationMessage:
    """
    A single message in the conversation history.
    
    Attributes:
        role: Message author ('user', 'assistant', or 'system')
        content: Text content of the message
        timestamp: ISO format timestamp
        interrupted: Whether message was interrupted
        interrupted_at: Character position where interruption occurred
    """
    role: str
    content: str
    timestamp: str
    interrupted: bool = False
    interrupted_at: Optional[int] = None


@dataclass
class SessionData:
    """
    Session state for an active call.
    
    Attributes:
        connected_at: ISO timestamp when connection was established
        call_sid: Twilio Call SID
        conversation: List of messages in the conversation
        current_response: Response being streamed (for interruption handling)
        interrupted_at: Position where current response was interrupted
    """
    connected_at: str
    call_sid: Optional[str]
    conversation: List[ConversationMessage]
    current_response: Optional[str] = None
    interrupted_at: Optional[int] = None


# =============================================================================
# BASE MESSAGE CLASS
# =============================================================================

class ConversationRelayMessage:
    """
    Base class for all ConversationRelay messages.
    
    Attributes:
        type: Message type identifier
    """
    type: str
    
    def __init__(self, message_type: str, **kwargs: Dict[str, Any]):
        self.type = message_type
        for key, value in kwargs.items():
            setattr(self, key, value)


# =============================================================================
# OUTBOUND MESSAGES (Server -> Twilio)
# =============================================================================

class ConversationRelayTextToken(ConversationRelayMessage):
    """
    Text token to be spoken via TTS.
    
    Attributes:
        token: Text content to speak
        last: Whether this is the last token in the response
        interruptible: Whether user can interrupt this speech
        preemptible: Whether this can be preempted by new input
        lang: Language code (optional)
    """
    
    def __init__(
        self,
        token: str,
        last: bool = False,
        interruptible: bool = False,
        preemptible: bool = False,
        lang: Optional[str] = None
    ):
        super().__init__('text')
        self.token = token
        self.last = last
        self.interruptible = interruptible
        self.preemptible = preemptible
        if lang:
            self.lang = lang
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'type': self.type,
            'token': self.token,
            'last': self.last,
        }
        if hasattr(self, 'interruptible'):
            result['interruptible'] = self.interruptible
        if hasattr(self, 'preemptible'):
            result['preemptible'] = self.preemptible
        if hasattr(self, 'lang'):
            result['lang'] = self.lang
        return result


class ConversationRelayPlayToken(ConversationRelayMessage):
    """
    Audio playback command.
    
    Attributes:
        source: URL of audio file to play
        loop: Number of times to loop (optional)
        interruptible: Whether user can interrupt playback
        preemptible: Whether this can be preempted
        lang: Language code (optional)
    """
    
    def __init__(
        self,
        source: str,
        loop: Optional[int] = None,
        interruptible: bool = False,
        preemptible: bool = False,
        lang: Optional[str] = None
    ):
        super().__init__('play')
        self.source = source
        if loop is not None:
            self.loop = loop
        self.interruptible = interruptible
        self.preemptible = preemptible
        if lang:
            self.lang = lang
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: Dict[str, Any] = {
            'type': self.type,
            'source': self.source,
        }
        if hasattr(self, 'loop'):
            result['loop'] = self.loop
        if hasattr(self, 'interruptible'):
            result['interruptible'] = self.interruptible
        if hasattr(self, 'preemptible'):
            result['preemptible'] = self.preemptible
        if hasattr(self, 'lang'):
            result['lang'] = self.lang
        return result


# =============================================================================
# INBOUND MESSAGES (Twilio -> Server)
# =============================================================================

class SetupMessage(ConversationRelayMessage):
    """
    Initial setup message when connection is established.
    
    Attributes:
        session_id: Unique session identifier
        call_sid: Twilio Call SID
        from_num: Caller's phone number
        to: Called phone number
        direction: 'inbound' or 'outbound-api'
        custom_parameters: Additional parameters from TwiML
    """
    
    def __init__(
        self,
        session_id: str,
        call_sid: str,
        from_num: str,
        to_num: str,
        direction: str,
        custom_parameters: Optional[Dict[str, Any]] = None
    ):
        super().__init__('setup')
        self.session_id = session_id
        self.call_sid = call_sid
        self.from_num = from_num
        self.to = to_num
        self.direction = direction
        self.custom_parameters = custom_parameters


class PromptMessage(ConversationRelayMessage):
    """
    User speech transcription (STT result).
    
    Attributes:
        voice_prompt: Transcribed text from user speech
        lang: Detected language
        last: Whether this is the final transcription
    """
    
    def __init__(self, voice_prompt: str, lang: str, last: bool):
        super().__init__('prompt')
        self.voice_prompt = voice_prompt
        self.lang = lang
        self.last = last


class DTMFMessage(ConversationRelayMessage):
    """
    DTMF (keypad) input from user.
    
    Attributes:
        digit: The digit pressed (0-9, *, #)
    """
    
    def __init__(self, digit: str):
        super().__init__('dtmf')
        self.digit = digit


class InterruptMessage(ConversationRelayMessage):
    """
    User interrupted agent's speech.
    
    Attributes:
        utterance_until_interrupt: Text spoken before interruption
        duration_until_interrupt_ms: Duration in milliseconds
    """
    
    def __init__(
        self,
        utterance_until_interrupt: str,
        duration_until_interrupt_ms: str
    ):
        super().__init__('interrupt')
        self.utterance_until_interrupt = utterance_until_interrupt
        self.duration_until_interrupt_ms = duration_until_interrupt_ms


class ErrorMessage(ConversationRelayMessage):
    """
    Error notification from ConversationRelay.
    
    Attributes:
        description: Error description
    """
    
    def __init__(self, description: str):
        super().__init__('error')
        self.description = description


# =============================================================================
# TYPE ALIAS
# =============================================================================

ConversationEvent = Union[
    SetupMessage,
    PromptMessage,
    DTMFMessage,
    InterruptMessage,
    ErrorMessage,
    ConversationRelayMessage
]


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'ConversationMessage',
    'SessionData',
    'ConversationRelayMessage',
    'ConversationRelayTextToken',
    'ConversationRelayPlayToken',
    'SetupMessage',
    'PromptMessage',
    'DTMFMessage',
    'InterruptMessage',
    'ErrorMessage',
    'ConversationEvent',
]
