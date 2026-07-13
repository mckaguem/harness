"""Event-driven wiring between the TaskList EventBus and the TUI task sidebar.

This module subscribes an :class:`~harness_core.eventbus.EventListener` to the
``agent.tasklist.*`` events emitted by a TaskList and refreshes the right-hand
TUI task sidebar whenever they fire.  A sender-id regex filter (see
:func:`harness_core.eventbus.filter_by_sender`) restricts updates to a single
agent's task list so, for example, only ``Agent.main``'s tasks are shown.  The
events are now published with the owning agent's id as the sender, so filtering
is done directly on the agent id.
"""

from __future__ import annotations

import re

from harness_core.eventbus import Event, EventListener, filter_by_sender
from harness_core.event_types import TaskListPayload

from .task_display import render_task_list_markdown_from_payload
from .tui import get_tui


def _make_refresh_handler() -> "callable":
    """Build the shared async handler used by each filtered event handler."""

    async def _refresh(self, event: Event) -> None:
        payload = event.payload
        if not isinstance(payload, TaskListPayload):
            return
        get_tui().update_sidebar_tasks_from_payload(payload)

    return _refresh


def make_task_list_listener(agent_id: str) -> EventListener:
    """Create a TaskListEventListener filtered to ``agent_id``'s task list.

    The returned listener subscribes to the three ``agent.tasklist.*`` topics.
    Each handler is decorated with :func:`harness_core.eventbus.filter_by_sender`
    using a per-agent regex (e.g. ``^Agent\\.main$``), so only events published
    by that agent (sender == its id, e.g. ``Agent.main``) reach the TUI — other
    agents' task-list events are silently ignored.
    """
    pattern = f"^{re.escape(agent_id)}$"
    refresh = _make_refresh_handler()

    class _TaskListEventListener(EventListener):
        @filter_by_sender(pattern)
        async def handle_agent_tasklist_initialize(self, event: Event) -> None:
            await refresh(self, event)

        @filter_by_sender(pattern)
        async def handle_agent_tasklist_update(self, event: Event) -> None:
            await refresh(self, event)

        @filter_by_sender(pattern)
        async def handle_agent_tasklist_reset(self, event: Event) -> None:
            await refresh(self, event)

    return _TaskListEventListener()


async def subscribe_task_list_listener(agent_id: str) -> EventListener:
    """Create and subscribe a TaskListEventListener for ``agent_id``."""
    listener = make_task_list_listener(agent_id)
    await listener.subscribe([
        "agent.tasklist.initialize",
        "agent.tasklist.update",
        "agent.tasklist.reset",
    ])
    return listener
