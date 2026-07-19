"""Single-hop TUI event-bus wiring for harness_core.terminal_io.

This module is the single place responsible for:
  * subscribing a TUI :class:`EventListener` to the agent-specific event bus topics
  * dispatching incoming :class:`Event` objects directly to the rendering
    handlers in :mod:`harness_core.terminal_io.event_handlers`

There is intentionally no two-hop bridge here: events are not re-posted to a
separate ``tui._app`` dispatch queue. Instead, the listener calls the
``TopicHandlers`` methods directly, and those handlers call ``get_tui()`` to
update the live TUI widgets.
"""

from __future__ import annotations

import re
from typing import Optional

from harness_core.eventbus import Event, EventBus, EventListener, event_bus
from .event_handlers import TopicHandlers


TUI_TOPICS = [
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
]


def make_event_listener(agent_id: str, bus: Optional[EventBus] = None):
    """Build a TUI event listener for the given agent id.

    The listener subscribes to all ``TUI_TOPICS`` and dispatches each incoming
    event directly to the matching :class:`TopicHandlers` method by topic name.
    """
    if bus is None:
        bus = event_bus
    pattern = f"^{re.escape(agent_id)}$"

    class HarnessEventListener(EventListener):
        def __init__(self):
            self._id = "tui"
            self._handlers = TopicHandlers()
            super().__init__(bus, self._id)

        async def _handle_incoming(self, message: Event) -> None:
            await self.handle_default(message)

        async def handle_default(self, event: Event) -> None:
            method_name = "handle_" + event.topic.replace(".", "_").replace("-", "_")
            handler = getattr(self._handlers, method_name, None)
            if handler is not None and callable(handler):
                await handler(event)

        def subscribeToStuff(self):
            self.subscribe(TUI_TOPICS)

    return HarnessEventListener()


def subscribe_event_listener(agent_id: str, bus: Optional[EventBus] = None) -> EventListener:
    """Create, start, and subscribe a TUI event listener for the given agent id."""
    listener = make_event_listener(agent_id, bus)
    listener.run()
    listener.subscribeToStuff()
    return listener


# Backward-compatibility aliases (the old module was named event_listener.py).
make_task_list_listener = make_event_listener
subscribe_task_list_listener = subscribe_event_listener


__all__ = [
    "make_event_listener",
    "subscribe_event_listener",
    "make_task_list_listener",
    "subscribe_task_list_listener",
    "TUI_TOPICS",
]
