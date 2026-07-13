"""
Event bus implementation for asynchronous event-driven communication.

This module provides:
- Event: A dataclass representing an event with topic, sender, and payload
- EventListener: Base class for objects that can listen to and handle events
- EventBus: A singleton event bus for publishing and subscribing to events
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, List


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
    
    async def subscribe(self, topics: List[str] = None) -> None:
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
        
        Creates an asyncio task for each listener and runs them concurrently
        using asyncio.gather(). This is a fire-and-forget operation.
        
        Args:
            event: The event to publish
        """
        listeners = self._subscribers.get(event.topic, [])
        if not listeners:
            return  # No subscribers for this topic
        
        # Create tasks for all listeners
        tasks = [
            asyncio.create_task(listener.handle(event))
            for listener in listeners
        ]
        
        # Run all tasks concurrently (fire and forget)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Singleton instance of the event bus
event_bus = EventBus()