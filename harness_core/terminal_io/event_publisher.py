"""Event publisher for TUI user input events.

This module provides :class:`TuiEventPublisher`, which publishes user input
events to the event bus when the user submits text through the terminal interface.
It is used as an alternative to the blocking prompt model — instead of waiting
for user input synchronously, the TUI publishes a ``UserInputPayload`` event that
the agent's :class:`~harness_core.agent.mixin.EventListenerLoopMixin` subscribes to.

Usage::

    from harness_core.terminal_io.event_publisher import get_tui_publisher
    publisher = get_tui_publisher()
    if publisher:
        publisher.publish_user_input(user_text)
"""

from __future__ import annotations

import threading
from typing import Optional

from harness_core.eventbus import EventPublisher, event_bus


class TuiEventPublisher(EventPublisher):
    """Publishes user input events from the TUI to the event bus.
    
    This is an :class:`~harness_core.eventbus.EventPublisher` that uses
    ``"Tui.main"`` as its sender id so agents can filter incoming messages
    using a regex pattern like ``r"^Tui\\.main$"``.
    
    Only one instance should exist per process — use :func:`get_tui_publisher`
    to obtain it.
    """

    TUI_SENDER_ID = "Tui.main"
    USER_INPUT_TOPIC = "tui.user.input"

    def __init__(self) -> None:
        super().__init__(event_bus, self.TUI_SENDER_ID)

    def publish_user_input(self, message: str, source: str = "tui") -> None:
        """Publish a user input event to the bus.
        
        Args:
            message: The text content submitted by the user.
            source: Identifier of where the input came from (defaults to "tui").
        """
        from harness_core.event_types import UserInputPayload
        import logging
        logging.debug(f"publish_user_input {message}")
        self.publish(
            self.USER_INPUT_TOPIC,
            UserInputPayload(message=message, source=source),
        )


# Module-level singleton guard — only one publisher per process.
_tui_publisher: Optional[TuiEventPublisher] = None
_lock = threading.Lock()


def get_tui_publisher() -> Optional[TuiEventPublisher]:
    """Return the process-wide :class:`TuiEventPublisher` instance.
    
    Creates and caches a singleton on first call. Returns ``None`` if the
    publisher has not been initialized yet (e.g., before any TUI is launched).
    
    The publisher is lazily created so that non-TUI code paths don't pay the
    cost of importing this module at startup time.
    """
    global _tui_publisher
    with _lock:
        if _tui_publisher is None:
            _tui_publisher = TuiEventPublisher()
        return _tui_publisher


def reset_tui_publisher() -> None:
    """Reset the publisher singleton (useful for testing)."""
    global _tui_publisher
    with _lock:
        _tui_publisher = None
