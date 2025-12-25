import 'dotenv/config';

import {
  A2AExpressApp,
  AgentCard,
  AgentExecutor,
  AgentExtension,
  DefaultRequestHandler,
  ExecutionEventBus,
  InMemoryTaskStore,
  Message,
  RequestContext,
  Task,
  TaskState,
  TaskStatusUpdateEvent,
  TaskStore,
  TextPart,
} from '@a2a-js/sdk';
import { AIMessage, BaseMessage, HumanMessage } from '@langchain/core/messages';
import { AgentLatencyExtension } from '@twilio-labs/a2a-latency-extension';
import express from 'express';
import { v4 as uuidv4 } from 'uuid';

import { config } from '../utils';
import { runMovieAgentStreaming } from './agent.js';

// Simple store for contexts
const HISTORY_CONTEXT: Map<string, Message[]> = new Map();

/**
 * MovieAgentExecutor implements the agent's core logic.
 */
class MovieAgentExecutor implements AgentExecutor {
  private cancelledTasks = new Set<string>();

  public cancelTask = async (
    taskId: string,
    _eventBus: ExecutionEventBus,
  ): Promise<void> => {
    this.cancelledTasks.add(taskId);
    // The execute loop is responsible for publishing the final state
  };

  async execute(
    requestContext: RequestContext,
    eventBus: ExecutionEventBus,
  ): Promise<void> {
    const { userMessage } = requestContext;
    const existingTask = requestContext.task;

    // Determine IDs for the task and context
    const taskId = existingTask?.id || uuidv4();
    const contextId =
      userMessage.contextId || existingTask?.contextId || uuidv4();

    console.log(
      `[MovieAgentExecutor] Processing message ${userMessage.messageId} for task ${taskId} (context: ${contextId})`,
    );

    // 1. Publish initial Task event if it's a new task
    if (!existingTask) {
      const initialTask: Task = {
        kind: 'task',
        id: taskId,
        contextId,
        status: {
          state: 'submitted',
          timestamp: new Date().toISOString(),
        },
        history: [userMessage], // Start history with the current user message
        metadata: userMessage.metadata, // Carry over metadata from message if any
      };

      eventBus.publish(initialTask);
    }

    // 2. Publish "working" status update
    const workingStatusUpdate: TaskStatusUpdateEvent = {
      kind: 'status-update',
      taskId,
      contextId,
      status: {
        state: 'working',
        message: {
          kind: 'message',
          role: 'agent',
          messageId: uuidv4(),
          parts: [
            { kind: 'text', text: 'Processing your question, hang tight!' },
          ],
          taskId,
          contextId,
        },
        timestamp: new Date().toISOString(),
      },
      final: false,
    };

    eventBus.publish(workingStatusUpdate);

    // 3. Prepare messages for Langgraph agent
    const historyForAgent = HISTORY_CONTEXT.get(contextId) || [];
    if (!historyForAgent.find((m) => m.messageId === userMessage.messageId)) {
      historyForAgent.push(userMessage);
    }
    HISTORY_CONTEXT.set(contextId, historyForAgent);

    // Convert A2A messages to Langgraph format
    const messageHistory: BaseMessage[] = historyForAgent
      .slice(0, -1) // Exclude the current message as it will be added by runMovieAgent
      .map((m) => {
        const textContent = m.parts
          .filter(
            (p): p is TextPart => p.kind === 'text' && !!(p as TextPart).text,
          )
          .map((p) => (p as TextPart).text)
          .join('\n');

        return m.role === 'agent'
          ? new AIMessage(textContent)
          : new HumanMessage(textContent);
      })
      .filter((m) => m.content.length > 0);

    const currentMessageText = userMessage.parts
      .filter((p): p is TextPart => p.kind === 'text' && !!(p as TextPart).text)
      .map((p) => (p as TextPart).text)
      .join('\n');

    if (!currentMessageText.trim()) {
      console.warn(
        `[MovieAgentExecutor] No valid text message found for task ${taskId}.`,
      );

      const failureUpdate: TaskStatusUpdateEvent = {
        kind: 'status-update',
        taskId,
        contextId,
        status: {
          state: 'failed',
          message: {
            kind: 'message',
            role: 'agent',
            messageId: uuidv4(),
            parts: [{ kind: 'text', text: 'No message found to process.' }],
            taskId,
            contextId,
          },
          timestamp: new Date().toISOString(),
        },
        final: true,
      };

      eventBus.publish(failureUpdate);

      return;
    }

    const goal =
      (existingTask?.metadata?.goal as string | undefined) ||
      (userMessage.metadata?.goal as string | undefined);

    try {
      // 4. Run the Langgraph agent with streaming
      const agentGenerator = runMovieAgentStreaming(
        currentMessageText,
        goal,
        messageHistory,
      );

      let finalResponse;

      // Manually consume the generator to capture both streaming updates and final result
      try {
        let result = await agentGenerator.next();

        while (!result.done) {
          const update = result.value;

          // Check if the request has been cancelled
          if (this.cancelledTasks.has(taskId)) {
            console.log(
              `[MovieAgentExecutor] Request cancelled for task: ${taskId}`,
            );

            const cancelledUpdate: TaskStatusUpdateEvent = {
              kind: 'status-update',
              taskId,
              contextId,
              status: {
                state: 'canceled',
                timestamp: new Date().toISOString(),
              },
              final: true,
            };

            eventBus.publish(cancelledUpdate);

            return;
          }

          // Publish streaming update for tool calls
          if (
            update.type === 'tool_call' &&
            config.supportsLatencyTaskUpdates
          ) {
            const toolUpdateEvent: TaskStatusUpdateEvent = {
              kind: 'status-update',
              taskId,
              contextId,
              status: {
                state: 'working',
                message: {
                  kind: 'message',
                  role: 'agent',
                  messageId: uuidv4(),
                  parts: [
                    {
                      kind: 'data',
                      data: {
                        latency:
                          config.skillLatencies[update.toolName as string],
                      },
                    },
                  ],
                  taskId,
                  contextId,
                  metadata: {
                    toolName: update.toolName,
                  },
                },
                timestamp: new Date().toISOString(),
              },
              final: false,
            };

            eventBus.publish(toolUpdateEvent);
          }

          // eslint-disable-next-line no-await-in-loop
          result = await agentGenerator.next();
        }

        // When result.done is true, result.value contains the return value
        finalResponse = result.value;
      } catch (error) {
        console.error(
          '[MovieAgentExecutor] Error during agent execution:',
          error,
        );
        throw error;
      }

      // Ensure we have a valid response
      if (!finalResponse) {
        throw new Error('Agent generator did not return a valid response');
      }

      // Check if the request has been cancelled after completion
      if (this.cancelledTasks.has(taskId)) {
        console.log(
          `[MovieAgentExecutor] Request cancelled for task: ${taskId}`,
        );

        const cancelledUpdate: TaskStatusUpdateEvent = {
          kind: 'status-update',
          taskId,
          contextId,
          status: {
            state: 'canceled',
            timestamp: new Date().toISOString(),
          },
          final: true,
        };
        eventBus.publish(cancelledUpdate);
        return;
      }

      const responseText = finalResponse.response;
      const finalA2AState: TaskState =
        finalResponse.finalState === 'AWAITING_USER_INPUT'
          ? 'input-required'
          : 'completed';

      console.info(`[MovieAgentExecutor] Agent response: ${responseText}`);

      // 5. Publish final task status update
      const agentMessage: Message = {
        kind: 'message',
        role: 'agent',
        messageId: uuidv4(),
        parts: [{ kind: 'text', text: responseText || 'Completed.' }],
        taskId,
        contextId,
      };
      historyForAgent.push(agentMessage);
      HISTORY_CONTEXT.set(contextId, historyForAgent);

      const finalUpdate: TaskStatusUpdateEvent = {
        kind: 'status-update',
        taskId,
        contextId,
        status: {
          state: finalA2AState,
          message: agentMessage,
          timestamp: new Date().toISOString(),
        },
        final: true,
      };
      eventBus.publish(finalUpdate);

      console.log(
        `[MovieAgentExecutor] Task ${taskId} finished with state: ${finalA2AState}`,
      );
    } catch (error: any) {
      console.error(
        `[MovieAgentExecutor] Error processing task ${taskId}:`,
        error,
      );
      const errorUpdate: TaskStatusUpdateEvent = {
        kind: 'status-update',
        taskId,
        contextId,
        status: {
          state: 'failed',
          message: {
            kind: 'message',
            role: 'agent',
            messageId: uuidv4(),
            parts: [{ kind: 'text', text: `Agent error: ${error.message}` }],
            taskId,
            contextId,
          },
          timestamp: new Date().toISOString(),
        },
        final: true,
      };
      eventBus.publish(errorUpdate);
    }
  }
}

const movieAgentCard: AgentCard = {
  name: 'Movie Agent',
  description:
    'An agent that can answer questions about movies and actors using TMDB.',
  url: `http://localhost:${config.port}`,
  version: '0.0.2',
  capabilities: {
    streaming: true,
    pushNotifications: false,
    stateTransitionHistory: true,
  },
  defaultInputModes: ['text'],
  defaultOutputModes: ['text', 'task-status'],
  skills: [
    {
      id: 'general_movie_chat',
      name: 'General Movie Chat',
      description:
        'Answer general questions or chat about movies, actors, directors.',
      tags: ['movies', 'actors', 'directors'],
      examples: [
        'Tell me about the plot of Inception.',
        'Recommend a good sci-fi movie.',
        'Who directed The Matrix?',
        'What other movies has Scarlett Johansson been in?',
        'Find action movies starring Keanu Reeves',
        'Which came out first, Jurassic Park or Terminator 2?',
      ],
      inputModes: ['text'],
      outputModes: ['text', 'task-status'],
    },
  ],
  supportsAuthenticatedExtendedCard: false,
};

const extensions: AgentLatencyExtension[] = [];

if (config.supportsExtensions) {
  const extension: AgentLatencyExtension = {
    uri: 'https://github.com/twilio-labs/a2a-latency-extension',
    description:
      'This extension provides latency updates for tasks. The server will send DataPart messages with latency information for each tool call.',
    required: true,
    params: {
      skillLatency: config.skillLatencies,
    },
  };

  if (config.supportsLatencyTaskUpdates) {
    extension.params.supportsLatencyTaskUpdates = true;
  }

  extensions.push(extension);
}

if (extensions.length > 0) {
  movieAgentCard.capabilities.extensions = extensions;
}

async function main() {
  const taskStore: TaskStore = new InMemoryTaskStore();
  const agentExecutor: AgentExecutor = new MovieAgentExecutor();

  const requestHandler = new DefaultRequestHandler(
    movieAgentCard,
    taskStore,
    agentExecutor,
  );

  const appBuilder = new A2AExpressApp(requestHandler);
  const expressApp = appBuilder.setupRoutes(express() as any);
  expressApp.listen(config.port, () => {
    console.log(
      `[MovieAgent] Server using new framework started on http://localhost:${config.port}`,
    );
    console.log(
      `[MovieAgent] Agent Card: http://localhost:${config.port}/.well-known/agent.json`,
    );
    console.log('[MovieAgent] Press Ctrl+C to stop the server');
  });
}

main().catch(console.error);
