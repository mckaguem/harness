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
* ``agent.tool.error`` / ``agent.tool.call`` / ``agent.tool.result`` /
  ``agent.status.usage`` / ``agent.turn.start`` / ``agent.turn.response`` /
  ``agent.turn.stop``
  -> render tool/agent/turn output by calling the matching
  :mod:`.display` helper (or the TUI spinner) for live event-driven display.
"""

from __future__ import annotations

import re
from typing import Callable

from harness_core.eventbus import Event, EventListener, filter_by_sender
from harness_core.event_types import (
    TaskListPayload,
    SystemMessagePayload,
    ToolErrorPayload,
    ToolCallPayload,
    ToolResultPayload,
    UsagePayload,
    TurnStartPayload,
    TurnResponsePayload,
    TurnStopPayload,
)

from .display import (
    print_system,
    display_error,
    display_tool_call,
    display_tool_result,
    display_turn_stats,
    display_agent_response,
)
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


def make_event_listener(agent_id: str) -> EventListener:
    """Create a :class:`HarnessEventListener` filtered to ``agent_id``.

    The returned listener subscribes to the five ``agent.*`` topics.  Each
    handler is decorated with :func:`harness_core.eventbus.filter_by_sender`
    using a per-agent regex (e.g. ``^Agent\\.main$``), so only events published
    by that agent (sender == its id, e.g. ``Agent.main``) reach the TUI — other
    agents' events are silently ignored.
    """
    pattern = f"^{re.escape(agent_id)}$"
    refresh = _make_refresh_handler()
    system_message = _make_system_message_handler()

    class HarnessEventListener(EventListener):
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

        @filter_by_sender(pattern)
        async def handle_agent_tool_error(self, event: Event) -> None:
            payload = event.payload
            if not isinstance(payload, ToolErrorPayload):
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
                payload.summary,
                pre_content=payload.pre_content,
                reasoning=payload.reasoning,
            )

        @filter_by_sender(pattern)
        async def handle_agent_tool_result(self, event: Event) -> None:
            payload = event.payload
            if not isinstance(payload, ToolResultPayload):
                return
            display_tool_result(payload.func_name, payload.result)

        @filter_by_sender(pattern)
        async def handle_agent_status_usage(self, event: Event) -> None:
            payload = event.payload
            if not isinstance(payload, UsagePayload):
                return
            display_turn_stats(
                payload.response,
                payload.context_length,
                elapsed_seconds=payload.elapsed_seconds,
            )

        @filter_by_sender(pattern)
        async def handle_agent_turn_start(self, event: Event) -> None:
            payload = event.payload
            if not isinstance(payload, TurnStartPayload):
                return
            get_tui().show_spinner()

        @filter_by_sender(pattern)
        async def handle_agent_turn_response(self, event: Event) -> None:
            payload = event.payload
            if not isinstance(payload, TurnResponsePayload):
                return
            display_agent_response(
                payload.content,
                payload.response,
                payload.context_length,
                reasoning=payload.reasoning,
            )

        @filter_by_sender(pattern)
        async def handle_agent_turn_stop(self, event: Event) -> None:
            payload = event.payload
            if not isinstance(payload, TurnStopPayload):
                return
            get_tui().hide_spinner()

    return HarnessEventListener()


async def subscribe_event_listener(agent_id: str) -> EventListener:
    """Create and subscribe a :class:`HarnessEventListener` for ``agent_id``."""
    listener = make_event_listener(agent_id)
    await listener.subscribe([
        "agent.tasklist.initialize",
        "agent.tasklist.update",
        "agent.tasklist.reset",
        "agent.session.autocompress",
        "agent.status.ready",
        "agent.tool.error",
        "agent.tool.call",
        "agent.tool.result",
        "agent.status.usage",
        "agent.turn.start",
        "agent.turn.response",
        "agent.turn.stop",
    ])
    return listener


def make_task_list_listener(agent_id: str) -> EventListener:
    """Backward-compatible alias for :func:`make_event_listener`."""
    return make_event_listener(agent_id)


async def subscribe_task_list_listener(agent_id: str) -> EventListener:
    """Backward-compatible alias for :func:`subscribe_event_listener`."""
    return await subscribe_event_listener(agent_id)
