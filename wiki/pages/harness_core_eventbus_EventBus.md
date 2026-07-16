---
name: "harness_core.eventbus.EventBus"
description: "Mailbox-pattern event bus for asynchronous agent communication."
source: "harness_core/eventbus.py"
---

Mailbox-pattern event bus for asynchronous agent communication.

The event bus maintains a mailbox (asyncio.Queue) for each registered agent.
Agents subscribe to topics, and publishing to a topic delivers the event to
all subscribed agents' mailboxes. Agents process messages sequentially from
their mailbox via a background listener task.

## Methods
- **__init__(self) -> None** - Initialize the event bus with empty mailboxes, bindings, and task tracking
- **register_background_task(self, coro: Any)** - Register a background task so it is not garbage-collected prematurely
- **register_agent(self, agent_id: str) -> asyncio.Queue[Any]** - Registers an agent using the event loop of the CALLING thread
- **deregister_agent(self, agent_id: str) -> None** - Clean up an agent's mailbox and all of their topic subscriptions
- **subscribe(self, agent_id: str, topic: str) -> None** - Bind an agent's existing mailbox to a specific topic
- **unsubscribe(self, agent_id: str, topic: str) -> None** - Unsubscribe an agent from a specific topic
- **send_direct(self, sender: str, target_agent_id: str, payload: Any) -> None** - Deliver a message directly to a specific agent's mailbox
- **publish_to_topic(self, sender: str, topic: str, payload: Any) -> None** - Broadcast a message to the mailboxes of all subscribed agents
- **publish(self, event: Event)** - Broadcasts a message to all subscribed loops safely across threads

## Class Variables
None

## References
- [Module: harness_core.eventbus](harness_core_eventbus) - Parent module
- [__init__](harness_core_eventbus_EventBus___init__) - Initialize the event bus with empty mailboxes, bindings, and task tracking
- [register_background_task](harness_core_eventbus_EventBus_register_background_task) - Register a background task so it is not garbage-collected prematurely
- [register_agent](harness_core_eventbus_EventBus_register_agent) - Registers an agent using the event loop of the CALLING thread
- [deregister_agent](harness_core_eventbus_EventBus_deregister_agent) - Clean up an agent's mailbox and all of their topic subscriptions
- [subscribe](harness_core_eventbus_EventBus_subscribe) - Bind an agent's existing mailbox to a specific topic
- [unsubscribe](harness_core_eventbus_EventBus_unsubscribe) - Unsubscribe an agent from a specific topic
- [send_direct](harness_core_eventbus_EventBus_send_direct) - Deliver a message directly to a specific agent's mailbox
- [publish_to_topic](harness_core_eventbus_EventBus_publish_to_topic) - Broadcast a message to the mailboxes of all subscribed agents
- [publish](harness_core_eventbus_EventBus_publish) - Broadcasts a message to all subscribed loops safely across threads
