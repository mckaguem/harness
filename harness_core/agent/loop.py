"""Interactive user loop for the agent harness."""

import json
import time as _time
import traceback

from harness_core.agent.constants import RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
from harness_core.agent.core import Agent
from harness_core.terminal_io import prompt_user
from harness_core.tools.dispatcher import summarize
from harness_core.commands import COMMANDS
from harness_core.skills.interceptor import intercept_message, InterceptorKind
from harness_core.event_types import (SystemMessagePayload, ControlPayload, ToolErrorPayload, SessionErrorPayload, AgentResponsePayload, TurnStatsPayload, ToolCallPayload, ToolResultPayload)
from harness_core.session.context_compression import check_and_compress_if_needed

def _check_and_compress_if_needed(agent) -> None:
    """Check context utilization and trigger compression if above threshold."""
    try:
        session = getattr(agent, 'session', None) or getattr(agent, '_session', None)
        context_length = getattr(agent, 'context_length', 1 << 17)  # default ~131072

        if session is None or not context_length:
            return

        result = check_and_compress_if_needed(session, context_length, threshold=0.5, fraction=0.1)

        if result.get("compressed"):
            # Compression happened - emit turn stats event and system event with pre/post utilization
            agent.publish("agent.turn.stats", TurnStatsPayload(response=None, context_length=context_length, elapsed_seconds=0.0))
            agent.publish(
                "agent.session.autocompress",
                SystemMessagePayload(
                    title="Auto-Compression",
                    message=f"Context utilization was {result['pre_util']:.1%} of {context_length} max tokens. Auto-compressed to {result['post_util']:.1%}.",
                ),
            )
        elif result.get("error"):
            # Compression was attempted but failed
            agent.publish("agent.session.error", SessionErrorPayload(message=f"Auto-compression failed: {result['error']}"))
        # else: not compressed, no error - nothing to do
    except Exception:
        # silently skip on any error
        pass


def user_loop(agent: "Agent", on_exit=None) -> None:
    """Run the interactive chat loop.

    Args:
        agent: An initialized :class:`Agent` instance with its configuration.
        on_exit: Optional callback invoked just before the loop breaks due to 
                 ``/exit`` or ``/quit``. Receives ``(agent, messages)``. Return
                 value is ignored — the callback can mutate whatever it needs.
    """
    agent.publish(
        "agent.status.ready",
        SystemMessagePayload(
            title=f"🚀 Agent Ready — {agent._agent_type.name} ({agent._agent_type.model_name})",
            message="Type a message to begin. Type /exit or /quit to stop."
        )
    )

    while True:
        user_input = prompt_user()
        turn_start = _time.time()

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
                agent.inject_text(outcome.payload or "")
                effective_input = outcome.stripped_message if outcome.stripped_message else user_input
            elif outcome.kind == InterceptorKind.RESTRICTED:
                agent.publish("agent.tool.error", ToolErrorPayload(message=outcome.payload or ""))
                effective_input = outcome.stripped_message if outcome.stripped_message else user_input
            else:
                # UNKNOWN or SKIP: treat as regular text and send to LLM.
                effective_input = user_input
        else:
            effective_input = user_input

        # Emit a control event to show a spinner at the bottom of the messages
        # panel while the agent is actively working through its handle_prompt
        # loop (LLM calls, tool dispatches, etc.).
        agent.publish("agent.turn.start", ControlPayload(action={}))
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
                    _, content, ollama_response, _ = output
                    elapsed = _time.time() - turn_start
                    reasoning = (
                        (ollama_response or {}).get("reasoning")
                        if isinstance(ollama_response, dict) else None
                    )
                    agent.publish("agent.turn.response", AgentResponsePayload(content=content or "", response=ollama_response, context_length=agent.context_length, reasoning=reasoning))
                    agent.publish("agent.turn.stats", TurnStatsPayload(response=ollama_response, context_length=agent.context_length, elapsed_seconds=elapsed))
                elif kind == TOOL_CALL:
                    _, func_name, args_str, response_data = output
                    args_dict = json.loads(args_str)
                    summary = summarize(func_name, args_dict)
                    pre_content = (response_data or {}).get("pre_tool_content", "") or ""
                    reasoning = (response_data or {}).get("reasoning", "") or ""
                    agent.publish("agent.tool.call", ToolCallPayload(func_name=func_name, args_str=args_str, summary=summary, pre_content=pre_content or "", reasoning=reasoning))
                elif kind == TOOL_RESULT:
                    _, func_name, result, response_data = output
                    # Extract ToolResult fields for event payload.
                    result_title = getattr(result, "title", None)
                    result_display_text = getattr(result, "display_text", "") or ""
                    result_theme = getattr(result, "theme", "info") or "info"
                    result_type_tag = getattr(result, "type_tag", "text") or "text"
                    agent.publish(
                        "agent.tool.result",
                        ToolResultPayload(
                            func_name=func_name,
                            result_title=result_title,
                            result_display_text=result_display_text or "",
                            result_theme=result_theme or "info",
                            result_type_tag=result_type_tag or "text",
                        ),
                    )
                elif kind == ERROR:
                    _, description, _, _ = output
                    agent.publish("agent.tool.error", ToolErrorPayload(message=description or ""))
        except Exception as exc:  # pragma: no cover - defensive
            agent.publish("agent.tool.error", ToolErrorPayload(message=f"Agent turn failed: {exc}\n" + traceback.format_exc()))
        finally:
            # Emit a control event to hide the spinner at the bottom of the
            # messages panel.
            agent.publish("agent.turn.stop", ControlPayload(action={}))
        
        # Auto-compression check: after each agent response to a user message,
        # if context utilization exceeds 50%, trigger compression.
        if not (user_input.startswith('/') and effective_input == user_input):
            try:
                _check_and_compress_if_needed(agent)
            except Exception as e:
                agent.publish("agent.session.error", SessionErrorPayload(message=f"Auto-compression check failed: {e}"))
