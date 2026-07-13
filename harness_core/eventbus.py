"""
Event bus implementation for asynchronous event-driven communication.

This module provides:
- Event: A dataclass representing an event with topic, sender, and payload
- EventListener: Base class for objects that can listen to and handle events
- EventBus: A singleton event bus for publishing and subscribing to events
"""

import asyncio
import functools
import re
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


# Reference to the application's main running event loop, if one has been
# registered (e.g. by the TUI on mount). When set, events published from any
# thread -- including worker threads that have no running loop of their own --
# are marshalled onto this loop so their handlers run on the correct thread.
_event_loop: Optional["asyncio.AbstractEventLoop"] = None


def set_event_loop(loop: Optional["asyncio.AbstractEventLoop"]) -> None:
    """Register the application's main running event loop.

    When set, methods that publish events off the loop thread (such as the
    agent loop running on a worker thread) will marshal delivery onto this
    loop via ``call_soon_threadsafe`` so subscribed listeners still fire on
    the correct thread. Pass ``None`` to clear the registration.
    """
    global _event_loop
    _event_loop = loop


def get_event_loop() -> Optional["asyncio.AbstractEventLoop"]:
    """Return the currently registered application event loop, if any."""
    return _event_loop


def generate_unique_id(prefix: str = "") -> str:
    """Generate a unique identifier with an optional prefix.

    Args:
        prefix: Optional prefix to prepend to the UUID (e.g., "TaskList", "Agent")

    Returns:
        A unique identifier string in the format "prefix.uuid" or just "uuid"
    """
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID for brevity
    if prefix:
        return f"{prefix}.{unique_id}"
    return unique_id


def filter_by_sender(sender_regex: str):
    """Decorator that only invokes the wrapped async handler when the event's
    sender id matches the supplied regular expression.

    If the sender does not match, the handler is skipped entirely.
    """
    pattern = re.compile(sender_regex)

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, event: Event):
            if pattern.search(event.sender):
                await func(self, event)
        return wrapper
    return decorator


@dataclass
class Event:
    """Represents an event in the event bus system.

    Attributes:
        topic: The event topic/name (e.g., 'user_created', 'message_received')
        sender: The identifier of the event sender
        payload: Arbitrary data associated with the event
    """
    topic: str
    sender: str
    payload: Any


class EventListener:
    """Base class for event listeners.

    Subclasses should implement handler methods named `handle_<topic>` where
    `<topic>` is the event topic with underscores replacing special characters.
    For example, for topic 'user.created', implement `handle_user_created(self, event)`.

    The `default_handler` method can be overridden to handle events without
    a specific handler method.
    """

    async def handle(self, event: Event) -> None:
        """Dispatch event to the appropriate handler method.

        Args:
            event: The event to handle
        """
        # Convert topic to valid method name (replace . and - with _)
        method_name = f"handle_{event.topic.replace('.', '_').replace('-', '_')}"

        handler = getattr(self, method_name, None)
        if handler is not None and callable(handler):
            await handler(event)
        else:
            await self.default_handler(event)

    async def default_handler(self, event: Event) -> None:
        """Default handler for events without a specific handler method.

        Override this method in subclasses to provide default handling behavior.

        Args:
            event: The event that was not handled by a specific method
        """
        pass  # Do nothing by default

    async def subscribe(self, topics: Optional[List[str]] = None) -> None:
        """Subscribe this listener to the specified topics and auto-discovered topics.

        This method:
        1. Finds all methods on the object named handle_* and extracts topic names
        2. Subscribes self to each topic in `topics` list AND discovered topics

        Args:
            topics: Optional list of additional topics to subscribe to
        """
        if topics is None:
            topics = []

        # Auto-discover handler methods
        discovered_topics = []
        for attr_name in dir(self):
            if attr_name.startswith('handle_') and attr_name != 'handle':
                # Convert method name back to topic
                # handle_user_created -> user.created
                topic = attr_name[7:]  # Remove 'handle_'
                topic = topic.replace('_', '.')
                discovered_topics.append(topic)

        # Combine explicit topics with discovered topics
        all_topics = list(set(topics + discovered_topics))

        # Subscribe to all topics on the singleton event bus
        for topic in all_topics:
            event_bus.subscribe(topic, self)


class EventBus:
    """Singleton event bus for publishing and subscribing to events.

    The event bus maintains a mapping of topics to lists of listeners.
    When an event is published, it is delivered to all subscribed listeners
    concurrently using asyncio tasks.
    """

    def __init__(self) -> None:
        """Initialize the event bus with an empty topic-to-listeners mapping."""
        self._subscribers: Dict[str, List[EventListener]] = {}

    def subscribe(self, topic: str, listener: EventListener) -> None:
        """Subscribe a listener to a topic.

        Args:
            topic: The event topic to subscribe to
            listener: The EventListener instance to subscribe
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []

        # Avoid duplicate subscriptions
        if listener not in self._subscribers[topic]:
            self._subscribers[topic].append(listener)

    def unsubscribe(self, topic: str, listener: EventListener) -> None:
        """Unsubscribe a listener from a topic.

        Args:
            topic: The event topic to unsubscribe from
            listener: The EventListener instance to unsubscribe
        """
        if topic in self._subscribers:
            if listener in self._subscribers[topic]:
                self._subscribers[topic].remove(listener)
            # Clean up empty topic lists
            if not self._subscribers[topic]:
                del self._subscribers[topic]

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers of its topic.

        Delivery is safe to call from any thread:

        * When called from an async context that already has a running loop on
          the current thread (e.g. unit tests or when awaited directly on the
          app loop), listeners are invoked inline via ``asyncio.gather`` so the
          caller can ``await`` completion and observe side effects immediately.
        * When called from a thread with no running loop (e.g. a worker thread
          running the agent loop), delivery is marshalled onto the registered
          application loop (set via :func:`set_event_loop`) using
          ``call_soon_threadsafe``. If no application loop is registered, a
          temporary loop is spun up to deliver inline.

        Args:
            event: The event to publish
        """
        listeners = self._subscribers.get(event.topic, [])
        if not listeners:
            return  # No subscribers for this topic

        async def _deliver() -> None:
            tasks = [listener.handle(event) for listener in listeners]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            # We are on a running loop's thread -- deliver inline so callers
            # that await publish() observe handler side effects synchronously.
            await _deliver()
            return

        # No running loop on this thread. Marshal to the registered app loop if
        # available (thread-safe, even from another thread); otherwise run a
        # throwaway loop inline to deliver the event.
        if _event_loop is not None and _event_loop.is_running():
            _event_loop.call_soon_threadsafe(
                lambda: asyncio.ensure_future(_deliver(), loop=_event_loop)
            )
            return

        asyncio.run(_deliver())


# Singleton instance of the event bus
event_bus = EventBus()
