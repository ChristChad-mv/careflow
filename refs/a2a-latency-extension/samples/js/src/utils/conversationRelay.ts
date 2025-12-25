export interface SessionData {
  connectedAt: string;
  callSid: string | null;
  conversation: ConversationMessage[];
  currentResponse?: string;
  interruptedAt?: number;
}

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  interrupted?: boolean;
  interruptedAt?: number;
}

export interface ConversationRelayMessage {
  type: string;
  [key: string]: any;
}

export interface ConversationRelayTextToken {
  type: 'text';
  token: string;
  last?: boolean;
  interruptible?: boolean;
  preemptible?: boolean;
  lang?: string;
}

export interface ConversationRelayPlayToken {
  type: 'play';
  source: string;
  loop?: number;
  interruptible?: boolean;
  preemptible?: boolean;
  lang?: string;
}

export interface SetupMessage extends ConversationRelayMessage {
  type: 'setup';
  sessionId: string;
  callSid: string;
  from: string;
  to: string;
  direction: string;
  customParameters?: { [key: string]: any };
}

export interface PromptMessage extends ConversationRelayMessage {
  type: 'prompt';
  voicePrompt: string;
  lang: string;
  last: boolean;
}

export interface DTMFMessage extends ConversationRelayMessage {
  type: 'dtmf';
  digit: string;
}

export interface InterruptMessage extends ConversationRelayMessage {
  type: 'interrupt';
  utteranceUntilInterrupt: string;
  durationUntilInterruptMs: string;
}

export interface ErrorMessage extends ConversationRelayMessage {
  type: 'error';
  description: string;
}

export type ConversationEvent =
  | SetupMessage
  | PromptMessage
  | DTMFMessage
  | InterruptMessage
  | ErrorMessage
  | ConversationRelayMessage;
