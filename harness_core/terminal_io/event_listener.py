"""Event-driven wiring between the terminal_io EventBus and the TUI.

This module subscribes a single :class:`HarnessEventListener` to the relevant
``agent.*`` topics and dispatches each event to the appropriate handler.  A
sender-id regex filter (see :func:`harness_core.eventbus.filter_by_sender`)
restricts updates to a single agent (e.g. ``Agent.main``), so only events
published by that agent reach the TUI.

Handled topics:

* ``agent.tasklist.initialize`` / ``agent.tasklist.update`` / ``agent.tasklist.reset``
  -> refresh the right-hand TUI task sidebar from the payload.
* ``agent.session.autocompress`` / ``agent.status.ready``
  -> render a system banner via :func:`.display.print_system`.
* ``agent.tool.call`` / ``agent.tool.result`` / ``agent.tool.error``
  -> render tool call/result/error panels via :func:`.display.display_tool_call`,
     :func:`.display.display_tool_result`, and :func:`.display.display_error` (only for events
     whose sender matches the filtered agent id, e.g. ``Agent.main``).
* ``agent.session.error``
  -> render an error message via :func:`.display.display_error` (only for events
    whose sender matches the filtered agent id, e.g. ``Agent.main``).
* ``agent.turn.response``
  -> render the agent's response via :func:`.display.display_agent_response`.
* ``agent.turn.stats``
  -> push turn usage + elapsed time to the sidebar via :func:`.speed.display_turn_stats`.
"""

from __future__ import annotations

import re
from typing import Callable, Optional

from harness_core.eventbus import Event, EventBus, EventListener, event_bus, filter_by_sender
from harness_core.event_types import (
    AgentResponsePayload, SessionErrorPayload, SystemMessagePayload, TaskListPayload, ToolCallPayload, ToolErrorPayload, ToolResultPayload, TurnStatsPayload,
)

from .display import display_agent_response, display_error, display_tool_call, display_tool_result, display_turn_stats, print_system
from .task_display import render_task_list_markdown_from_payload
from .tui import get_tui


def _make_refresh_handler() -> "Callable":
    """Build the shared async handler used by each task-list event handler."""

    async def _refresh(self, event: Event) -> None:
        payload = event.payload
        if not isinstance(payload, TaskListPayload):
            return
        get_tui().update_sidebar_tasks_from_payload(payload)

    return _refresh


def _make_system_message_handler() -> "Callable":
    """Build the shared async handler used by each system-message event handler."""

    async def _system_message(self, event: Event) -> None:
        payload = event.payload
        if not isinstance(payload, SystemMessagePayload):
            return
        print_system(payload.title, payload.message)

    return _system_message


def make_event_listener(agent_id: str, bus: Optional[EventBus] = None) -> EventListener:
    """Create a :class:`HarnessEventListener` filtered to ``agent_id``.

    The returned listener subscribes to the five ``agent.*`` topics.  Each
    handler is decorated with :func:`harness_core.eventbus.filter_by_sender`
    using a per-agent regex (e.g. ``^Agent\\.main$``), so only events published
    by that agent (sender == its id, e.g. ``Agent.main``) reach the TUI — other
    agents' events are silently ignored.

    Args:
        agent_id: The agent identifier to filter events for (e.g. "Agent.main")
        bus: Optional EventBus instance (defaults to global event_bus singleton)
    """

    if bus is None:
        bus = event_bus

    pattern = f"^{re.escape(agent_id)}$"
    refresh = _make_refresh_handler()
    system_message = _make_system_message_handler()

    class HarnessEventListener(EventListener):
        def __init__(self):
            super().__init__(agent_id, bus)

        @filter_by_sender(pattern)
        async def handle_agent_tasklist_initialize(self, event: Event) -> None:
            await refresh(self, event)

        @filter_by_sender(pattern)
        async def handle_agent_tasklist_update(self, event: Event) -> None:
            await refresh(self, event)

        @filter_by_sender(pattern)
        async def handle_agent_tasklist_reset(self, event: Event) -> None:
            await refresh(self, event)

        @filter_by_sender(pattern)
        async def handle_agent_session_autocompress(self, event: Event) -> None:
            await system_message(self, event)

        @filter_by_sender(pattern)
        async def handle_agent_status_ready(self, event: Event) -> None:
            await system_message(self, event)
            payload = event.payload
            if isinstance(payload, SystemMessagePayload):
                tui = get_tui()
                if tui is not None and payload.model:
                    # Only update if the payload has a non-empty model string.
                    # This prevents overwriting the correct value set in on_mount().
                    tui.update_sidebar_model_name(payload.model)

        @filter_by_sender(pattern)
        async def handle_agent_turn_start(self, event: Event) -> None:
            get_tui().show_spinner()

        @filter_by_sender(pattern)
        async def handle_agent_turn_stop(self, event: Event) -> None:
            get_tui().hide_spinner()

        @filter_by_sender(pattern)
        async def handle_agent_tool_error(self, event: Event) -> None:
            payload = event.payload
            if not isinstance(payload, ToolErrorPayload):
                return
            display_error(payload.message)
            # An 'agent.tool.error' signals the end of a tool call chain — no
            # matching result will follow. Clear any pending panel state so a
            # later spurious TOOL_RESULT does not fold into the wrong collapsible.
            from harness_core.terminal_io import display as _display
            _display.reset_pending_tool_panel()

        @filter_by_sender(pattern)
        async def handle_agent_session_error(self, event: Event) -> None:
            payload = event.payload
            if not isinstance(payload, SessionErrorPayload):
                return
            display_error(payload.message)

        @filter_by_sender(pattern)
        async def handle_agent_tool_call(self, event: Event) -> None:
            payload = event.payload
            if not isinstance(payload, ToolCallPayload):
                return
            display_tool_call(
                payload.func_name,
                payload.args_str,
                summary=payload.summary,
                pre_content=payload.pre_content or "",
                reasoning=payload.reasoning,
            )

        @filter_by_sender(pattern)
        async def handle_agent_tool_result(self, event: Event) -> None:
            payload = event.payload
            if not isinstance(payload, ToolResultPayload):
                return
            display_tool_result(
                payload.func_name,
                result_title=payload.result_title,
                result_display_text=payload.result_display_text or "",
                result_theme=payload.result_theme or "info",
                result_type_tag=payload.result_type_tag or "text",
            )

        @filter_by_sender(pattern)
        async def handle_agent_turn_response(self, event: Event) -> None:
            payload = event.payload
            if not isinstance(payload, AgentResponsePayload):
                return
            display_agent_response(
                payload.content,
                payload.response,
                payload.context_length,
                reasoning=payload.reasoning,
            )

        @filter_by_sender(pattern)
        async def handle_agent_turn_stats(self, event: Event) -> None:
            payload = event.payload
            if not isinstance(payload, TurnStatsPayload):
                return
            display_turn_stats(
                payload.response,
                payload.context_length,
                elapsed_seconds=payload.elapsed_seconds,
            )

    return HarnessEventListener()


def subscribe_event_listener(agent_id: str, bus: Optional[EventBus] = None) -> EventListener:
    """Create and subscribe a :class:`HarnessEventListener` for ``agent_id``."""


    listener = make_event_listener(agent_id, bus)
    listener.subscribe([
        "agent.tasklist.initialize",
        "agent.tasklist.update",
        "agent.tasklist.reset",
        "agent.session.autocompress",
        "agent.session.error",
        "agent.status.ready",
        "agent.tool.call",
        "agent.tool.error",
        "agent.tool.result",
        "agent.turn.response",
        "agent.turn.stats",
        "agent.turn.start",
        "agent.turn.stop",
    ])

    return listener


def make_task_list_listener(agent_id: str, bus: Optional[EventBus] = None) -> EventListener:
    """Backward-compatible alias for :func:`make_event_listener`."""
    return make_event_listener(agent_id, bus)


def subscribe_task_list_listener(agent_id: str, bus: Optional[EventBus] = None) -> EventListener:
    """Backward-compatible alias for :func:`subscribe_event_listener`."""
    return subscribe_event_listener(agent_id, bus)