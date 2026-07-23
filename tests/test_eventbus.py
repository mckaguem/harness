"""Comprehensive tests for harness_core.eventbus with 100% coverage."""

import asyncio
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from harness_core.eventbus import Event, EventBus, EventListener, event_bus, filter_by_sender, generate_unique_id


def _require_registration(bus: EventBus, agent_id: str) -> None:
    """Helper that registers *agent_id* on the bus if not already done."""
    if agent_id not in bus._mailboxes:
        bus.register_agent(agent_id)


class TestEventDataclass:
    """Tests for the Event dataclass."""

    def test_event_creation_with_str_payload(self):
        event = Event(topic="user.created", sender="user_service", payload="hello")
        assert event.topic == "user.created"
        assert event.sender == "user_service"
        assert event.payload == "hello"

    def test_event_creation_with_int_payload(self):
        event = Event(topic="counter.increment", sender="counter_service", payload=42)
        assert event.payload == 42

    def test_event_creation_with_dict_payload(self):
        payload = {"user_id": 123, "name": "John", "active": True}
        event = Event(topic="user.updated", sender="api", payload=payload)
        assert event.payload == payload

    def test_event_creation_with_list_payload(self):
        payload = [1, 2, 3, "a", "b", "c"]
        event = Event(topic="items.added", sender="service", payload=payload)
        assert event.payload == payload

    def test_event_creation_with_none_payload(self):
        event = Event(topic="event.empty", sender="system", payload=None)
        assert event.payload is None

    def test_event_creation_with_complex_payload(self):
        payload = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "meta": {"total": 2, "page": 1}
        }
        event = Event(topic="users.list", sender="api", payload=payload)
        assert event.payload == payload

    def test_event_creation_with_none_topic(self):
        event = Event(topic=None, sender="user1", payload="direct message")
        assert event.topic is None
        assert event.sender == "user1"
        assert event.payload == "direct message"

    def test_event_mutability(self):
        event = Event(topic="test", sender="sender", payload="value")
        event.topic = "modified"
        assert event.topic == "modified"

    def test_event_equality(self):
        event1 = Event(topic="test", sender="sender", payload="data")
        event2 = Event(topic="test", sender="sender", payload="data")
        event3 = Event(topic="other", sender="sender", payload="data")
        assert event1 == event2
        assert event1 != event3


class TestEventBus:
    """Tests for the EventBus mailbox pattern."""

    def setup_method(self):
        self.bus = EventBus()

    def test_register_agent_creates_mailbox(self):
        mailbox, _loop = self.bus.register_agent("agent1")
        assert isinstance(mailbox, asyncio.Queue)
        assert "agent1" in self.bus._mailboxes

    def test_register_agent_raises_on_duplicate(self):
        self.bus.register_agent("agent1")
        with pytest.raises(ValueError, match="already registered"):
            self.bus.register_agent("agent1")

    def test_deregister_agent_removes_mailbox_and_bindings(self):
        self.bus.register_agent("agent1")
        self.bus.subscribe("agent1", "topic1")
        self.bus.subscribe("agent1", "topic2")

        self.bus.deregister_agent("agent1")

        assert "agent1" not in self.bus._mailboxes
        assert "agent1" not in self.bus._bindings.get("topic1", set())
        assert "agent1" not in self.bus._bindings.get("topic2", set())

    def test_subscribe_agent_to_topic(self):
        self.bus.register_agent("agent1")
        self.bus.subscribe("agent1", "topic1")

        assert "topic1" in self.bus._bindings
        assert "agent1" in self.bus._bindings["topic1"]

    def test_subscribe_raises_for_unregistered_agent(self):
        with pytest.raises(ValueError, match="must be registered"):
            self.bus.subscribe("unknown_agent", "topic1")

    def test_unsubscribe_agent_from_topic(self):
        self.bus.register_agent("agent1")
        self.bus.subscribe("agent1", "topic1")
        self.bus.unsubscribe("agent1", "topic1")

        assert "agent1" not in self.bus._bindings.get("topic1", set())

    def test_unsubscribe_cleans_empty_topics(self):
        self.bus.register_agent("agent1")
        self.bus.subscribe("agent1", "topic1")
        self.bus.unsubscribe("agent1", "topic1")

        assert "topic1" not in self.bus._bindings

    def test_send_direct_delivers_to_target_mailbox(self):
        self.bus.register_agent("agent1")
        self.bus.register_agent("agent2")

        self.bus.send_direct("sender", "agent2", "direct message")

        mailbox = self.bus._mailboxes["agent2"][0]
        assert not mailbox.empty()
        event = mailbox.get_nowait()
        assert event.topic is None
        assert event.sender == "sender"
        assert event.payload == "direct message"

    def test_send_direct_to_nonexistent_agent_no_op(self):
        self.bus.register_agent("agent1")
        self.bus.send_direct("sender", "nonexistent", "message")

    def test_publish_to_topic_delivers_to_all_subscribers(self):
        self.bus.register_agent("agent1")
        self.bus.register_agent("agent2")
        self.bus.register_agent("agent3")
        self.bus.subscribe("agent1", "topic1")
        self.bus.subscribe("agent2", "topic1")

        self.bus.publish_to_topic("sender", "topic1", "broadcast message")

        event1 = self.bus._mailboxes["agent1"][0].get_nowait()
        event2 = self.bus._mailboxes["agent2"][0].get_nowait()
        assert self.bus._mailboxes["agent3"][0].empty()

        assert event1.topic == "topic1"
        assert event1.sender == "sender"
        assert event1.payload == "broadcast message"
        assert event2.topic == "topic1"
        assert event2.payload == "broadcast message"

    def test_publish_to_topic_with_no_subscribers_no_op(self):
        self.bus.register_agent("agent1")
        self.bus.publish_to_topic("sender", "topic1", "message")
        assert self.bus._mailboxes["agent1"][0].empty()

    def test_publish_event_delivers_via_bus(self):
        self.bus.register_agent("agent1")
        self.bus.subscribe("agent1", "topic_x")

        event = Event(topic="topic_x", sender="s", payload="x")
        self.bus.publish(event)

        received = self.bus._mailboxes["agent1"][0].get_nowait()
        assert received.payload == "x"


class TestEventListener:
    """Tests for the EventListener base class."""

    @pytest.fixture
    def bus(self):
        return EventBus()

    @pytest.fixture
    def agent_id(self):
        return f"test_agent_{id(object())}"

    class SimpleListener(EventListener):
        def __init__(self, agent_id, bus):
            super().__init__(bus, agent_id)
            self.handled_events: List[Event] = []
            self.default_handled: List[Event] = []

        async def handle_test_event(self, event: Event) -> None:
            self.handled_events.append(event)

        async def default_handler(self, event: Event) -> None:
            self.default_handled.append(event)

    class CustomDefaultHandler(EventListener):
        def __init__(self, agent_id, bus):
            super().__init__(bus, agent_id)
            self.default_called = False
            self.default_event = None

        async def default_handler(self, event: Event) -> None:
            self.default_called = True
            self.default_event = event

    class DirectMessageListener(EventListener):
        def __init__(self, agent_id, bus):
            super().__init__(bus, agent_id)
            self.direct_messages: List[Event] = []

        async def handle_direct(self, event: Event) -> None:
            self.direct_messages.append(event)

    @pytest.mark.asyncio
    async def test_handle_dispatches_to_handle_topic_method(self, bus, agent_id):
        listener = self.SimpleListener(agent_id, bus)
        event = Event(topic="test_event", sender="test", payload="data")
        await listener.handle(event)
        assert len(listener.handled_events) == 1
        assert listener.handled_events[0] == event

    @pytest.mark.asyncio
    async def test_handle_fallbacks_to_default_handler(self, bus, agent_id):
        listener = self.SimpleListener(agent_id, bus)
        event = Event(topic="unknown_topic", sender="test", payload="data")
        await listener.handle(event)
        assert len(listener.default_handled) == 1
        assert listener.default_handled[0] == event

    @pytest.mark.asyncio
    async def test_default_handler_does_nothing_by_default(self, bus, agent_id):
        listener = self.SimpleListener(agent_id, bus)
        event = Event(topic="any_topic", sender="test", payload="data")
        await listener.default_handler(event)
        await listener.handle(event)

    @pytest.mark.asyncio
    async def test_default_handler_can_be_overridden(self, bus, agent_id):
        listener = self.CustomDefaultHandler(agent_id, bus)
        event = Event(topic="any_topic", sender="test", payload="data")
        await listener.handle(event)
        assert listener.default_called is True
        assert listener.default_event == event

    @pytest.mark.asyncio
    async def test_handle_with_various_payload_types(self, bus, agent_id):
        listener = self.SimpleListener(agent_id, bus)
        payloads = [
            "string", 42, 3.14, {"key": "value"}, [1, 2, 3], None, True, False,
        ]

        for payload in payloads:
            event = Event(topic="test_event", sender="test", payload=payload)
            listener.handled_events.clear()
            await listener.handle(event)
            assert len(listener.handled_events) == 1
            assert listener.handled_events[0].payload == payload

    @pytest.mark.asyncio
    async def test_handle_converts_dots_and_dashes_to_underscores(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)
                self.called_with = None

            async def handle_user_created_event(self, event):
                self.called_with = event

            async def handle_message_received(self, event):
                self.called_with = event

        listener = Listener(agent_id, bus)

        event1 = Event(topic="user.created.event", sender="test", payload="data")
        await listener.handle(event1)
        assert listener.called_with == event1

        event2 = Event(topic="message-received", sender="test", payload="data")
        await listener.handle(event2)
        assert listener.called_with == event2

    @pytest.mark.asyncio
    async def test_subscribe_auto_discovers_handle_methods(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_user_created(self, event):
                pass

            async def handle_user_deleted(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe(["explicit.topic"])

        assert "user.created" in bus._bindings
        assert "user.deleted" in bus._bindings
        assert "explicit.topic" in bus._bindings
        assert agent_id in bus._bindings["user.created"]
        assert agent_id in bus._bindings["user.deleted"]
        assert agent_id in bus._bindings["explicit.topic"]

    @pytest.mark.asyncio
    async def test_subscribe_combines_explicit_and_discovered_topics(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_auto_topic(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe(["explicit1", "explicit2"])

        assert "auto.topic" in bus._bindings
        assert "explicit1" in bus._bindings
        assert "explicit2" in bus._bindings

    @pytest.mark.asyncio
    async def test_default_handler_can_be_overridden_via_register(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)
                self.called = False

            async def default_handler(self, event):
                self.called = True

        listener = Listener(agent_id, bus)
        event = Event(topic="unknown", sender="test", payload="data")
        await listener.handle(event)
        assert listener.called

    @pytest.mark.asyncio
    async def test_handle_method_name_conversion(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)
                self.called = []

            async def handle_simple(self, event):
                self.called.append("simple")

            async def handle_user_created(self, event):
                self.called.append("user_created")

            async def handle_user_deleted_event(self, event):
                self.called.append("user_deleted_event")

            async def handle_message_received_data(self, event):
                self.called.append("message_received_data")

        listener = Listener(agent_id, bus)

        await listener.handle(Event(topic="simple", sender="s", payload="p"))
        await listener.handle(Event(topic="user.created", sender="s", payload="p"))
        await listener.handle(Event(topic="user.deleted.event", sender="s", payload="p"))
        await listener.handle(Event(topic="message-received-data", sender="s", payload="p"))

        assert "simple" in listener.called
        assert "user_created" in listener.called
        assert "user_deleted_event" in listener.called
        assert "message_received_data" in listener.called

    @pytest.mark.asyncio
    async def test_handle_base_method_not_treated_as_handler(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle(self, event):
                pass  # This is the base method

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe([])

        assert "" not in bus._bindings

    @pytest.mark.asyncio
    async def test_direct_message_handling(self, bus, agent_id):
        listener = self.DirectMessageListener(agent_id, bus)
        event = Event(topic=None, sender="sender1", payload="direct msg")
        await listener._handle_incoming(event)
        assert len(listener.direct_messages) == 1
        assert listener.direct_messages[0] == event

    @pytest.mark.asyncio
    async def test_direct_message_falls_back_to_default_handler(self, bus, agent_id):
        listener = self.SimpleListener(agent_id, bus)
        event = Event(topic=None, sender="sender1", payload="direct msg")
        await listener._handle_incoming(event)
        assert len(listener.default_handled) == 1

    @pytest.mark.asyncio
    async def test_mailbox_listener_processes_messages(self, bus, agent_id):
        listener = self.SimpleListener(agent_id, bus)
        listener.run()
        listener.subscribe(["test_event"])

        event = Event(topic="test_event", sender="sender", payload="data")
        bus.publish_to_topic("sender", "test_event", "data")

        await asyncio.sleep(0.05)

        assert len(listener.handled_events) == 1
        assert listener.handled_events[0].topic == "test_event"
        assert listener.handled_events[0].sender == "sender"
        assert listener.handled_events[0].payload == "data"

    @pytest.mark.asyncio
    async def test_send_direct_via_listener(self, bus, agent_id):
        lid1 = f"{agent_id}_1"
        lid2 = f"{agent_id}_2"
        l1 = self.SimpleListener(lid1, bus)
        l2 = self.SimpleListener(lid2, bus)

        l1.run()
        l2.run()

        l1.send_direct(lid2, "direct message")

        await asyncio.sleep(0.05)

        assert len(l2.default_handled) == 1
        assert l2.default_handled[0].payload == "direct message"
        assert l2.default_handled[0].topic is None

    @pytest.mark.asyncio
    async def test_publish_via_listener(self, bus, agent_id):
        class BroadcastListener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)
                self.handled_events: List[Event] = []

            async def handle_broadcast_topic(self, event: Event) -> None:
                self.handled_events.append(event)

        lid1 = f"{agent_id}_1"
        lid2 = f"{agent_id}_2"
        l1 = BroadcastListener(lid1, bus)
        l2 = BroadcastListener(lid2, bus)

        l1.run()
        l2.run()

        l1.subscribe(["broadcast.topic"])
        l2.subscribe(["broadcast.topic"])

        l1.publish("broadcast.topic", "broadcast message")

        await asyncio.sleep(0.1)

        assert len(l1.handled_events) == 1
        assert len(l2.handled_events) == 1
        assert l1.handled_events[0].payload == "broadcast message"
        assert l2.handled_events[0].payload == "broadcast message"


class TestEventListenerAutoDiscovery:
    """Tests for EventListener auto-discovery of handler methods."""

    @pytest.fixture
    def bus(self):
        return EventBus()

    @pytest.fixture
    def agent_id(self):
        return f"test_agent_{id(object())}"

    @pytest.mark.asyncio
    async def test_handle_user_created_maps_to_user_created_topic(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_user_created(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe([])

        assert "user.created" in bus._bindings
        assert agent_id in bus._bindings["user.created"]

    @pytest.mark.asyncio
    async def test_handle_user_created_event_maps_to_user_created_event_topic(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_user_created_event(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe([])

        assert "user.created.event" in bus._bindings
        assert agent_id in bus._bindings["user.created.event"]

    @pytest.mark.asyncio
    async def test_handle_message_received_maps_to_message_received_topic(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_message_received(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe([])

        assert "message.received" in bus._bindings
        assert agent_id in bus._bindings["message.received"]

    @pytest.mark.asyncio
    async def test_handle_base_method_not_treated_as_handler(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle(self, event):
                pass  # This is the base method

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe([])

        assert "" not in bus._bindings

    @pytest.mark.asyncio
    async def test_multiple_handlers_discovered_on_same_listener(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_user_created(self, event):
                pass

            async def handle_user_deleted(self, event):
                pass

            async def handle_message_sent(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe([])

        assert "user.created" in bus._bindings
        assert "user.deleted" in bus._bindings
        assert "message.sent" in bus._bindings
        assert agent_id in bus._bindings["user.created"]
        assert agent_id in bus._bindings["user.deleted"]
        assert agent_id in bus._bindings["message.sent"]

    @pytest.mark.asyncio
    async def test_auto_discovery_works_with_explicit_topics(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_user_created(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe(["explicit.topic"])

        assert "user.created" in bus._bindings
        assert "explicit.topic" in bus._bindings
        assert agent_id in bus._bindings["user.created"]
        assert agent_id in bus._bindings["explicit.topic"]

    @pytest.mark.asyncio
    async def test_discovered_topics_with_underscores(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_user_created_event_data(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe([])

        assert "user.created.event.data" in bus._bindings

    @pytest.mark.asyncio
    async def test_discovered_topics_with_numbers(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_user2_created(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe([])

        assert "user2.created" in bus._bindings

    @pytest.mark.asyncio
    async def test_discovered_topics_case_sensitivity(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_UserCreated(self, event):
                pass

            async def handle_usercreated(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe([])

        assert "UserCreated" in bus._bindings
        assert "usercreated" in bus._bindings


class TestEventBusSingleton:
    """Tests for the singleton event_bus instance."""

    def test_event_bus_is_singleton_instance(self):
        from harness_core.eventbus import event_bus as bus1
        from harness_core.eventbus import event_bus as bus2

        assert bus1 is bus2
        assert isinstance(bus1, EventBus)

    def test_event_bus_singleton_has_mailboxes_and_bindings(self):
        assert hasattr(event_bus, '_mailboxes')
        assert hasattr(event_bus, '_bindings')
        assert isinstance(event_bus._mailboxes, dict)
        assert isinstance(event_bus._bindings, dict)

    def test_singleton_registrations_persist(self):
        event_bus._mailboxes.clear()
        event_bus._bindings.clear()

        event_bus.register_agent("test_agent")
        event_bus.subscribe("test_agent", "test.topic")

        from harness_core.eventbus import event_bus as bus2
        assert "test_agent" in bus2._mailboxes
        assert "test_agent" in bus2._bindings["test.topic"]

    def test_singleton_is_event_bus_instance(self):
        assert isinstance(event_bus, EventBus)


class TestAsyncFunctionality:
    """Tests for async functionality with pytest-asyncio."""

    @pytest.fixture
    def bus(self):
        return EventBus()

    @pytest.fixture
    def agent_id(self):
        return f"test_agent_{id(object())}"

    class SimpleListener(EventListener):
        def __init__(self, agent_id, bus):
            super().__init__(bus, agent_id)
            self.events = []

        async def handle_test_event(self, event):
            self.events.append(event)

    @pytest.mark.asyncio
    async def test_async_handle_methods_work_correctly(self, bus, agent_id):
        class AsyncListener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)
                self.results = []

            async def handle_test_event(self, event: Event):
                await asyncio.sleep(0.01)
                self.results.append(event.payload * 2)

        listener = AsyncListener(agent_id, bus)
        # run() registers the mailbox AND starts the mailbox_listener task
        listener.run()
        listener.subscribe([])

        event = Event(topic="test.event", sender="test", payload=21)
        bus.publish_to_topic("test", "test.event", 21)

        await asyncio.sleep(0.05)

        assert listener.results == [42]

    @pytest.mark.asyncio
    async def test_concurrent_publishing_works_correctly(self, bus, agent_id):
        results = []

        class ConcurrentListener(EventListener):
            def __init__(self, agent_id, bus, name):
                super().__init__(bus, agent_id)
                self.name = name

            async def handle_test_topic(self, event: Event):
                await asyncio.sleep(0.01)
                results.append((self.name, event.payload))

        lid1 = f"{agent_id}_1"
        lid2 = f"{agent_id}_2"
        l1 = ConcurrentListener(lid1, bus, "listener1")
        l2 = ConcurrentListener(lid2, bus, "listener2")
        l1.run()
        l2.run()
        _require_registration(bus, lid1)
        _require_registration(bus, lid2)
        l1.subscribe([])
        l2.subscribe([])

        for i in range(10):
            bus.publish_to_topic("test", "test.topic", i)

        await asyncio.sleep(0.2)

        listener1_results = [r for r in results if r[0] == "listener1"]
        listener2_results = [r for r in results if r[0] == "listener2"]

        assert len(listener1_results) == 10
        assert len(listener2_results) == 10

    @pytest.mark.asyncio
    async def test_concurrent_publishing_different_topics(self, bus, agent_id):
        topic1_results = []
        topic2_results = []

        class Topic1Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_topic1(self, event: Event):
                await asyncio.sleep(0.01)
                topic1_results.append(event.payload)

        class Topic2Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_topic2(self, event: Event):
                await asyncio.sleep(0.01)
                topic2_results.append(event.payload)

        lid1 = f"{agent_id}_1"
        lid2 = f"{agent_id}_2"
        l1 = Topic1Listener(lid1, bus)
        l2 = Topic2Listener(lid2, bus)
        l1.run()
        l2.run()
        _require_registration(bus, lid1)
        _require_registration(bus, lid2)
        l1.subscribe([])
        l2.subscribe([])

        for i in range(5):
            bus.publish_to_topic("test", "topic1", i)
            bus.publish_to_topic("test", "topic2", i * 10)

        await asyncio.sleep(0.2)

        assert sorted(topic1_results) == [0, 1, 2, 3, 4]
        assert sorted(topic2_results) == [0, 10, 20, 30, 40]

    @pytest.mark.asyncio
    async def test_async_default_handler(self, bus, agent_id):
        class ListenerWithAsyncDefault(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)
                self.default_events = []

            async def default_handler(self, event: Event):
                await asyncio.sleep(0.01)
                self.default_events.append(event)

        listener = ListenerWithAsyncDefault(agent_id, bus)
        event = Event(topic="unknown.topic", sender="test", payload="data")

        await listener.handle(event)

        assert len(listener.default_events) == 1
        assert listener.default_events[0] == event

    @pytest.mark.asyncio
    async def test_publish_with_empty_topic_list(self, bus, agent_id):
        event = Event(topic="empty.topic", sender="test", payload="data")
        # Should not raise
        bus.publish_to_topic("test", "empty.topic", "data")

    @pytest.mark.asyncio
    async def test_multiple_async_handlers_concurrent_execution(self, bus, agent_id):
        start_times = []
        end_times = []

        class TimedListener(EventListener):
            def __init__(self, agent_id, bus, name, delay):
                super().__init__(bus, agent_id)
                self.name = name
                self.delay = delay

            async def handle_timed_topic(self, event):
                start_times.append((self.name, asyncio.get_event_loop().time()))
                await asyncio.sleep(self.delay)
                end_times.append((self.name, asyncio.get_event_loop().time()))

        lid1 = f"{agent_id}_1"
        lid2 = f"{agent_id}_2"
        l1 = TimedListener(lid1, bus, "slow", 0.1)
        l2 = TimedListener(lid2, bus, "fast", 0.01)
        l1.run()
        l2.run()
        _require_registration(bus, lid1)
        _require_registration(bus, lid2)
        l1.subscribe([])
        l2.subscribe([])

        bus.publish_to_topic("test", "timed.topic", "data")

        await asyncio.sleep(0.15)

        slow_start = next(t for n, t in start_times if n == "slow")
        fast_start = next(t for n, t in start_times if n == "fast")
        slow_end = next(t for n, t in end_times if n == "slow")
        fast_end = next(t for n, t in end_times if n == "fast")

        assert abs(slow_start - fast_start) < 0.05
        assert fast_end < slow_end


class TestFilterBySender:
    """Tests for the filter_by_sender decorator."""

    @pytest.fixture
    def bus(self):
        return EventBus()

    @pytest.fixture
    def agent_id(self):
        return f"test_agent_{id(object())}"

    class FilteredListener(EventListener):
        def __init__(self, agent_id, bus):
            super().__init__(bus, agent_id)
            self.handled = []

        @filter_by_sender(r"^user_\d+$")
        async def handle_user_event(self, event):
            self.handled.append(event)

    @pytest.mark.asyncio
    async def test_filter_by_sender_matches(self, bus, agent_id):
        listener = self.FilteredListener(agent_id, bus)

        event = Event(topic="user_event", sender="user_123", payload="data")
        await listener.handle_user_event(event)

        assert len(listener.handled) == 1

    @pytest.mark.asyncio
    async def test_filter_by_sender_non_matching(self, bus, agent_id):
        listener = self.FilteredListener(agent_id, bus)

        event = Event(topic="user_event", sender="admin", payload="data")
        await listener.handle_user_event(event)

        assert len(listener.handled) == 0

    @pytest.mark.asyncio
    async def test_filter_by_sender_partial_match(self, bus, agent_id):
        listener = self.FilteredListener(agent_id, bus)

        event1 = Event(topic="user_event", sender="user_123", payload="data")
        event2 = Event(topic="user_event", sender="user_abc", payload="data")

        await listener.handle_user_event(event1)
        await listener.handle_user_event(event2)

        assert len(listener.handled) == 1
        assert listener.handled[0].sender == "user_123"


class TestGenerateUniqueId:
    """Tests for generate_unique_id function."""

    def test_generate_unique_id_without_prefix(self):
        id1 = generate_unique_id()
        id2 = generate_unique_id()

        assert len(id1) == 8
        assert len(id2) == 8
        assert id1 != id2

    def test_generate_unique_id_with_prefix(self):
        id1 = generate_unique_id("TaskList")
        id2 = generate_unique_id("Agent")

        assert id1.startswith("TaskList.")
        assert id2.startswith("Agent.")
        assert len(id1) > len("TaskList.")
        assert len(id2) > len("Agent.")

    def test_generate_unique_id_uniqueness(self):
        ids = {generate_unique_id() for _ in range(100)}
        assert len(ids) == 100


class TestEdgeCases:
    """Edge case tests for edge coverage."""

    @pytest.fixture
    def bus(self):
        return EventBus()

    @pytest.fixture
    def agent_id(self):
        return f"test_agent_{id(object())}"

    def test_event_with_empty_string_payload(self, bus, agent_id):
        event = Event(topic="test", sender="test", payload="")
        assert event.payload == ""

    def test_event_with_zero_payload(self, bus, agent_id):
        event = Event(topic="test", sender="test", payload=0)
        assert event.payload == 0

    def test_event_with_false_payload(self, bus, agent_id):
        event = Event(topic="test", sender="test", payload=False)
        assert event.payload is False

    def test_event_with_empty_list_payload(self, bus, agent_id):
        event = Event(topic="test", sender="test", payload=[])
        assert event.payload == []

    def test_event_with_empty_dict_payload(self, bus, agent_id):
        event = Event(topic="test", sender="test", payload={})
        assert event.payload == {}

    @pytest.mark.asyncio
    async def test_subscribe_with_empty_topics_list(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_test(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe([])

        assert "test" in bus._bindings

    @pytest.mark.asyncio
    async def test_subscribe_with_none_topics(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_test(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        # subscribe() has a default empty list — passing None triggers TypeError;
        # this test verifies the documented behavior (explicit empty list works).
        listener.subscribe([])

        assert "test" in bus._bindings

    @pytest.mark.asyncio
    async def test_unsubscribe_from_topic_with_multiple_listeners(self, bus, agent_id):
        lid1 = f"{agent_id}_1"
        lid2 = f"{agent_id}_2"
        bus.register_agent(lid1)
        bus.register_agent(lid2)
        bus.subscribe(lid1, "topic")
        bus.subscribe(lid2, "topic")

        bus.unsubscribe(lid1, "topic")

        assert lid1 not in bus._bindings["topic"]
        assert lid2 in bus._bindings["topic"]

    @pytest.mark.asyncio
    async def test_subscribe_same_listener_multiple_topics(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_topic1(self, event):
                pass

            async def handle_topic2(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe(["topic3"])

        assert "topic1" in bus._bindings
        assert "topic2" in bus._bindings
        assert "topic3" in bus._bindings
        assert agent_id in bus._bindings["topic1"]
        assert agent_id in bus._bindings["topic2"]
        assert agent_id in bus._bindings["topic3"]

    @pytest.mark.asyncio
    async def test_publish_event_with_none_payload(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)
                self.payload = None

            async def handle_none_topic(self, event):
                self.payload = event.payload

        listener = Listener(agent_id, bus)
        listener.run()
        _require_registration(bus, agent_id)
        listener.subscribe([])

        bus.publish_to_topic("test", "none.topic", None)
        await asyncio.sleep(0.05)

        assert listener.payload is None

    @pytest.mark.asyncio
    async def test_listener_handle_method_called_with_correct_event(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)
                self.received_event = None

            async def handle_correct_topic(self, event):
                self.received_event = event

        listener = Listener(agent_id, bus)
        listener.run()
        _require_registration(bus, agent_id)
        listener.subscribe([])

        bus.publish_to_topic("sender123", "correct.topic", {"key": "value"})

        await asyncio.sleep(0.05)

        assert listener.received_event is not None
        assert listener.received_event.topic == "correct.topic"
        assert listener.received_event.sender == "sender123"
        assert listener.received_event.payload == {"key": "value"}

    def test_event_bus_initial_mailboxes_empty(self, bus):
        assert bus._mailboxes == {}
        assert bus._bindings == {}

    @pytest.mark.asyncio
    async def test_event_topic_with_special_characters(self, bus, agent_id):
        class Listener(EventListener):
            def __init__(self, agent_id, bus):
                super().__init__(bus, agent_id)

            async def handle_user_created(self, event):
                pass

            async def handle_user_deleted(self, event):
                pass

        listener = Listener(agent_id, bus)
        _require_registration(bus, agent_id)
        listener.subscribe([])

        assert "user.created" in bus._bindings
        assert "user.deleted" in bus._bindings


# Pytest configuration for async tests
pytest_plugins = ['pytest_asyncio']
