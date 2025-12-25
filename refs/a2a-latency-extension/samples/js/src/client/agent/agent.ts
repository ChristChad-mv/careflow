import { AgentCard } from '@a2a-js/sdk';
import {
  AIMessage,
  HumanMessage,
  SystemMessage,
} from '@langchain/core/messages';
import { tool } from '@langchain/core/tools';
import { MemorySaver } from '@langchain/langgraph';
import { createReactAgent } from '@langchain/langgraph/prebuilt';
import WebSocket from 'ws';
import { z } from 'zod';

import {
  BaseChatModel,
  config,
  ConversationRelayPlayToken,
  ConversationRelayTextToken,
  getModel,
  SessionData,
} from '../../utils';
import { formattedCards } from './formatters';

type SSEEventMessage = {
  text?: string;
  parts?: {
    kind: string;
    data?: {
      latency?: number;
    };
  }[];
};

type SSEEvent = {
  final: boolean;
  kind: string;
  text?: string;
  message?: SSEEventMessage;
  status: {
    message: SSEEventMessage;
  };
};

export default class Agent {
  agent: ReturnType<typeof createReactAgent>;

  systemMessage: SystemMessage;

  model: BaseChatModel;

  memory: MemorySaver;

  a2aServers: string[];

  agentCards: AgentCard[] = [];

  ws: WebSocket | null = null;

  sentInterstitialMessage: boolean = false;

  /**
   * Create a new Agent instance.
   * @param systemMessage The system message to initialize the agent with.
   * @param a2aServers Optional list of A2A servers for communication.
   */
  constructor({
    systemMessage,
    a2aServers,
  }: {
    systemMessage: string;
    a2aServers?: string[];
  }) {
    this.systemMessage = new SystemMessage(systemMessage || '');

    this.model = getModel({
      temperature: 0,
      streaming: true,
    });

    this.memory = new MemorySaver();

    this.a2aServers = a2aServers || [];

    this.agent = createReactAgent({
      llm: this.model,
      tools: [...this.getA2ATools()],
      checkpointer: this.memory,
    });
  }

  async init(): Promise<void> {
    await this.loadAgentCards();
  }

  /**
   * Load agent cards from all configured A2A servers.
   * This method fetches agent cards during initialization to avoid repeated requests.
   */
  private async loadAgentCards(): Promise<void> {
    console.log('Loading agent cards from A2A servers...');

    // Use Promise.all to handle servers in parallel instead of sequential loop
    const serverPromises = this.a2aServers.map(async (serverUrl) => {
      try {
        const agentCardUrl = new URL(
          '/.well-known/agent.json',
          serverUrl,
        ).toString();

        const response = await fetch(agentCardUrl, {
          method: 'GET',
          headers: {
            Accept: 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(
            `Failed to fetch agent card: ${response.status} ${response.statusText}`,
          );
        }

        const agentCard = (await response.json()) as AgentCard;
        console.log(
          `Fetched agent card from ${serverUrl}:`,
          agentCard.capabilities.extensions,
        );

        return agentCard;
      } catch (error) {
        console.error(`Error fetching agent card from ${serverUrl}:`, error);
        throw error;
      }
    });

    const results = await Promise.all(serverPromises);
    this.agentCards.push(...(results.filter(Boolean) as AgentCard[]));
    console.log(`Loaded ${this.agentCards.length} agent cards`);

    if (this.agentCards.length === 0) {
      throw new Error('No agent cards loaded');
    }

    console.log(this.a2aServers);
    const cards = formattedCards(this.agentCards);
    console.log('Available Remote Agents:\n', cards);
    this.systemMessage.content += `\n\nAvailable Remote Agents:\n${cards}`;
  }

  /**
   * Handle a conversation with the agent, streaming the response.
   * @param userMessage The user's message to the agent.
   * @param sessionData The session data containing conversation history.
   * @returns An async generator yielding response chunks.
   */
  async *streamMessage(
    userMessage: string,
    sessionData: SessionData,
  ): AsyncGenerator<string, void, unknown> {
    try {
      const sessionId = sessionData.callSid || 'default-session';
      const messages = this.getMessages(sessionData);
      messages.push(new HumanMessage(userMessage));

      const eventStream = this.agent.streamEvents(
        {
          messages: [
            ...(this.systemMessage ? [this.systemMessage] : []),
            ...messages,
          ],
        },
        {
          configurable: { thread_id: sessionId },
          version: 'v2',
          callbacks: [],
        },
      );

      let fullResponse = '';

      // eslint-disable-next-line no-restricted-syntax
      for await (const event of eventStream) {
        if (
          (event.event === 'on_chat_model_stream' ||
            event.event === 'on_llm_stream') &&
          event.data?.chunk?.content
        ) {
          const { content } = event.data.chunk;

          if (typeof content === 'string' && content.length > 0) {
            fullResponse += content;
            yield content;
          }
        }
      }

      console.log(
        `Agent streaming response for session ${sessionId}:`,
        fullResponse,
      );
    } catch (error) {
      console.error('Error in handleConversationWithAgentStream:', error);

      yield 'I apologize, but I encountered an error processing your request. Please try again.';
    }
  }

  getMessages(sessionData: SessionData): (HumanMessage | AIMessage)[] {
    const messages = sessionData.conversation.map((msg) => {
      if (msg.role === 'user') {
        return new HumanMessage(msg.content);
      }

      return new AIMessage(msg.content);
    });

    return messages;
  }

  getA2ATools() {
    return [
      tool(
        async (input: { serverUrl: string; task: string }) => {
          const { serverUrl, task } = input;

          if (!this.a2aServers.includes(serverUrl)) {
            return `Whoops! Looks like we don't have access to that server.`;
          }

          console.log(
            `calling send_remote_agent_task tool with server: ${serverUrl}, task: ${task}`,
          );

          try {
            // Generate a unique request ID for this RPC call
            const requestId = Date.now();

            // Generate a unique task ID
            const taskId = `task_${Date.now()}_${Math.random()
              .toString(36)
              .substr(2, 9)}`;

            // Prepare the JSON-RPC request for message/stream
            const rpcRequest = {
              jsonrpc: '2.0',
              method: 'message/stream',
              id: requestId,
              params: {
                message: {
                  messageId: taskId,
                  kind: 'message',
                  role: 'user',
                  parts: [
                    {
                      kind: 'text',
                      text: task,
                    },
                  ],
                },
              },
            };

            // Send the streaming request
            const response = await fetch(serverUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                Accept: 'text/event-stream, application/json', // Accept both SSE and JSON
              },
              body: JSON.stringify(rpcRequest),
            });

            if (!response.ok) {
              let errorBody = '';
              try {
                errorBody = await response.text();
                const errorJson = JSON.parse(errorBody);
                if (errorJson.error) {
                  throw new Error(
                    `A2A Server Error: ${errorJson.error.message} (Code: ${errorJson.error.code})`,
                  );
                }
              } catch (e: any) {
                if (e.message.startsWith('A2A Server Error')) throw e;
                throw new Error(
                  `HTTP error ${response.status}: ${
                    response.statusText
                  }. Response: ${errorBody || '(empty)'}`,
                );
              }
            }

            // Check content type and handle accordingly
            const contentType = response.headers.get('Content-Type');
            const isSSE = contentType?.startsWith('text/event-stream');
            const isJSON = contentType?.startsWith('application/json');

            if (!isSSE && !isJSON) {
              console.warn(
                `Unexpected Content-Type: ${contentType}. Attempting to process as JSON.`,
              );
            }

            let finalResult: string | null = null;

            if (isSSE) {
              // Handle SSE streaming response
              if (!response.body) {
                throw new Error('No response body received for SSE stream');
              }

              const reader = response.body
                .pipeThrough(new TextDecoderStream())
                .getReader();
              let buffer = '';
              let eventDataBuffer = '';

              try {
                let isDone = false;
                while (!isDone) {
                  // eslint-disable-next-line no-await-in-loop
                  const readerResult = await reader.read();
                  console.log('aloha reading', readerResult);
                  isDone = readerResult.done;

                  if (!isDone && readerResult.value) {
                    buffer += readerResult.value;
                    let lineEndIndex = buffer.indexOf('\n');
                    // Process all complete lines in the buffer
                    while (lineEndIndex >= 0) {
                      const line = buffer.substring(0, lineEndIndex).trim();
                      buffer = buffer.substring(lineEndIndex + 1);

                      if (line === '') {
                        // Empty line signifies end of an event
                        if (eventDataBuffer) {
                          const result = this.processSseEventData(
                            eventDataBuffer,
                            requestId,
                          );

                          console.log('SSE event:', result);

                          if (result && result.kind === 'status-update') {
                            if (
                              result.status?.message?.parts?.[0]?.kind ===
                                'data' &&
                              result.status.message.parts[0].data?.latency &&
                              config.supportsLatencyTaskUpdates &&
                              !this.sentInterstitialMessage
                            ) {
                              const { latency } =
                                result.status.message.parts[0].data;

                              console.log(
                                `Received latency update: ${latency}ms`,
                              );

                              if (latency > 3000) {
                                this.sendText(
                                  `Processing your request, this should take about ${Math.ceil(latency / 1000)} seconds...`,
                                );
                              } else if (latency > 1000) {
                                this.sendText(
                                  `Please hold for just a couple of seconds while I process your request..`,
                                );
                              }

                              this.sendPlay(
                                `https://${config.ngrokUrl}/keyboard-typing.mp3`,
                              );

                              this.sentInterstitialMessage = true;
                            }

                            if (result.final) {
                              finalResult = this.extractFinalMessage(result);
                              this.sentInterstitialMessage = false;
                              break; // Exit the streaming loop
                            }
                          }
                          eventDataBuffer = '';
                        }
                      } else if (line.startsWith('data:')) {
                        eventDataBuffer += `${line.substring(5).trimStart()}\n`;
                      } else if (line.startsWith(':')) {
                        // Comment line, ignore
                      }

                      lineEndIndex = buffer.indexOf('\n');
                    }

                    // If we have the final result, break out of the reading loop
                    if (finalResult !== null) {
                      break;
                    }
                  }
                }

                // Process any final buffered event data
                if (eventDataBuffer.trim()) {
                  const result = this.processSseEventData(
                    eventDataBuffer,
                    requestId,
                  );

                  if (
                    result &&
                    result.kind === 'status-update' &&
                    result.final
                  ) {
                    finalResult = this.extractFinalMessage(result);
                  }
                }
              } finally {
                reader.releaseLock();
              }
            } else {
              // Handle regular JSON response
              try {
                const jsonResponse = (await response.json()) as any;

                console.log(
                  'Received JSON response:',
                  JSON.stringify(jsonResponse, null, 2),
                );

                // Validate JSON-RPC response structure
                if (jsonResponse.jsonrpc !== '2.0') {
                  throw new Error('Invalid JSON-RPC response format');
                }

                // Check for JSON-RPC errors
                if (jsonResponse.error) {
                  throw new Error(
                    `A2A Server Error: ${jsonResponse.error.message} (Code: ${jsonResponse.error.code})`,
                  );
                }

                // Extract the result
                if (jsonResponse.result) {
                  console.log(
                    'Processing result:',
                    JSON.stringify(jsonResponse.result, null, 2),
                  );

                  // Try to extract message from various possible structures
                  if (jsonResponse.result.message?.text) {
                    finalResult = jsonResponse.result.message.text;
                  } else if (jsonResponse.result.message?.parts) {
                    finalResult = jsonResponse.result.message.parts
                      .filter((part: any) => part.kind === 'text')
                      .map((part: any) => part.text)
                      .join('');
                  } else if (jsonResponse.result.text) {
                    finalResult = jsonResponse.result.text;
                  } else if (typeof jsonResponse.result === 'string') {
                    finalResult = jsonResponse.result;
                  } else {
                    // Fallback: stringify the result
                    finalResult = JSON.stringify(jsonResponse.result);
                  }
                } else {
                  finalResult = 'Task completed but no result was returned.';
                }
              } catch (parseError) {
                console.error('Failed to parse JSON response:', parseError);
                throw new Error(
                  `Failed to parse server response: ${
                    parseError instanceof Error
                      ? parseError.message
                      : 'Unknown error'
                  }`,
                );
              }
            }

            // Return the final result
            if (finalResult !== null) {
              return `A2A task completed successfully. Response: ${finalResult}`;
            }
            return 'A2A task completed but no final message was received.';
          } catch (error) {
            console.error(
              `Error sending task to A2A server ${serverUrl}:`,
              error,
            );
            return `Failed to send task to A2A server at ${serverUrl}: ${
              error instanceof Error ? error.message : 'Unknown error'
            }`;
          }
        },
        {
          name: 'send_remote_agent_task',
          description:
            'Send a task to a specified remote agent for processing using SSE streaming. The tool waits for the complete response and only returns the final result. Requires serverUrl and task parameters.',
          schema: z.object({
            serverUrl: z
              .string()
              .describe(
                'The URL of the remote A2A server to send the task to.',
              ),
            task: z
              .string()
              .describe(
                'The task message to send to the remote agent. This should be a clear and concise description of the task.',
              ),
          }),
        },
      ),
    ];
  }

  setWsChannel(ws: WebSocket): void {
    this.ws = ws;
  }

  private send(
    message: ConversationRelayPlayToken | ConversationRelayTextToken,
  ) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket is not connected. Cannot send message.');
      return;
    }

    this.ws.send(JSON.stringify(message));
  }

  private sendText(message?: string) {
    if (!message) {
      console.warn('No message provided. Cannot send message.');
      return;
    }

    this.send({
      type: 'text',
      token: message,
      last: true,
      interruptible: false,
      preemptible: false,
    });
  }

  private sendPlay(source?: string) {
    if (!source) {
      console.warn('No source provided. Cannot send message.');
      return;
    }

    this.send({
      type: 'play',
      source,
      interruptible: false,
      preemptible: true,
    });
  }

  /**
   * Helper method to process SSE event data from A2A streaming responses.
   * @param data The JSON string from the SSE data field
   * @param originalRequestId The original request ID to validate against
   * @returns The parsed result object or null
   */
  private processSseEventData(
    data: string,
    originalRequestId: number,
  ): SSEEvent | null {
    if (!data.trim()) {
      console.warn('Attempted to process empty SSE event data');
      return null;
    }

    try {
      // Parse the JSON-RPC response from the SSE data
      const parsed = JSON.parse(data.replace(/\n$/, ''));

      // Validate basic JSON-RPC structure
      if (
        typeof parsed !== 'object' ||
        parsed === null ||
        parsed.jsonrpc !== '2.0'
      ) {
        console.warn('Invalid JSON-RPC response structure in SSE data');
        return null;
      }

      // Check for request ID mismatch (optional validation)
      if (parsed.id !== originalRequestId) {
        console.warn(
          `SSE Event's JSON-RPC response ID mismatch. Expected: ${originalRequestId}, got: ${parsed.id}`,
        );
      }

      // Check for errors in the response
      if (parsed.error) {
        const err = parsed.error;
        throw new Error(
          `SSE event contained an error: ${err.message} (Code: ${err.code})`,
        );
      }

      // Return the result if it exists
      if (parsed.result !== undefined) {
        return parsed.result;
      }

      console.warn('SSE event JSON-RPC response missing result field');
    } catch (error) {
      if (
        error instanceof Error &&
        error.message.startsWith('SSE event contained an error')
      ) {
        throw error; // Re-throw JSON-RPC errors
      }
      console.error('Failed to parse SSE event data:', data, error);
    }

    return null;
  }

  /**
   * Helper method to extract the final message from a TaskStatusUpdateEvent.
   * @param event The status update event
   * @returns The extracted message text or null
   */
  private extractFinalMessage(event: SSEEvent): string | null {
    try {
      // Handle different possible structures for the final message
      if (event && event.kind === 'status-update' && event.final) {
        // Try to extract message from various possible structures
        if (event.status?.message?.text) {
          return event.status.message.text;
        }
        if (event.status?.message?.parts) {
          return event.status.message.parts
            .filter((part: any) => part.kind === 'text')
            .map((part: any) => part.text)
            .join('');
        }
        if (event.message?.text) {
          return event.message.text;
        }
        if (event.message?.parts) {
          return event.message.parts
            .filter((part: any) => part.kind === 'text')
            .map((part: any) => part.text)
            .join('');
        }
        // Fallback: try to find any text content in the event
        if (event.text) {
          return event.text;
        }
      }
      return null;
    } catch (error) {
      console.error('Error extracting final message from event:', event, error);
      return null;
    }
  }
}
