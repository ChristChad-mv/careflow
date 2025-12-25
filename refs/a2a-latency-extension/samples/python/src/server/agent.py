from typing import List, Dict, Any, AsyncGenerator, Tuple, Optional, Union, Callable, Awaitable
from datetime import datetime
import asyncio
from asyncio import Task
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    AIMessage
)
from enum import Enum
from src.utils.llm import get_model
from src.server.tools import search_movies, search_people

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinalState(str, Enum):
    """
    Represents the possible states of a Task.
    """
    input_required = 'input-required'
    completed = 'completed'


# Create the system prompt template
SYSTEM_PROMPT = """You are a movie expert. Answer the user's question about movies and film industry personalities, using the searchMovies and searchPeople tools to find out more information as needed. Feel free to call them multiple times in parallel if necessary.

{goal_text}

The current date and time is: {current_time}

If the user asks you for specific information about a movie or person (such as the plot or a specific role an actor played), do a search for that movie/actor using the available functions before responding.

## Output Instructions

ALWAYS end your response with either "COMPLETED" or "AWAITING_USER_INPUT" on its own line. If you have answered the user's question, use COMPLETED. If you need more information to answer the question, use AWAITING_USER_INPUT.

Example:
Question: when was [some_movie] released?
Answer: [some_movie] was released on October 3, 1992.
COMPLETED"""

# Streaming update type
class StreamingUpdate:
    def __init__(self, update_type: str, content: str,
                 tool_name: Optional[str] = None,
                 tool_args: Optional[Dict[str, Any]] = None,
                 final_state: Optional[FinalState] = None):
        self.type = update_type
        self.content = content
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.final_state = final_state

async def _execute_tool(tool_name: str, tool_call_id: str, tool_func: Callable[[], Awaitable[str]]) -> ToolMessage:
    """Execute a tool and return a ToolMessage with the result."""
    try:
        result = await tool_func()
        return ToolMessage(
            content=result,
            tool_call_id=tool_call_id,
            name=tool_name
        )
    except Exception as error:
        logger.error(f'Failed to execute tool {tool_name}: {error}')
        return ToolMessage(
            content=f"Error executing {tool_name}: {str(error)}",
            tool_call_id=tool_call_id,
            name=tool_name
        )

async def run_movie_agent_streaming(
    user_message: str,
    goal: Optional[str] = None,
    message_history: List[BaseMessage] = []
) -> AsyncGenerator[StreamingUpdate, None]:
    """
    Run the movie agent with streaming updates

    Args:
        user_message: The message from the user
        goal: Optional goal for this conversation
        message_history: Previous conversation history

    Yields:
        StreamingUpdate objects with information about tool calls

    Returns:
        Tuple of (response text, final state)
    """

    goal_text = f"Your goal in this task is: {goal}" if goal else ""

    system_message = SystemMessage(
        content=SYSTEM_PROMPT.replace('{goal_text}', goal_text).replace(
            '{current_time}', datetime.now().isoformat()
        )
    )

    messages = [
        system_message,
        *message_history,
        HumanMessage(content=user_message)
    ]

    # Bind tools to the model
    model_with_tools = get_model().bind_tools(tools=[search_movies, search_people])

    # Run the agent with tool execution loop
    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        try:
            response = await model_with_tools.ainvoke(messages)
            messages.append(response)

            if isinstance(response, AIMessage) and hasattr(response, 'tool_calls') and response.tool_calls:
                # Yield update about tool calls being executed
                for tool in response.tool_calls:
                    yield StreamingUpdate(
                        update_type='tool_call',
                        content=f"Searching for information using {tool.get('name', '')}...",
                        tool_name=tool.get('name', ''),
                        tool_args=tool.get('args', {}),
                    )

                # Execute tools in parallel
                tool_results: List[ToolMessage] = []

                # Execute tools in parallel using gather
                tool_execution_tasks: List[Task[ToolMessage]] = []

                for tool in response.tool_calls:
                    try:
                        tool_name: str = tool.get('name') or ''
                        tool_args = tool.get('args') or {}
                        tool_id: str = tool.get('id') or ''

                        # Create a task for each tool execution
                        if tool_name == 'searchMovies':
                            async def search_movies_task() -> str:
                                return await search_movies.ainvoke({"query": tool_args.get('query', '')})
                            task = asyncio.create_task(_execute_tool(tool_name, tool_id, search_movies_task))
                        elif tool_name == 'searchPeople':
                            async def search_people_task() -> str:
                                return await search_people.ainvoke({"query": tool_args.get('query', '')})
                            task = asyncio.create_task(_execute_tool(tool_name, tool_id, search_people_task))
                        else:
                            # For unknown tools, create a simple completed task
                            async def unknown_tool():
                                return f"Unknown tool: {tool_name}"
                            task = asyncio.create_task(_execute_tool(tool_name, tool_id, unknown_tool))

                        tool_execution_tasks.append(task)
                    except Exception as error:
                        logger.error(f'Failed to setup tool execution: {error}')
                        tool_message = ToolMessage(
                            content=f"Error executing {tool.get('name', '')}: {str(error)}",
                            tool_call_id=tool.get('id', ''),
                            name=tool.get('name', '')
                        )
                        tool_results.append(tool_message)

                # Wait for all tool executions to complete in parallel
                if tool_execution_tasks:
                    completed_tools = await asyncio.gather(*tool_execution_tasks, return_exceptions=True)
                    for tool_message in completed_tools:
                        if isinstance(tool_message, Exception):
                            logger.error(f'Tool execution failed: {tool_message}')
                            continue
                        if isinstance(tool_message, ToolMessage):
                            tool_results.append(tool_message)

                messages.extend(tool_results)

                continue

            # No tool calls, this is the final response
            response_text: str = response.content
            lines = response_text.strip().split('\n')
            final_state_line = lines[-1].strip().upper() if lines else ""

            final_state = FinalState.completed
            cleaned_response = response_text

            if final_state_line in ["COMPLETED", "AWAITING_USER_INPUT"]:
                cleaned_response = '\n'.join(lines[:-1]).strip()
            if final_state_line == "AWAITING_USER_INPUT":
                final_state = FinalState.input_required

            final_response = cleaned_response or "Completed."
            yield StreamingUpdate(
                update_type='final_response',
                content=final_response,
                final_state=final_state
            )
            return

        except Exception as error:
            logger.error('Error in agent:', error)
            error_message = f"Agent error: {str(error)}"
            yield StreamingUpdate(
                update_type='final_response',
                content=error_message,
                final_state=FinalState.completed
            )
            return

    # If we reach here, we've hit the max iterations
    max_iterations_message = "Maximum iterations reached. Please try again."
    yield StreamingUpdate(
        update_type='final_response',
        content=max_iterations_message,
        final_state=FinalState.completed
    )


async def run_movie_agent(
    user_message: str,
    goal: Optional[str] = None,
    message_history: List[BaseMessage] = []
) -> Dict[str, str]:
    """
    Non-streaming wrapper for backward compatibility

    Args:
        user_message: The message from the user
        goal: Optional goal for this conversation
        message_history: Previous conversation history

    Returns:
        Dict with response text and final state
    """
    generator = run_movie_agent_streaming(user_message, goal, message_history)

    results: List[Union[StreamingUpdate, Tuple[str, str]]] = []
    final_update: Optional[Tuple[str, str]] = None

    async for update in generator:
        logger.info(f"[Tool Update] {update.content}")
        results.append(update)

    # When generator is done, final_update contains the return value
    if final_update:
        response, final_state = final_update
        return {
            "response": response,
            "finalState": final_state
        }
    else:
        return {
            "response": "Error: No response generated",
            "finalState": "COMPLETED"
        }
