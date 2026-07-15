"""Interactive user loop for the agent harness."""

import asyncio
import logging
import time as _time
from rich.console import Console

from typing import TYPE_CHECKING

# Module-level logger for debug logging
logger = logging.getLogger(__name__)

from harness_core.agent.constants import RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR

if TYPE_CHECKING:
    from harness_core.agent.core import Agent
from harness_core.terminal_io import (
    print_system, prompt_user,
    display_tool_call, display_tool_result, display_error,
    display_agent_response, display_user_message, display_turn_stats,
    format_speed,
)
from harness_core.terminal_io.tui import get_tui
from harness_core.tools.dispatcher import summarize
import json
from harness_core.commands import COMMANDS
from harness_core.skills.interceptor import intercept_message, InterceptorKind
from harness_core.eventbus import Event, event_bus, get_event_loop

DEBUG_LOG = "/tmp/harness_debug.log"
def _debug_log(msg: str) -> None:
    """Write a debug message to a file so we can see it even if stdout is captured."""
    try:
        with open(DEBUG_LOG, "a") as f:
            f.write(f"{msg}\n")
            f.flush()
    except Exception:
        pass

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

def _check_and_compress_if_needed(agent) -> None:
    """Check context utilization and trigger compression if above threshold."""
    try:
        messages = getattr(agent, 'messages', None) or (getattr(agent, '_session', None) and getattr(agent, '_session').messages)
        context_length = getattr(agent, '_context_length', 1 << 17)  # default ~131072
        
        if not messages or not context_length:
            return
        
        token_count = _count_approx_tokens(messages)
        utilization = token_count / context_length if context_length > 0 else 0
        
        THRESHOLD = 0.5  # Compress when above 50% utilization
        
        if utilization > THRESHOLD:
            pre_util = utilization
            try:
                from harness_core.session.context_compression import compress_session
                session = getattr(agent, 'session', None) or getattr(agent, '_session', None)
                if session is not None:
                    compress_session(session, fraction=0.1)
                    post_util = _count_approx_tokens(session.messages) / context_length if context_length > 0 else 0
                    # Reflect the compressed context size in the usage stats
                    # sidebar (previously it showed the stale pre-compression size).
                    from harness_core.terminal_io import speed as _speed
                    from harness_core.terminal_io.tui import get_tui as _get_tui
                    _compressed_usage = {"usage": {"prompt_tokens": _count_approx_tokens(session.messages)}}
                    _usage_text = _speed.format_speed(_compressed_usage, context_length)
                    if _usage_text:
                        _get_tui().update_sidebar_usage(_usage_text)
                    _emit_system_event(
                        agent,
                        "agent.session.autocompress",
                        "Auto-Compression",
                        f"Context utilization was {pre_util:.1%} of {context_length} max tokens. Auto-compressed to {post_util:.1%}.",
                    )
            except Exception as e:
                _emit_session_error_event(agent, f"Auto-compression failed: {e}")
    except Exception as e:
        pass  # silently skip on any error

def _emit_system_event(agent, topic: str, title: str, message: str) -> None:
    """Emit a system-notification event, or render it directly when no TUI is active.

    When the textual TUI is active the event is published on the registered app
    loop (set via ``set_event_loop`` in ``TextualHarnessApp.on_mount``) so the
    subscribed :class:`~harness_core.terminal_io.event_listener.HarnessEventListener`
    can render it through the TUI output pane.  In the classic REPL (and other
    non-TUI contexts) there is no event listener subscribed, so we fall back to
    calling :func:`harness_core.terminal_io.display.print_system` directly.
    """
    _debug_log(f"_emit_system_event called: topic={topic}, title={title}")
    
    from harness_core.terminal_io.tui import get_tui

    tui = get_tui()
    tui_active = getattr(tui, "is_active", None)
    if not (callable(tui_active) and tui_active()):
        # Non-TUI mode (classic REPL, tests, non-interactive): render directly.
        print_system(title, message)
        return

    import asyncio
    from harness_core.eventbus import Event, event_bus, get_event_loop
    from harness_core.event_types import SystemMessagePayload

    event = Event(
        topic=topic,
        sender=agent.id,
        payload=SystemMessagePayload(title=title, message=message),
    )
    loop = get_event_loop()
    if loop is not None and loop.is_running():
        try:
            event_bus.publish(event)
            _debug_log(f"Published system event on topic '{topic}' to app loop")
        except RuntimeError as exc:
            # If the loop is closed or not running, fall back to direct render
            print_system(title, message)
    else:
        # No app loop available — render directly (best-effort).
        print_system(title, message)


def _emit_control_event(agent, topic: str) -> None:
    """Emit a control event (e.g. agent.turn.start/stop) on the TUI event loop.

    These are lightweight control events without payload. They are only emitted
    when the textual TUI is active; in non-TUI mode they are no-ops (the classic
    REPL does not need spinner/turn control events).
    """
    agent_id = getattr(agent, 'id', 'unknown-agent')
    from harness_core.terminal_io.tui import get_tui

    tui = get_tui()
    tui_active = getattr(tui, "is_active", None)
    if not (callable(tui_active) and tui_active()):
        # Non-TUI mode: control events are no-ops.
        return

    import asyncio
    from harness_core.eventbus import Event, event_bus, get_event_loop

    event = Event(
        topic=topic,
        sender=agent_id,
        payload=None,
    )
    loop = get_event_loop()
    if loop is not None and loop.is_running():
        try:
            event_bus.publish(event)
        except RuntimeError:
            # If the loop is closed or not running, silently ignore
            # (control events are best-effort in non-TUI mode anyway)
            pass
    else:
        # No app loop available — no-op for control events.
        pass


def _emit_tool_error_event(agent, description: str) -> None:
    """Emit an 'agent.tool.error' event for tool-call errors.

    Handles both high-level agent turn failures and handle_prompt ERROR outputs.
    The TUI listener handles display + panel reset on receipt.
    """
    from harness_core.eventbus import Event, event_bus
    from harness_core.event_types import ToolErrorPayload

    event = Event(
        topic="agent.tool.error",
        sender=agent.id,
        payload=ToolErrorPayload(message=description or ""),
    )
    event_bus.publish(event)


def _emit_session_error_event(agent, description: str) -> None:
    """Emit an 'agent.session.error' event (e.g. auto-compression failures)."""
    from harness_core.eventbus import Event, event_bus
    from harness_core.event_types import SessionErrorPayload

    event = Event(
        topic="agent.session.error",
        sender=agent.id,
        payload=SessionErrorPayload(message=description),
    )
    event_bus.publish(event)


def _emit_agent_response_event(agent, content: str | None, ollama_response: dict | None, context_length: int, reasoning: str | None = None) -> None:
    """Emit an 'agent.turn.response' event so terminal_io can render it via display_agent_response."""
    from harness_core.eventbus import Event, event_bus
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
    from harness_core.eventbus import Event, event_bus
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
    from harness_core.eventbus import Event, event_bus
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
    from harness_core.eventbus import Event, event_bus
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
        # loop (LLM calls, tool dispatches, etc.).  The event is a no-op when
        # no textual TUI is active, so the classic REPL keeps its original
        # behaviour.
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
                    _emit_agent_response_event(agent, content, ollama_response, agent._context_length, reasoning=reasoning)
                    _emit_turn_stats_event(agent, ollama_response, agent._context_length, elapsed)
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
                + (traceback.format_exc() if Console().is_terminal else "")
            )
        finally:
            # Emit a control event to hide the spinner at the bottom of the
            # messages panel.  No-op when no textual TUI is active.
            _emit_control_event(agent, "agent.turn.stop")
        
        # Auto-compression check: after each agent response to a user message,
        # if context utilization exceeds 50%, trigger compression.
        if not (user_input.startswith('/') and effective_input == user_input):
            try:
                _check_and_compress_if_needed(agent)
            except Exception as e:
                _emit_session_error_event(agent, f"Auto-compression check failed: {e}")
