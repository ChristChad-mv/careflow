import http from 'http';
import path from 'path';
import { fileURLToPath } from 'url';

import express, { Request, Response } from 'express';
import WebSocket, { WebSocketServer } from 'ws';

import {
  config,
  ConversationEvent,
  ConversationRelayTextToken,
  DTMFMessage,
  ErrorMessage,
  InterruptMessage,
  PromptMessage,
  SessionData,
  SetupMessage,
} from '../utils';
import { agent } from './agent';

// ES module equivalent of __dirname
// eslint-disable-next-line @typescript-eslint/naming-convention, no-underscore-dangle
const __filename = fileURLToPath(import.meta.url);
// eslint-disable-next-line @typescript-eslint/naming-convention, no-underscore-dangle
const __dirname = path.dirname(__filename);

/**
 * Handle interruption events by updating conversation history.
 */
function handleInterruption(
  interruptMessage: InterruptMessage,
  sessionData: SessionData,
): void {
  console.log('Handling interruption...');

  if (sessionData.currentResponse) {
    const { utteranceUntilInterrupt } = interruptMessage;
    const { currentResponse } = sessionData;

    let interruptPosition = currentResponse.length;
    if (utteranceUntilInterrupt && utteranceUntilInterrupt.trim()) {
      const position = currentResponse
        .toLowerCase()
        .indexOf(utteranceUntilInterrupt.toLowerCase());
      if (position !== -1) {
        interruptPosition = position + utteranceUntilInterrupt.length;
      }
    }

    const spokenPortion = currentResponse.substring(0, interruptPosition);

    if (spokenPortion.trim()) {
      sessionData.conversation.push({
        role: 'assistant',
        content: spokenPortion,
        timestamp: new Date().toISOString(),
        interrupted: true,
        interruptedAt: interruptPosition,
      });

      console.log(
        `Added interrupted response to conversation: "${spokenPortion}"`,
      );
      console.log(
        `Interrupted at position: ${interruptPosition} of ${currentResponse.length}`,
      );
    }

    sessionData.interruptedAt = interruptPosition;
  }
}

const app = express();
const server = http.createServer(app);

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));

app.use('/twiml', (req: Request, res: Response): void => {
  const host =
    config.ngrokUrl ||
    req.get('host') ||
    `localhost:${parseInt(config.port || '3000', 10)}`;

  const twiml = `
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <ConversationRelay url="wss://${host}/ws" welcomeGreeting="Hi there! Ask me about a movie or an actor!" ttsProvider="Amazon" voice="Matthew-Generative" />
    </Connect>
</Response>`.trim();

  res.type('text/xml');
  res.send(twiml);
});

const wss = new WebSocketServer({
  server,
  path: '/ws',
});

wss.on(
  'connection',
  async (ws: WebSocket, _req: http.IncomingMessage): Promise<void> => {
    console.log('New WebSocket connection established');

    // Store session data for this connection
    const sessionData: SessionData = {
      connectedAt: new Date().toISOString(),
      callSid: null,
      conversation: [],
      currentResponse: undefined,
      interruptedAt: undefined,
    };

    // agent.init();
    agent.setWsChannel(ws);

    ws.on('message', async (data: WebSocket.Data): Promise<void> => {
      try {
        const message: ConversationEvent = JSON.parse(data.toString());
        console.log('Received message:', message);

        // Handle different ConversationRelay message types
        switch (message.type) {
          case 'setup': {
            const setupMessage = message as SetupMessage;
            console.log('ConversationRelay setup');
            sessionData.callSid = setupMessage.callSid;
            console.log('Session ID:', setupMessage.sessionId);
            console.log('Call SID:', setupMessage.callSid);
            if (setupMessage.customParameters) {
              console.log('Custom parameters:', setupMessage.customParameters);
            }
            break;
          }

          case 'prompt': {
            const promptMessage = message as PromptMessage;
            console.log('User said:', promptMessage.voicePrompt);

            // Add user message to conversation history
            sessionData.conversation.push({
              role: 'user',
              content: promptMessage.voicePrompt,
              timestamp: new Date().toISOString(),
            });

            // Stream response from our LangGraph agent
            try {
              let isFirstChunk = true;
              let tokenIndex = 0;
              let accumulatedResponse = '';

              // Clear any previous response tracking
              sessionData.currentResponse = '';
              sessionData.interruptedAt = undefined;

              // eslint-disable-next-line no-restricted-syntax
              for await (const chunk of agent.streamMessage(
                promptMessage.voicePrompt,
                sessionData,
              )) {
                // Accumulate the response for tracking
                accumulatedResponse += chunk;
                sessionData.currentResponse = accumulatedResponse;

                // Send each chunk as a streaming text token
                const responseMessage: ConversationRelayTextToken = {
                  type: 'text',
                  token: chunk,
                  last: false,
                  interruptible: isFirstChunk,
                };

                ws.send(JSON.stringify(responseMessage));
                console.log(`Sent streaming chunk ${tokenIndex}:`, chunk);
                isFirstChunk = false;
                tokenIndex += 1;
              }

              // Send final empty token to indicate end of stream
              const finalMessage: ConversationRelayTextToken = {
                type: 'text',
                token: '',
                last: true, // This is the last chunk
              };

              ws.send(JSON.stringify(finalMessage));
              console.log('Sent final streaming token');

              // Add complete response to conversation history if not interrupted
              if (!sessionData.interruptedAt) {
                sessionData.conversation.push({
                  role: 'assistant',
                  content: accumulatedResponse,
                  timestamp: new Date().toISOString(),
                });
              }

              // Clear tracking
              sessionData.currentResponse = undefined;
            } catch (error) {
              throw new Error(
                error instanceof Error ? error.message : 'Unknown error',
              );
            }
            break;
          }

          case 'interrupt': {
            const interruptMessage = message as InterruptMessage;
            console.log(
              'User interrupted at:',
              interruptMessage.utteranceUntilInterrupt,
            );
            console.log(
              'Interrupt duration:',
              `${interruptMessage.durationUntilInterruptMs}ms`,
            );

            // Handle interruption for conversation tracking
            handleInterruption(interruptMessage, sessionData);
            break;
          }

          case 'dtmf': {
            const dtmfMessage = message as DTMFMessage;
            console.log('DTMF received:', dtmfMessage.digit);
            break;
          }

          case 'error': {
            const errorMessage = message as ErrorMessage;
            console.error('ConversationRelay error:', errorMessage.description);
            break;
          }

          default:
            console.log('Unknown message type:', message.type);
            console.log('Full message:', message);
        }
      } catch (error) {
        console.error('Error processing message:', error);
      }
    });

    ws.on('close', (code: number, reason: Buffer): void => {
      console.log(`WebSocket connection closed: ${code} ${reason.toString()}`);
    });

    ws.on('error', (error: Error): void => {
      console.error('WebSocket error:', error);
    });
  },
);

server.listen(config.port, (): void => {
  console.log(
    `🚀 Twilio ConversationRelay server running on port ${config.port}`,
  );

  const { ngrokUrl } = config;

  console.log(`📞 Local TwiML endpoint: http://localhost:${config.port}/twiml`);
  if (ngrokUrl) {
    console.log(`📞 Public TwiML endpoint: https://${ngrokUrl}/twiml`);
  }
  console.log(`🔌 WebSocket endpoint: ws://localhost:${config.port}/ws`);
  console.log('');

  if (ngrokUrl) {
    console.log('🔗 ngrok tunnel configured:');
    console.log(`   Public URL: https://${ngrokUrl}`);
    console.log(
      `   Configure your Twilio phone number webhook to: https://${ngrokUrl}/twiml`,
    );
  } else {
    console.log('🔗 To use with ngrok:');
    console.log(`1. Run: ngrok http ${config.port}`);
    console.log(
      '2. Configure your Twilio phone number webhook to: https://YOUR_NGROK_URL.ngrok.io/twiml',
    );
  }
  console.log('');
});
