"""Main conversation loop — drives chat with Ollama and dispatches tool calls."""

import json

from model_utils import tokenize_prompt
from terminal_io import (
    print_system, prompt_user,
    display_tool_call, display_tool_result, display_tool_success, display_error,
    display_agent_response,
)
from commands import COMMANDS
from tools.dispatcher import dispatch


def run_loop(ollama_client, model_name: str, system_prompt: str,
             agent_tools: list, context_length: int) -> None:
    """Run the interactive chat loop.

    Args:
        ollama_client: An initialized Ollama client instance.
        model_name: The model identifier to use.
        system_prompt: System message prepended to every conversation.
        agent_tools: List of tool definitions (JSON-schema-like dicts).
        context_length: Model's context window size (0 if unknown).
    """
    messages = [{"role": "system", "content": system_prompt}]

    print_system(f"🚀 Agent Ready — {model_name}",
                 "Type a message to begin. Type /exit or /quit to stop.")

    while True:
        user_input = prompt_user()

        # Check for slash commands first.
        if user_input.startswith('/'):
            parts = user_input[1:].split(' ', 1)
            command_name = parts[0].lower()
            rest = parts[1] if len(parts) > 1 else ''

            handler = COMMANDS.get(command_name)
            if handler:
                result = handler(rest)
                if result is True:
                    break
                continue

        messages.append({"role": "user", "content": user_input})

        while True:
            response = ollama_client.chat(
                model=model_name,
                messages=messages,
                tools=agent_tools,
                options={
                    'num_ctx': context_length
                }
            )

            message = response['message']
            messages.append(message)

            print("Message length:", len(str(messages)), "Context length:", context_length)
            with open("session.txt", 'w') as thefile:
                thefile.write(str(messages))

            if not message.get('tool_calls'):
                content = message.get('content', '')
                prompt_token_count = tokenize_prompt(ollama_client, messages, model_name)
                display_agent_response(content, response, context_length, prompt_token_count)
                break

            for tool_call in message['tool_calls']:
                func_name = tool_call['function']['name']
                args = tool_call['function']['arguments']

                # Format arguments as a readable block.
                try:
                    args_str = json.dumps(args, indent=2)
                except Exception:
                    args_str = str(args)

                # Step 1: Print the tool call box BEFORE execution.
                display_tool_call(func_name, args_str)

                try:
                    result = dispatch(func_name, args)
                except KeyError:
                    display_error(f"Unknown function {func_name}")
                    result = f"Error: Unknown function '{func_name}'."

                # Step 2: Print the tool result box AFTER execution returns.
                display_tool_result(func_name, result)
                messages.append({
                    "role": "tool",
                    "content": result,
                    "name": func_name
                })
