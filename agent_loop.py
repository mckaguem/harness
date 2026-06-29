"""Main conversation loop — drives chat with Ollama and dispatches tool calls."""

import json
from terminal_io import (
    print_system, prompt_user, display_user_prompt,
    display_tool_call, display_tool_result,
    display_agent_response, display_tool_success, display_error,
)
from tools import execute_bash, write_file as _write_file, read_file as _read_file


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
                 "Type a message to begin. Type 'exit' or 'quit' to stop.")

    while True:
        user_input = prompt_user()
        if user_input.strip().lower() in ['exit', 'quit']:
            print_system("Goodbye!", "See you next time.")
            break

        messages.append({"role": "user", "content": user_input})
        display_user_prompt(user_input)

        while True:
            response = ollama_client.chat(
                model=model_name,
                messages=messages,
                tools=agent_tools
            )

            message = response['message']
            messages.append(message)

            if not message.get('tool_calls'):
                content = message.get('content', '')
                display_agent_response(content, response, context_length)
                break

            for tool_call in message['tool_calls']:
                func_name = tool_call['function']['name']
                args = tool_call['function']['arguments']

                # Format arguments as a readable block.
                try:
                    args_str = json.dumps(args, indent=2)
                except Exception:
                    args_str = str(args)

                display_tool_call(func_name, args_str)

                if func_name == 'execute_bash':
                    result = execute_bash(args.get('command', ''))
                elif func_name == 'write_file':
                    result = _write_file(args.get('filename', ''), args.get('content', ''))
                    display_tool_success(func_name, result)
                elif func_name == 'read_file':
                    result = _read_file(args.get('filename', ''))
                else:
                    display_error(f"Unknown function {func_name}")
                    continue

                # Truncation happens inside the helper; full result still goes to agent.
                messages.append({
                    "role": "tool",
                    "content": result,
                    "name": func_name
                })
                display_tool_result(func_name, result)
