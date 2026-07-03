"""Interactive user loop for the agent harness."""

from terminal_io import (
    print_system, prompt_user,
    display_tool_call, display_tool_result, display_error,
    display_agent_response,
)
from commands import COMMANDS
from skills_interceptor import intercept_message, InterceptorKind


def user_loop(agent: "Agent", ollama_client: "ollama.Client", on_exit=None) -> None:
    """Run the interactive chat loop.

    Args:
        agent: An initialized :class:`Agent` instance with its configuration.
        ollama_client: The Ollama client (kept for future use).
        on_exit: Optional callback invoked just before the loop breaks due to 
                 ``/exit`` or ``/quit``. Receives ``(agent, messages)``. Return
                 value is ignored — the callback can mutate whatever it needs.
    """
    print_system(
        f"🚀 Agent Ready — {agent._agent_type.name} ({agent._agent_type.model_name})",
        "Type a message to begin. Type /exit or /quit to stop."
    )

    while True:
        user_input = prompt_user()

        # Check for slash commands first.
        if user_input.startswith('/'):
            parts = user_input[1:].split(' ', 1)
            command_name = parts[0].lower()
            rest = parts[1] if len(parts) > 1 else ''

            handler = COMMANDS.get(command_name)
            if handler:
                result = handler(rest, agent=agent)
                if result is True and on_exit is not None:
                    # Let caller do its own exit-time work (e.g. summarize)
                    on_exit(agent, agent.messages)
                    break
                elif result is True:
                    break
                continue
            
            # No built-in handler — run the skill-activation interceptor.
            outcome = intercept_message(user_input)
            if outcome.kind == InterceptorKind.ACTIVATED:
                # Inject the skill context block into the next user message so
                # it is prepended to the user's request before being sent to the LLM.
                agent.inject_text(outcome.payload)
                effective_input = outcome.stripped_message if outcome.stripped_message else user_input
            elif outcome.kind == InterceptorKind.RESTRICTED:
                display_error(outcome.payload)
                effective_input = outcome.stripped_message if outcome.stripped_message else user_input
            else:
                # UNKNOWN or SKIP: treat as regular text and send to LLM.
                effective_input = user_input
        else:
            effective_input = user_input

        for output in agent.handle_prompt(effective_input):
            kind = output[0]
            if kind == "response":
                _, content, ollama_response = output
                display_agent_response(content, ollama_response, agent._context_length, None)
            elif kind == "tool_call":
                _, func_name, args_str = output
                display_tool_call(func_name, args_str)
            elif kind == "tool_result":
                _, func_name, result_type, content = output
                display_tool_result(func_name, result_type, content)
            else:  # ERROR
                _, description = output
                display_error(description)
