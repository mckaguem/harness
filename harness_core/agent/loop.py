"""Interactive user loop for the agent harness."""
import time as _time
import traceback

from harness_core.agent.constants import RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
from harness_core.agent.core import Agent
from harness_core.terminal_io import prompt_user
from harness_core.tools.dispatcher import summarize
import json
from harness_core.commands import COMMANDS
from harness_core.skills.interceptor import intercept_message, InterceptorKind
from harness_core.eventbus import Event, event_bus
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
            _emit_turn_stats_event(agent, None, context_length, 0.0)
            _emit_system_event(
                agent,
                "agent.session.autocompress",
                "Auto-Compression",
                f"Context utilization was {result['pre_util']:.1%} of {context_length} max tokens. Auto-compressed to {result['post_util']:.1%}.",
            )
        elif result.get("error"):
            # Compression was attempted but failed
            _emit_session_error_event(agent, f"Auto-compression failed: {result['error']}")
        # else: not compressed, no error - nothing to do
    except Exception:
        # silently skip on any error
        pass

def _emit_system_event(agent, topic: str, title: str, message: str) -> None:
    """Emit a system-notification event.

    The event is published on the event bus. The TUI's
    :class:`~harness_core.terminal_io.event_listener.HarnessEventListener`
    subscribes to these events to render system messages in the TUI output pane.
    """

    from harness_core.event_types import SystemMessagePayload

    event = Event(
        topic=topic,
        sender=agent.id,
        payload=SystemMessagePayload(title=title, message=message),
    )
    event_bus.publish(event)


def _emit_control_event(agent, topic: str, payload: dict | None = None) -> None:
    """Emit a control event (e.g. spinner start/stop, agent turn start/stop).

    These events are published on the event bus. The TUI's
    :class:`~harness_core.terminal_io.event_listener.HarnessEventListener`
    subscribes to them to show/hide spinners in the messages panel.
    """

    from harness_core.event_types import ControlPayload

    event = Event(
        topic=topic,
        sender=agent.id,
        payload=ControlPayload(action=payload or {}),
    )
    event_bus.publish(event)



def _emit_tool_error_event(agent, description: str) -> None:
    """Emit an 'agent.tool.error' event for tool-call errors.

    Handles both high-level agent turn failures and handle_prompt ERROR outputs.
    The TUI listener handles display + panel reset on receipt.
    """
    from harness_core.event_types import ToolErrorPayload

    event = Event(
        topic="agent.tool.error",
        sender=agent.id,
        payload=ToolErrorPayload(message=description or ""),
    )
    event_bus.publish(event)


def _emit_session_error_event(agent, description: str) -> None:
    """Emit an 'agent.session.error' event (e.g. auto-compression failures)."""
    from harness_core.event_types import SessionErrorPayload

    event = Event(
        topic="agent.session.error",
        sender=agent.id,
        payload=SessionErrorPayload(message=description),
    )
    event_bus.publish(event)


def _emit_agent_response_event(agent, content: str | None, ollama_response: dict | None, context_length: int, reasoning: str | None = None) -> None:
    """Emit an 'agent.turn.response' event so terminal_io can render it via display_agent_response."""
    from harness_core.event_types import AgentResponsePayload

    event = Event(
        topic="agent.turn.response",
        sender=agent.id,
        payload=AgentResponsePayload(
            content=content or "",
            response=ollama_response,
            context_length=context_length,
            reasoning=reasoning,
        ),
    )
    event_bus.publish(event)


def _emit_turn_stats_event(agent, ollama_response: dict | None, context_length: int, elapsed_seconds: float) -> None:
    """Emit an 'agent.turn.stats' event so terminal_io can render it via display_turn_stats."""
    from harness_core.event_types import TurnStatsPayload

    event = Event(
        topic="agent.turn.stats",
        sender=agent.id,
        payload=TurnStatsPayload(
            response=ollama_response,
            context_length=context_length,
            elapsed_seconds=elapsed_seconds,
        ),
    )
    event_bus.publish(event)


def _emit_tool_call_event(
    agent, func_name: str, args_str: str, summary: str | None = None,
    pre_content: str = "", reasoning: str | None = None,
) -> None:
    """Emit an 'agent.tool.call' event for in-progress tool calls."""
    from harness_core.event_types import ToolCallPayload

    event = Event(
        topic="agent.tool.call",
        sender=agent.id,
        payload=ToolCallPayload(
            func_name=func_name,
            args_str=args_str,
            summary=summary,
            pre_content=pre_content or "",
            reasoning=reasoning,
        ),
    )
    event_bus.publish(event)


def _emit_tool_result_event(
    agent, func_name: str, result_title: str | None = None,
    result_display_text: str = "", result_theme: str = "info",
    result_type_tag: str = "text",
) -> None:
    """Emit an 'agent.tool.result' event for tool results."""
    from harness_core.event_types import ToolResultPayload

    event = Event(
        topic="agent.tool.result",
        sender=agent.id,
        payload=ToolResultPayload(
            func_name=func_name,
            result_title=result_title,
            result_display_text=result_display_text or "",
            result_theme=result_theme or "info",
            result_type_tag=result_type_tag or "text",
        ),
    )
    event_bus.publish(event)



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

    _emit_system_event(
        agent,
        "agent.status.ready",
        f"🚀 Agent Ready — {agent._agent_type.name} ({agent._agent_type.model_name})",
        "Type a message to begin. Type /exit or /quit to stop."
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
                _emit_tool_error_event(agent, outcome.payload or "")
                effective_input = outcome.stripped_message if outcome.stripped_message else user_input
            else:
                # UNKNOWN or SKIP: treat as regular text and send to LLM.
                effective_input = user_input
        else:
            effective_input = user_input

        # Emit a control event to show a spinner at the bottom of the messages
        # panel while the agent is actively working through its handle_prompt
        # loop (LLM calls, tool dispatches, etc.).
        _emit_control_event(agent, "agent.turn.start")
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
                    _emit_agent_response_event(agent, content, ollama_response, agent.context_length, reasoning=reasoning)
                    _emit_turn_stats_event(agent, ollama_response, agent.context_length, elapsed)
                elif kind == TOOL_CALL:
                    _, func_name, args_str, response_data = output
                    args_dict = json.loads(args_str)
                    summary = summarize(func_name, args_dict)
                    pre_content = (response_data or {}).get("pre_tool_content", "") or ""
                    reasoning = (response_data or {}).get("reasoning", "") or ""
                    _emit_tool_call_event(agent, func_name, args_str, summary=summary, pre_content=pre_content, reasoning=reasoning)
                elif kind == TOOL_RESULT:
                    _, func_name, result, response_data = output
                    # Extract ToolResult fields for event payload.
                    result_title = getattr(result, "title", None)
                    result_display_text = getattr(result, "display_text", "") or ""
                    result_theme = getattr(result, "theme", "info") or "info"
                    result_type_tag = getattr(result, "type_tag", "text") or "text"
                    _emit_tool_result_event(
                        agent, func_name,
                        result_title=result_title,
                        result_display_text=result_display_text,
                        result_theme=result_theme,
                        result_type_tag=result_type_tag,
                    )
                elif kind == ERROR:
                    _, description, _, _ = output
                    _emit_tool_error_event(agent, description or "")
        except Exception as exc:  # pragma: no cover - defensive
            _emit_tool_error_event(
                agent,
                f"Agent turn failed: {exc}\n"
                + traceback.format_exc()
            )
        finally:
            # Emit a control event to hide the spinner at the bottom of the
            # messages panel.
            _emit_control_event(agent, "agent.turn.stop")
        
        # Auto-compression check: after each agent response to a user message,
        # if context utilization exceeds 50%, trigger compression.
        if not (user_input.startswith('/') and effective_input == user_input):
            try:
                _check_and_compress_if_needed(agent)
            except Exception as e:
                _emit_session_error_event(agent, f"Auto-compression check failed: {e}")
