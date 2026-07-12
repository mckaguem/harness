"""Interactive user loop for the agent harness."""

import time as _time
from rich.console import Console

from harness_core.agent.constants import RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
from harness_core.terminal_io import (
    print_system, prompt_user,
    display_tool_call, display_tool_result, display_error,
    display_agent_response, display_user_message, format_speed,
)
from harness_core.tools.dispatcher import summarize
import json
from harness_core.commands import COMMANDS
from harness_core.skills.interceptor import intercept_message, InterceptorKind


_console = Console()

def _count_approx_tokens(messages: list) -> int:
    """Approximate token count from a message list using character estimation.
    
    Uses ~4 chars per token as a rough approximation. This is much faster than
    calling the OpenAI tokenizer for every message loop iteration.
    """
    if not messages:
        return 0
    total_chars = sum(
        len(str(msg.get('content', '')) or '')
        for msg in messages
    )
    # Rough approximation: ~4 characters per token
    return total_chars // 4

def _check_and_compress_if_needed(agent, display_error) -> None:
    """Check context utilization and trigger compression if above threshold.
    
    Args:
        agent: The Agent instance with .messages and ._context_length attributes.
        display_error: Error display callback from harness_core.terminal_io.
    """
    try:
        messages = getattr(agent, 'messages', None) or (getattr(agent, '_session', None) and getattr(agent, '_session').messages)
        context_length = getattr(agent, '_context_length', 1 << 17)  # default ~131072
        
        if not messages or not context_length:
            return
        
        token_count = _count_approx_tokens(messages)
        utilization = token_count / context_length if context_length > 0 else 0
        
        THRESHOLD = 0.5  # Compress when above 50% utilization
        
        if utilization > THRESHOLD:
            print(f"⚠️ Context utilization at {utilization:.1%} — auto-compressing...")
            try:
                from harness_core.session.context_compression import compress_session
                session = getattr(agent, 'session', None) or getattr(agent, '_session', None)
                if session is not None:
                    compress_session(session, fraction=0.5)
                    print(f"✅ Auto-compressed: {len(messages)} → {len(session.messages)} messages")
            except Exception as e:
                display_error(f"Auto-compression failed: {e}")
    except Exception as e:
        pass  # silently skip on any error

def user_loop(agent: "Agent", on_exit=None) -> None:
    """Run the interactive chat loop.

    Args:
        agent: An initialized :class:`Agent` instance with its configuration.
        on_exit: Optional callback invoked just before the loop breaks due to 
                 ``/exit`` or ``/quit``. Receives ``(agent, messages)``. Return
                 value is ignored — the callback can mutate whatever it needs.
    """
    # Bind this agent as the current agent for the duration of the loop. This is
    # essential because the loop may run on a worker thread (e.g. the Textual
    # TUI launches it via ``run_worker(thread=True)``). ContextVars set on the
    # main thread in Agent.__init__ are NOT visible inside that worker thread,
    # so without re-binding here the agent-aware tools (task list, run_subagent)
    # would see CURRENT_AGENT as None and fail. Binding it on the loop's own
    # thread makes the agent available to every tool dispatch in this loop.
    from harness_core.agent.context import CURRENT_AGENT
    CURRENT_AGENT.set(agent)

    print_system(
        f"🚀 Agent Ready — {agent._agent_type.name} ({agent._agent_type.model_name})",
        "Type a message to begin. Type /exit or /quit to stop."
    )

    while True:
        user_input = prompt_user()

        # Echo the user's own message into the output pane so it appears
        # alongside the agent's response.  (The classic REPL renders the typed
        # text via prompt_toolkit; the TUI does not, so we echo it here.)
        if user_input.strip():
            display_user_message(user_input)

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
                    on_exit(agent, agent._session.messages)
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

        # Show a spinner at the bottom of the messages panel while the agent is
        # actively working through its handle_prompt loop (LLM calls, tool
        # dispatches, etc.).  show/hide are no-ops when no textual TUI is active,
        # so the classic REPL keeps its original behaviour.
        from harness_core.terminal_io.tui import get_tui
        _tui = get_tui()
        _tui.show_spinner()
        try:
            # Iterate defensively: agent.handle_prompt() is a generator, so the
            # provider/LLM call (and any tool dispatch) runs lazily as we pull
            # items. An exception raised while pulling the first item must be
            # caught *here* — otherwise it propagates out of user_loop, and in
            # the Textual TUI the worker's finally-block calls app.exit(),
            # closing the whole app after a single message. Surface it and keep
            # the loop alive so the user can retry (just like a tool ERROR).
            outputs = agent.handle_prompt(effective_input)
            for output in outputs:
                kind = output[0]
                if kind == RESPONSE:
                    _, content, ollama_response = output
                    display_agent_response(content, ollama_response, agent._context_length)
                elif kind == TOOL_CALL:
                    _, func_name, args_str, response_data = output
                    args_dict = json.loads(args_str)
                    summary = summarize(func_name, args_dict)
                    display_tool_call(func_name, args_str, summary)
                elif kind == TOOL_RESULT:
                    _, func_name, result, response_data = output
                    display_tool_result(func_name, result)
                    if response_data and 'usage' in response_data:
                        _console.print(format_speed(response_data, agent._context_length))
                elif kind == ERROR:
                    _, description = output
                    display_error(description)
                    # An ERROR means no matching tool result will follow for the
                    # most recent tool call, so reset the "pending tool call"
                    # tracking so a later result does not merge into the wrong
                    # panel.
                    from harness_core.terminal_io import display as _display
                    _display.reset_pending_tool_panel()
        except Exception as exc:  # pragma: no cover - defensive
            import traceback
            display_error(
                f"Agent turn failed: {exc}\n"
                + (traceback.format_exc() if _console.is_terminal else "")
            )
        finally:
            _tui.hide_spinner()
        
        # Auto-compression check: after each agent response to a user message,
        # if context utilization exceeds 50%, trigger compression.
        if effective_input != user_input or not user_input.startswith('/'):
            try:
                _check_and_compress_if_needed(agent, display_error)
            except Exception as e:
                pass  # silently skip auto-compression on any error
