---
name: "harness_core.eventbus.EventListener"
description: "Base class for event listeners using the mailbox pattern."
source: "harness_core/eventbus.py"
---

Base class for event listeners using the mailbox pattern.

Subclasses should implement handler methods named `handle_<topic>` where
`<topic>` is the event topic with dots and hyphens replaced by underscores.
For example, for topic 'user.created', implement `handle_user_created(self, event)`.

For direct messages (topic is None), implement `handle_direct(self, event)`.

The `default_handler` method can be overridden to handle events without
a specific handler method.

## Methods
- **__init__(self, agent_id: str, bus: EventBus)** - Initialize the event listener
- **_mailbox_listener(self) -> None** - The single consumer loop
- **_handle_incoming(self, message: Event) -> None** - Dispatch incoming message to the appropriate handler method
- **handle(self, event: Event) -> None** - Dispatch event to the appropriate handler method
- **default_handler(self, event: Event) -> None** - Default handler for events without a specific handler method
- **subscribe(self, topics: List[str]) -> None** - Subscribe this listener to the specified topics and auto-discovered topics
- **unsubscribe(self, topics: List[str]) -> None** - Unsubscribe this listener from the specified topics
- **send_direct(self, target: str, payload: Any) -> None** - Send a message straight to another agent without blocking
- **publish(self, topic: str, payload: Any) -> None** - Broadcast to a topic without blocking

## Class Variables
None

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [__init__](harness_core_eventbus_EventListener___init__) - Initialize the event listener
- [_mailbox_listener](harness_core_eventbus_EventListener__mailbox_listener) - The single consumer loop
- [_handle_incoming](harness_core_eventbus_EventListener__handle_incoming) - Dispatch incoming message to the appropriate handler method
- [handle](harness_core_eventbus_EventListener_handle) - Dispatch event to the appropriate handler method
- [default_handler](harness_core_eventbus_EventListener_default_handler) - Default handler for events without a specific handler method
- [subscribe](harness_core_eventbus_EventListener_subscribe) - Subscribe this listener to the specified topics and auto-discovered topics
- [unsubscribe](harness_core_eventbus_EventListener_unsubscribe) - Unsubscribe this listener from the specified topics
- [send_direct](harness_core_eventbus_EventListener_send_direct) - Send a message straight to another agent without blocking
- [publish](harness_core_eventbus_EventListener_publish) - Broadcast to a topic without blocking
