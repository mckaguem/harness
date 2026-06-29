"""Main conversation loop — drives chat with Ollama and dispatches tool calls."""

import json
from model_utils import tokenize_prompt
from terminal_io import (
    print_system, prompt_user,
    display_tool_call, display_tool_result, display_tool_success, display_error,
    display_agent_response,
)
from tools import execute_bash, write_file as _write_file, read_file as _read_file, edit_file, grep


def cmd_exit(rest: str) -> bool | None:
    """Handle the /exit command. Returns True to break the loop."""
    print_system("Goodbye!", "See you next time.")
    return True  # signal break


def cmd_quit(rest: str) -> bool | None:
    """Handle the /quit command. Returns True to break the loop."""
    print_system("Goodbye!", "See you next time.")
    return True  # signal break


COMMANDS = {
    'exit': cmd_exit,
    'quit': cmd_quit,
}


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

                if func_name == 'execute_bash':
                    result = execute_bash(args.get('command', ''))
                elif func_name == 'write_file':
                    result = _write_file(args.get('filename', ''), args.get('content', ''))
                    display_tool_success(func_name, result)
                elif func_name == 'read_file':
                    result = _read_file(args.get('filename', ''))
                elif func_name == 'edit_file':
                    result = edit_file(
                        args.get('filename', ''),
                        args.get('edits', [])
                    )
                    display_tool_success(func_name, result)
                elif func_name == 'grep':
                    result = grep(
                        pattern=args.get('pattern', ''),
                        path=args.get('path', ''),
                        use_regex=args.get('use_regex', False),
                        file_filter=args.get('file_filter'),
                        max_matches=args.get('max_matches', 50)
                    )
                else:
                    display_error(f"Unknown function {func_name}")
                    result = f"Error: Unknown function '{func_name}'."

                # Step 2: Print the tool result box AFTER execution returns.
                display_tool_result(func_name, result)
                messages.append({
                    "role": "tool",
                    "content": result,
                    "name": func_name
                })
