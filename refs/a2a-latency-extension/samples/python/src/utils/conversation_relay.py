from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass

@dataclass
class ConversationMessage:
    role: str
    content: str
    timestamp: str
    interrupted: bool = False
    interrupted_at: Optional[int] = None


@dataclass
class SessionData:
    connected_at: str
    call_sid: Optional[str]
    conversation: List[ConversationMessage]
    current_response: Optional[str] = None
    interrupted_at: Optional[int] = None


class ConversationRelayMessage:
    type: str

    def __init__(self, message_type: str, **kwargs: Dict[str, str]):
        self.type = message_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class ConversationRelayTextToken(ConversationRelayMessage):
    def __init__(self, token: str, last: bool = False,
                 interruptible: bool = False, preemptible: bool = False,
                 lang: Optional[str] = None):
        super().__init__('text')
        self.token = token
        self.last = last
        self.interruptible = interruptible
        self.preemptible = preemptible
        if lang:
            self.lang = lang

    def to_dict(self):
        result = {
            'type': self.type,
            'token': self.token,
            'last': self.last
        }
        if hasattr(self, 'interruptible'):
            result['interruptible'] = self.interruptible
        if hasattr(self, 'preemptible'):
            result['preemptible'] = self.preemptible
        if hasattr(self, 'lang'):
            result['lang'] = self.lang
        return result


class ConversationRelayPlayToken(ConversationRelayMessage):
    def __init__(self, source: str, loop: Optional[int] = None,
                 interruptible: bool = False, preemptible: bool = False,
                 lang: Optional[str] = None):
        super().__init__('play')
        self.source = source
        if loop is not None:
            self.loop = loop
        self.interruptible = interruptible
        self.preemptible = preemptible
        if lang:
            self.lang = lang

    def to_dict(self):
        result: Dict[str, Any] = {
            'type': self.type,
            'source': self.source
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


class SetupMessage(ConversationRelayMessage):
    def __init__(self, session_id: str, call_sid: str, from_num: str,
                 to_num: str, direction: str, custom_parameters: Optional[Dict[str, Any]] = None):
        super().__init__('setup')
        self.session_id = session_id
        self.call_sid = call_sid
        self.from_num = from_num
        self.to = to_num
        self.direction = direction
        self.custom_parameters = custom_parameters


class PromptMessage(ConversationRelayMessage):
    def __init__(self, voice_prompt: str, lang: str, last: bool):
        super().__init__('prompt')
        self.voice_prompt = voice_prompt
        self.lang = lang
        self.last = last


class DTMFMessage(ConversationRelayMessage):
    def __init__(self, digit: str):
        super().__init__('dtmf')
        self.digit = digit


class InterruptMessage(ConversationRelayMessage):
    def __init__(self, utterance_until_interrupt: str, duration_until_interrupt_ms: str):
        super().__init__('interrupt')
        self.utterance_until_interrupt = utterance_until_interrupt
        self.duration_until_interrupt_ms = duration_until_interrupt_ms


class ErrorMessage(ConversationRelayMessage):
    def __init__(self, description: str):
        super().__init__('error')
        self.description = description


ConversationEvent = Union[
    SetupMessage,
    PromptMessage,
    DTMFMessage,
    InterruptMessage,
    ErrorMessage,
    ConversationRelayMessage
]
