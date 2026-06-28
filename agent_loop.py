"""Main conversation loop — drives chat with Ollama and dispatches tool calls."""

import json
from terminal_io import print_box, c, CYAN, GREEN, BLUE, YELLOW, RED, MAGENTA, _format_speed
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

    print_box(
        f"🚀 Agent Ready — {model_name}",
        "Type a message to begin. Type 'exit' or 'quit' to stop.",
        MAGENTA, width=0
    )

    while True:
        user_input = input(c("\nYou> ", CYAN, bold=True))
        if user_input.strip().lower() in ['exit', 'quit']:
            print_box("Goodbye!", "See you next time.", MAGENTA, width=0)
            break

        messages.append({"role": "user", "content": user_input})

        # Show the prompt inside a fancy box.
        print_box(f"📝 Your Prompt ({len(user_input)} chars)", user_input, CYAN, width=0)

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
                print_box("🤖 Agent Response", content, GREEN, width=0)
                speed_info = _format_speed(response, context_length)
                if speed_info:
                    print(speed_info)
                break

            for tool_call in message['tool_calls']:
                func_name = tool_call['function']['name']
                args = tool_call['function']['arguments']

                # Format arguments as a readable block.
                try:
                    args_str = json.dumps(args, indent=2)
                except Exception:
                    args_str = str(args)

                print_box(f"🔧 {func_name}", args_str, BLUE, width=0, style="rounded")

                if func_name == 'execute_bash':
                    result = execute_bash(args.get('command', ''))
                elif func_name == 'write_file':
                    result = _write_file(args.get('filename', ''), args.get('content', ''))
                    print(f"   → {result}")
                elif func_name == 'read_file':
                    result = _read_file(args.get('filename', ''))
                else:
                    result = c(f"Error: Unknown function {func_name}", RED)

                # Show the tool result in its own box.
                print_box(f"✅ {func_name} Result", str(result), YELLOW, width=0, style="rounded")

                messages.append({
                    "role": "tool",
                    "content": result,
                    "name": func_name
                })
