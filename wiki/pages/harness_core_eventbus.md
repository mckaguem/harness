---
name: "harness_core.eventbus"
description: "Event bus implementation for asynchronous event-driven communication."
source: "harness_core/eventbus.py"
---

Event bus implementation for asynchronous event-driven communication.

This module provides:
- Event: A dataclass representing an event with topic, sender, and payload
- EventListener: Base class for objects that can listen to and handle events
- EventBus: A mailbox-pattern event bus for publishing and subscribing to events
- filter_by_sender: Decorator for filtering events by sender
- generate_unique_id: Utility for generating unique identifiers
- set_event_loop/get_event_loop: Functions to manage the application event loop for cross-thread event delivery

## References
- [Event](harness_core_eventbus_Event) - Represents an event in the event bus system
- [EventBus](harness_core_eventbus_EventBus) - Mailbox-pattern event bus for asynchronous agent communication
  - [__init__](harness_core_eventbus_EventBus___init__) - Initialize the event bus with empty mailboxes, bindings, and task tracking
  - [register_background_task](harness_core_eventbus_EventBus_register_background_task) - Register a background task so it is not garbage-collected prematurely
  - [register_agent](harness_core_eventbus_EventBus_register_agent) - Registers an agent using the event loop of the CALLING thread
  - [deregister_agent](harness_core_eventbus_EventBus_deregister_agent) - Clean up an agent's mailbox and all of their topic subscriptions
  - [subscribe](harness_core_eventbus_EventBus_subscribe) - Bind an agent's existing mailbox to a specific topic
  - [unsubscribe](harness_core_eventbus_EventBus_unsubscribe) - Unsubscribe an agent from a specific topic
  - [send_direct](harness_core_eventbus_EventBus_send_direct) - Deliver a message directly to a specific agent's mailbox
  - [publish_to_topic](harness_core_eventbus_EventBus_publish_to_topic) - Broadcast a message to the mailboxes of all subscribed agents
  - [publish](harness_core_eventbus_EventBus_publish) - Broadcasts a message to all subscribed loops safely across threads
- [EventListener](harness_core_eventbus_EventListener) - Base class for event listeners using the mailbox pattern
  - [__init__](harness_core_eventbus_EventListener___init__) - Initialize the event listener
  - [_mailbox_listener](harness_core_eventbus_EventListener__mailbox_listener) - The single consumer loop
  - [_handle_incoming](harness_core_eventbus_EventListener__handle_incoming) - Dispatch incoming message to the appropriate handler method
  - [handle](harness_core_eventbus_EventListener_handle) - Dispatch event to the appropriate handler method
  - [default_handler](harness_core_eventbus_EventListener_default_handler) - Default handler for events without a specific handler method
  - [subscribe](harness_core_eventbus_EventListener_subscribe) - Subscribe this listener to the specified topics and auto-discovered topics
  - [unsubscribe](harness_core_eventbus_EventListener_unsubscribe) - Unsubscribe this listener from the specified topics
  - [send_direct](harness_core_eventbus_EventListener_send_direct) - Send a message straight to another agent without blocking
  - [publish](harness_core_eventbus_EventListener_publish) - Broadcast to a topic without blocking
- [set_event_loop](harness_core_eventbus_set_event_loop) - Register the application's main running event loop
- [get_event_loop](harness_core_eventbus_get_event_loop) - Return the currently registered application event loop, if any
- [generate_unique_id](harness_core_eventbus_generate_unique_id) - Generate a unique identifier with an optional prefix
- [filter_by_sender](harness_core_eventbus_filter_by_sender) - Decorator that only invokes the wrapped async handler when the event's
sender id matches the supplied regular expression
- [Module Index](../index/harness_core.md) - Parent module index
