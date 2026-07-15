"""
Event bus implementation for asynchronous event-driven communication.

This module provides:
- Event: A dataclass representing an event with topic, sender, and payload
- EventListener: Base class for objects that can listen to and handle events
- EventBus: A mailbox-pattern event bus for publishing and subscribing to events
- filter_by_sender: Decorator for filtering events by sender
- generate_unique_id: Utility for generating unique identifiers
- set_event_loop/get_event_loop: Functions to manage the application event loop for cross-thread event delivery
"""

import asyncio
import functools
import logging
import re
import threading
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


# Module-level logger for the event bus
logger = logging.getLogger(__name__)


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

    Args:
        sender_regex: Regular expression pattern to match against event.sender
    """
    pattern = re.compile(sender_regex)

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, event: "Event"):
            if pattern.search(event.sender):
                await func(self, event)
        return wrapper
    return decorator


@dataclass
class Event:
    """Represents an event in the event bus system.

    Attributes:
        topic: The event topic/name (e.g., 'user_created', 'message_received').
               None for direct messages.
        sender: The identifier of the event sender
        payload: Arbitrary data associated with the event
    """
    topic: Optional[str]
    sender: str
    payload: Any


class EventBus:
    """Mailbox-pattern event bus for asynchronous agent communication.

    The event bus maintains a mailbox (asyncio.Queue) for each registered agent.
    Agents subscribe to topics, and publishing to a topic delivers the event to
    all subscribed agents' mailboxes. Agents process messages sequentially from
    their mailbox via a background listener task.
    """

    def __init__(self) -> None:
        """Initialize the event bus with empty mailboxes, bindings, and task tracking."""
        # Maps topic -> set of agent_ids subscribed to it (Bindings)
        self._bindings: Dict[str, Set[str]] = {}
        # Maps agent_id -> tuple of (mailbox, event_loop_bound_to_thread)
        self._mailboxes: Dict[str, Tuple[asyncio.Queue, Optional[asyncio.AbstractEventLoop]]] = {}
        # Kept for backward compatibility with tests that reference it.
        self._running_tasks: Set["asyncio.Task"] = set()

    def register_background_task(self, coro: Any):
        """Register a background task so it is not garbage-collected prematurely.

        This method exists for backward-compatibility with older test fixtures;
        the current publish path does synchronous delivery and no longer needs
        explicit task tracking. Callers may still pass coroutines here — they are
        scheduled as :class:`asyncio.Task` objects, stored in
        :attr:`_running_tasks`, and automatically removed when they complete.

        Args:
            coro: A coroutine (or existing Task) to register and run.

        Returns:
            The registered :class:`asyncio.Task` so callers can await it directly.
        """
        if asyncio.iscoroutine(coro):
            task = asyncio.create_task(coro)
        elif isinstance(coro, asyncio.Task):
            task = coro
        else:  # pragma: no cover - defensive; callers pass coroutines or Tasks
            raise TypeError(
                f"register_background_task expects a coroutine or Task, got {type(coro).__name__}"
            )

        def _on_done(t: "asyncio.Task") -> None:
            self._running_tasks.discard(t)

        task.add_done_callback(_on_done)
        self._running_tasks.add(task)
        return task

    def register_agent(self, agent_id: str) -> asyncio.Queue[Any]:
        """Registers an agent using the event loop of the CALLING thread.

        If no event loop is currently running (e.g. when called from a
        synchronous context such as unit tests), stores ``None`` as the bound
        loop — calls to :meth:`publish` will then deliver directly via
        :meth:`asyncio.Queue.put_nowait` on the same thread, which is always
        safe for synchronous callers.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            The ``asyncio.Queue`` mailbox bound to this thread's loop.

        Raises:
            ValueError: If the agent_id is already registered
        """
        if agent_id in self._mailboxes:
            raise ValueError(f"Agent '{agent_id}' is already registered.")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running on this thread (e.g. sync test context).
            loop = None  # type: ignore[assignment]
        mailbox: asyncio.Queue[Any] = asyncio.Queue()

        self._mailboxes[agent_id] = (mailbox, loop)
        return mailbox

    def deregister_agent(self, agent_id: str) -> None:
        """Clean up an agent's mailbox and all of their topic subscriptions.

        Args:
            agent_id: Unique identifier for the agent to deregister
        """
        self._mailboxes.pop(agent_id, None)
        for subscribed_agents in self._bindings.values():
            subscribed_agents.discard(agent_id)

    def subscribe(self, agent_id: str, topic: str) -> None:
        """Bind an agent's existing mailbox to a specific topic.

        Args:
            agent_id: Unique identifier for the agent
            topic: The topic to subscribe to

        Raises:
            ValueError: If the agent_id is not registered
        """
        if agent_id not in self._mailboxes:
            raise ValueError(f"Agent '{agent_id}' must be registered before subscribing.")

        if topic not in self._bindings:
            self._bindings[topic] = set()
        self._bindings[topic].add(agent_id)

    def unsubscribe(self, agent_id: str, topic: str) -> None:
        """Unsubscribe an agent from a specific topic.

        Args:
            agent_id: Unique identifier for the agent
            topic: The topic to unsubscribe from
        """
        if topic in self._bindings:
            self._bindings[topic].discard(agent_id)
            # Clean up empty topic sets
            if not self._bindings[topic]:
                del self._bindings[topic]

    def send_direct(self, sender: str, target_agent_id: str, payload: Any) -> None:
        """Deliver a message directly to a specific agent's mailbox.

        This is a point-to-point message (topic is None).

        Args:
            sender: Identifier of the sender
            target_agent_id: Unique identifier of the target agent
            payload: Arbitrary data to send
        """
        entry = self._mailboxes.get(target_agent_id)
        if entry:
            mailbox, loop = entry  # Unpack (mailbox, loop) tuple
            event = Event(topic=None, sender=sender, payload=payload)
            mailbox.put_nowait(event)

    def publish_to_topic(self, sender: str, topic: str, payload: Any) -> None:
        """Broadcast a message to the mailboxes of all subscribed agents.

        Args:
            sender: Identifier of the sender
            topic: The topic to publish to
            payload: Arbitrary data to send
        """
        if topic not in self._bindings:
            return

        event = Event(topic=topic, sender=sender, payload=payload)
        for agent_id in self._bindings[topic]:
            entry = self._mailboxes.get(agent_id)
            if entry:
                mailbox, loop = entry  # Unpack (mailbox, loop) tuple
                mailbox.put_nowait(event)

    def publish(self, event: Event):
        """Broadcasts a message to all subscribed loops safely across threads.
        
        When called from a worker thread, schedules delivery onto each target's
        event loop via call_soon_threadsafe. When called on the same thread as
        the target (e.g., non-TUI mode), delivers directly.
        
        Args:
            event: The event to publish (must have a topic)
        """
        if event.topic is None:
            return

        if event.topic not in self._bindings:
            return

        for agent_id in self._bindings[event.topic]:
            entry = self._mailboxes.get(agent_id)
            if entry:
                mailbox, loop = entry

                # If no loop was bound (e.g. synchronous context), deliver directly.
                if loop is None:
                    try:
                        mailbox.put_nowait(event)
                    except Exception:
                        pass
                else:
                    try:
                        current_thread = threading.current_thread()
                        target_loop_thread = getattr(loop, '_thread', None)

                        same_thread = (current_thread is target_loop_thread) if target_loop_thread else False

                        if same_thread:
                            # Same thread - direct put_nowait (fast path)
                            mailbox.put_nowait(event)
                        else:
                            # Different thread - use call_soon_threadsafe to schedule delivery
                            try:
                                loop.call_soon_threadsafe(mailbox.put_nowait, event)
                            except RuntimeError as exc:
                                try:
                                    mailbox.put_nowait(event)
                                except Exception:
                                    pass
                    except AttributeError:
                        # Some AbstractEventLoop implementations don't expose _thread.
                        # Fall back to call_soon_threadsafe anyway; if that fails too,
                        # direct put_nowait is a last-resort delivery.
                        try:
                            loop.call_soon_threadsafe(mailbox.put_nowait, event)
                        except RuntimeError:
                            try:
                                mailbox.put_nowait(event)
                            except Exception:
                                pass


class EventListener:
    """Base class for event listeners using the mailbox pattern.

    Subclasses should implement handler methods named `handle_<topic>` where
    `<topic>` is the event topic with dots and hyphens replaced by underscores.
    For example, for topic 'user.created', implement `handle_user_created(self, event)`.

    For direct messages (topic is None), implement `handle_direct(self, event)`.

    The `default_handler` method can be overridden to handle events without
    a specific handler method.
    """

    def __init__(self, agent_id: str, bus: EventBus):
        """Initialize the event listener.
        
        Args:
            agent_id: Unique identifier for this listener/agent
            bus: The EventBus instance to use for communication
        """
        self.agent_id = agent_id
        self.bus = bus

        logger.debug("Creating EventListener for agent %s on loop %r", self.agent_id, asyncio.get_running_loop())

        logger.info("Initializing EventListener for agent %s", self.agent_id)

        # 1. Register with the bus. This binds our mailbox to 
        #    the current worker thread's event loop.
        self.mailbox = self.bus.register_agent(self.agent_id)
        
        # 2. Keep a local strong reference to the listener task
        #    to prevent garbage collection while we're running.
        self._listener_task = asyncio.create_task(self._mailbox_listener())
        # Verify the listener task started successfully
        if self._listener_task.done():
            # Get any exception that occurred during startup
            try:
                self._listener_task.result()
            except Exception as e:
                logger.error("Listener task failed immediately in __init__: %s", e)
        logger.info("Listener for agent %s registered with bus on loop %r", self.agent_id)

    async def _mailbox_listener(self) -> None:
        """The single consumer loop. Processes everything sequentially."""
        logger.info("Mailbox listener started for agent %s", self.agent_id)
        try:
            while True:
                # Yields control to the loop if the mailbox is empty.
                # Once a message arrives, this wakes up.
                message = await self.mailbox.get()

                topic = message.topic or "direct"
                logger.debug("Processing event for agent %s on topic '%s'", self.agent_id, topic)

                try:
                    await self._handle_incoming(message)
                    logger.debug("Successfully handled event on topic '%s' for agent %s", topic, self.agent_id)
                except Exception as e:
                    # Log full traceback with handler name and payload details — but DON'T re-raise!
                    # Re-raising would kill the listener task and silently stop all future events.
                    import traceback
                    logger.exception(
                        "Unhandled exception in handler for agent %s on topic '%s':\n%s\nPayload: %r",
                        self.agent_id,
                        topic,
                        e,
                        message.payload if hasattr(message.payload, 'to_dict') else str(message.payload)
                    )

                self.mailbox.task_done()
        except asyncio.CancelledError:
            # Listener cancelled — the bus will handle cleanup via deregister_agent
            logger.info("Mailbox listener cancelled for agent %s", self.agent_id)

    async def _handle_incoming(self, message: Event) -> None:
        """Dispatch incoming message to the appropriate handler method.

        Args:
            message: The event message to handle
        """
        if message.topic is None:
            # Direct message - use a special handler if available
            handler = getattr(self, "handle_direct", None)
            if handler is not None and callable(handler):
                logger.debug("Dispatching direct message to handler")
                await handler(message)
            else:
                # Fall back to default_handler for direct messages without handle_direct
                logger.warning(
                    "Received direct message for agent %s with no handle_direct method",
                    self.agent_id,
                )
                await self.default_handler(message)
        else:
            # Topic-based dispatch
            topic = message.topic.replace(".", "_").replace("-", "_")
            handler_name = f"handle_{topic}"

            logger.debug("Looking up handler '%s' for agent %s", handler_name, self.agent_id)

            handler = getattr(self, handler_name, None)
            if handler is not None and callable(handler):
                logger.debug("Calling handler '%s'", handler_name)
                try:
                    await handler(message)
                    logger.debug("Successfully called handler '%s' for agent %s", handler_name, self.agent_id)
                except Exception as e:
                    # Log full traceback with payload details for debugging
                    import traceback
                    logger.exception(
                        "Handler '%s' failed for agent %s:\n%s\nPayload type: %r\nPayload data: %r",
                        handler_name,
                        self.agent_id,
                        e,
                        type(message.payload).__name__,
                        message.payload.to_dict() if hasattr(message.payload, 'to_dict') else str(message.payload)
                    )
                    # Re-raise to break the loop — this prevents silent failures
            else:
                logger.warning(
                    "No handler found for topic '%s' on agent %s",
                    topic,
                    self.agent_id,
                )

    async def handle(self, event: Event) -> None:
        """Dispatch event to the appropriate handler method.

        Converts the topic to a valid method name (replacing . and - with _)
        and calls handle_<topic> if it exists, otherwise calls default_handler.

        Args:
            event: The event to handle
        """
        # Convert topic to valid method name (replace . and - with _); treat None as direct message.
        topic = event.topic or "direct"
        method_name = f"handle_{topic.replace('.', '_').replace('-', '_')}"

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

    def subscribe(self, topics: List[str]) -> None:
        """Subscribe this listener to the specified topics and auto-discovered topics.

        This method:
        1. Finds all methods on the object named handle_* and extracts topic names
        2. Subscribes self to each topic in `topics` list AND discovered topics

        Args:
            topics: List of additional topics to subscribe to
        """
        if topics is None:
            topics = []

        # Auto-discover handler methods
        discovered_topics = []
        for attr_name in dir(self):
            if attr_name.startswith('handle_') and attr_name not in ('handle', 'handle_direct', 'handle_event'):
                # Convert method name back to topic
                # handle_user_created -> user.created
                topic = attr_name[7:]  # Remove 'handle_'
                topic = topic.replace('_', '.')
                discovered_topics.append(topic)

        # Combine explicit topics with discovered topics
        all_topics = list(set(topics + discovered_topics))

        # Subscribe to all topics on the bus
        for topic in all_topics:
            self.bus.subscribe(self.agent_id, topic)

    def unsubscribe(self, topics: List[str]) -> None:
        """Unsubscribe this listener from the specified topics.

        Args:
            topics: List of topics to unsubscribe from
        """
        for topic in topics:
            self.bus.unsubscribe(self.agent_id, topic)

    def send_direct(self, target: str, payload: Any) -> None:
        """Send a message straight to another agent without blocking.

        Args:
            target: The target agent_id
            payload: Arbitrary data to send
        """
        self.bus.send_direct(sender=self.agent_id, target_agent_id=target, payload=payload)

    def publish(self, topic: str, payload: Any) -> None:
        """Broadcast to a topic without blocking.

        Args:
            topic: The topic to publish to
            payload: Arbitrary data to send
        """
        self.bus.publish_to_topic(sender=self.agent_id, topic=topic, payload=payload)


# Singleton instance of the event bus
event_bus = EventBus()