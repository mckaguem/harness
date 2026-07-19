"""Event-driven wiring between the terminal_io EventBus and the TUI.

This module subscribes a single :class:`HarnessEventListener` to the relevant
``agent.*`` topics, wraps each incoming event into an :class:`EventBusMessage`,
and posts it onto the Textual message bus of the running TUI app.  The TUI app
then dispatches by topic name to the appropriate handler in
:mod:`~harness_core.terminal_io.event_handlers`.

Handled topics (via ``agent.*`` EventBus):

* ``agent.tasklist.initialize`` / ``agent.tasklist.update`` / ``agent.tasklist.reset``
  -> refresh the right-hand TUI task sidebar from the payload.
* ``agent.session.autocompress`` / ``agent.status.ready``
  -> render a system banner via :func:`.display.print_system`.
* ``agent.tool.call`` / ``agent.tool.result`` / ``agent.tool.error``
  -> render tool call/result/error panels via :func:`.display.display_tool_call`,
     :func:`.display.display_tool_result`, and :func:`.display.display_error`.
* ``agent.session.error``
  -> render an error message via :func:`.display.display_error`.
* ``agent.turn.response``
  -> render the agent's response via :func:`.display.display_agent_response`.
* ``agent.turn.stats``
  -> push turn usage + elapsed time to the sidebar via :func:`.speed.display_turn_stats`.
"""

from __future__ import annotations

import re
from typing import Callable, Optional

from textual.message import Message

from harness_core.eventbus import Event, EventBus, EventListener, event_bus, filter_by_sender

from .tui import get_tui


class EventBusMessage(Message):
    """A Textual :class:`~textual.messaging.Message` that wraps an
    :class:`~harness_core.eventbus.Event`.  This is the bridge between the
    harness EventBus and Textual's internal message bus.
    """

    def __init__(self, event: Event) -> None:
        super().__init__()
        self.event = event


def make_event_listener(agent_id: str, bus: Optional[EventBus] = None):
    """Create a :class:`HarnessEventListener` filtered to ``agent_id``.

    The returned listener subscribes to the relevant ``agent.*`` topics and
    dispatches every incoming event through a single :meth:`handle_default`
    handler that wraps the :class:`~harness_core.eventbus.Event` in an
    :class:`EventBusMessage` and posts it onto the running TUI app via
    Textual's message bus.

    Args:
        agent_id: The agent identifier to filter events for (e.g. "Agent.main")
        bus: Optional EventBus instance (defaults to global event_bus singleton)
    """

    if bus is None:
        bus = event_bus

    pattern = f"^{re.escape(agent_id)}$"

    class HarnessEventListener(EventListener):
        def __init__(self):
            self._id = 'tui'
            super().__init__(bus, self._id)

        async def _handle_incoming(self, message: Event) -> None:
            """Route ALL incoming events through :meth:`handle_default`.

            The base :class:`~harness_core.eventbus.EventListener._handle_incoming`
            only calls ``default_handler`` for direct messages (topic=None); for
            topic-based events it looks for a ``handle_<topic>`` method and
            silently drops the event if none is found.  Since our inner class
            only defines :meth:`handle_default`, we override this so every
            incoming EventBus event reaches the bridge wrapper.

            Args:
                message: The raw :class:`~harness_core.eventbus.Event` received
                    from the harness EventBus.
            """
            await self.handle_default(message)

        async def handle_default(self, event: Event) -> None:
            """Wrap the incoming EventBus event into an :class:`EventBusMessage`
            and post it to the running Textual TUI app.  The TUI app's
            ``on_event_bus_message`` handler will then dispatch by topic name.

            Args:
                event: The raw :class:`~harness_core.eventbus.Event` received
                    from the harness EventBus.
            """
            tui = get_tui()
            if tui is None or tui._app is None:
                return
            message = EventBusMessage(event)
            tui._app.post_message(message)

        def subscribeToStuff(self):
            self.subscribe([
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

    return HarnessEventListener()


def subscribe_event_listener(agent_id: str, bus: Optional[EventBus] = None) -> EventListener:
    """Create and subscribe a :class:`HarnessEventListener` for ``agent_id``."""
    listener = make_event_listener(agent_id, bus)
    return listener


def make_task_list_listener(agent_id: str, bus: Optional[EventBus] = None) -> EventListener:
    """Backward-compatible alias for :func:`make_event_listener`."""
    return make_event_listener(agent_id, bus)


def subscribe_task_list_listener(agent_id: str, bus: Optional[EventBus] = None) -> EventListener:
    """Backward-compatible alias for :func:`subscribe_event_listener`."""
    return subscribe_event_listener(agent_id, bus)
