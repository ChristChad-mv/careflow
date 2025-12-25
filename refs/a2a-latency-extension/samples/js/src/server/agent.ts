import {
  BaseMessage,
  HumanMessage,
  SystemMessage,
  ToolMessage,
} from '@langchain/core/messages';

import { getModel } from '../utils';
import { searchMovies, searchPeople } from './tools.js';

// Create the system prompt template
const SYSTEM_PROMPT = `You are a movie expert. Answer the user's question about movies and film industry personalities, using the searchMovies and searchPeople tools to find out more information as needed. Feel free to call them multiple times in parallel if necessary.

{goal_text}

The current date and time is: {current_time}

If the user asks you for specific information about a movie or person (such as the plot or a specific role an actor played), do a search for that movie/actor using the available functions before responding.

## Output Instructions

ALWAYS end your response with either "COMPLETED" or "AWAITING_USER_INPUT" on its own line. If you have answered the user's question, use COMPLETED. If you need more information to answer the question, use AWAITING_USER_INPUT.

Example:
Question: when was [some_movie] released?
Answer: [some_movie] was released on October 3, 1992.
COMPLETED`;

// Streaming update type
export interface StreamingUpdate {
  type: 'tool_call' | 'final_response';
  content: string;
  toolName?: string;
  toolArgs?: any;
}

// Helper function to run the agent with tool execution (streaming version)
export async function* runMovieAgentStreaming(
  userMessage: string,
  goal?: string,
  messageHistory: BaseMessage[] = [],
): AsyncGenerator<
  StreamingUpdate,
  {
    response: string;
    finalState: 'COMPLETED' | 'AWAITING_USER_INPUT';
  },
  unknown
> {
  const goalText = goal ? `Your goal in this task is: ${goal}` : '';

  const systemMessage = new SystemMessage(
    SYSTEM_PROMPT.replace('{goal_text}', goalText).replace(
      '{current_time}',
      new Date().toISOString(),
    ),
  );

  const messages: BaseMessage[] = [
    systemMessage,
    ...messageHistory,
    new HumanMessage(userMessage),
  ];

  // Bind tools to the model
  const modelWithTools = getModel().bindTools([searchMovies, searchPeople]);

  // Run the agent with tool execution loop
  const maxIterations = 5;
  let iteration = 0;

  while (iteration < maxIterations) {
    iteration += 1;

    try {
      // eslint-disable-next-line no-await-in-loop
      const response = await modelWithTools.invoke(messages);

      // Add the AI response to messages
      messages.push(response);

      // Check if there are tool calls to execute
      if (response.tool_calls && response.tool_calls.length > 0) {
        // Yield update about tool calls being executed
        // eslint-disable-next-line no-restricted-syntax
        for (const toolCall of response.tool_calls) {
          yield {
            type: 'tool_call',
            content: `Searching for information using ${toolCall.name}...`,
            toolName: toolCall.name,
            toolArgs: toolCall.args,
          };
        }

        // Execute tools in parallel
        const toolPromises = response.tool_calls.map(async (toolCall) => {
          let result: string;

          try {
            if (toolCall.name === 'searchMovies') {
              const toolResult = await searchMovies.invoke({
                query: toolCall.args.query,
              });
              result =
                typeof toolResult === 'string'
                  ? toolResult
                  : JSON.stringify(toolResult);
            } else if (toolCall.name === 'searchPeople') {
              const toolResult = await searchPeople.invoke({
                query: toolCall.args.query,
              });
              result =
                typeof toolResult === 'string'
                  ? toolResult
                  : JSON.stringify(toolResult);
            } else {
              result = `Unknown tool: ${toolCall.name}`;
            }
          } catch (error) {
            result = `Error executing ${toolCall.name}: ${
              (error as Error).message
            }`;
          }

          return new ToolMessage({
            tool_call_id: toolCall.id!,
            content: result,
            name: toolCall.name,
          });
        });

        // eslint-disable-next-line no-await-in-loop
        const toolMessages = await Promise.all(toolPromises);

        // Add tool results to messages
        messages.push(...toolMessages);

        // Continue the loop to get the final response
        // eslint-disable-next-line no-continue
        continue;
      }

      // No tool calls, this is the final response
      const responseText = response.content as string;
      const lines = responseText.trim().split('\n');
      const finalStateLine = lines.at(-1)?.trim().toUpperCase();

      let finalState: 'COMPLETED' | 'AWAITING_USER_INPUT' = 'COMPLETED';
      let cleanedResponse = responseText;

      if (
        finalStateLine === 'COMPLETED' ||
        finalStateLine === 'AWAITING_USER_INPUT'
      ) {
        finalState = finalStateLine as 'COMPLETED' | 'AWAITING_USER_INPUT';
        // Remove the final state line from the response
        cleanedResponse = lines.slice(0, -1).join('\n').trim();
      }

      return {
        response: cleanedResponse || 'Completed.',
        finalState,
      };
    } catch (error) {
      console.error('Error in agent:', error);
      return {
        response: `Agent error: ${(error as Error).message}`,
        finalState: 'COMPLETED',
      };
    }
  }

  // If we reach here, we've hit the max iterations
  return {
    response: 'Maximum iterations reached. Please try again.',
    finalState: 'COMPLETED',
  };
}

// Non-streaming wrapper for backward compatibility
export async function runMovieAgent(
  userMessage: string,
  goal?: string,
  messageHistory: BaseMessage[] = [],
): Promise<{
  response: string;
  finalState: 'COMPLETED' | 'AWAITING_USER_INPUT';
}> {
  const generator = runMovieAgentStreaming(userMessage, goal, messageHistory);

  // Manually consume the generator to capture both streaming updates and final result
  const results = [];
  // eslint-disable-next-line no-await-in-loop
  let result = await generator.next();

  while (!result.done) {
    const update = result.value;
    // We can log updates here if needed for debugging
    console.log(`[Tool Update] ${update.content}`);
    results.push(update);
    // eslint-disable-next-line no-await-in-loop
    result = await generator.next();
  }

  // When result.done is true, result.value contains the return value
  return result.value;
}
