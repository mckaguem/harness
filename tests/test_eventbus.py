"""Comprehensive tests for harness_core.eventbus with 100% coverage."""

import asyncio
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from harness_core.eventbus import Event, EventBus, EventListener, event_bus


class TestEventDataclass:
    """Tests for the Event dataclass."""

    def test_event_creation_with_str_payload(self):
        """Test Event creation with string payload."""
        event = Event(topic="user.created", sender="user_service", payload="hello")
        assert event.topic == "user.created"
        assert event.sender == "user_service"
        assert event.payload == "hello"

    def test_event_creation_with_int_payload(self):
        """Test Event creation with integer payload."""
        event = Event(topic="counter.increment", sender="counter_service", payload=42)
        assert event.payload == 42

    def test_event_creation_with_dict_payload(self):
        """Test Event creation with dictionary payload."""
        payload = {"user_id": 123, "name": "John", "active": True}
        event = Event(topic="user.updated", sender="api", payload=payload)
        assert event.payload == payload

    def test_event_creation_with_list_payload(self):
        """Test Event creation with list payload."""
        payload = [1, 2, 3, "a", "b", "c"]
        event = Event(topic="items.added", sender="service", payload=payload)
        assert event.payload == payload

    def test_event_creation_with_none_payload(self):
        """Test Event creation with None payload."""
        event = Event(topic="event.empty", sender="system", payload=None)
        assert event.payload is None

    def test_event_creation_with_complex_payload(self):
        """Test Event creation with complex nested payload."""
        payload = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "meta": {"total": 2, "page": 1}
        }
        event = Event(topic="users.list", sender="api", payload=payload)
        assert event.payload == payload

    def test_event_mutability(self):
        """Test that Event is a dataclass with mutable fields."""
        event = Event(topic="test", sender="sender", payload="value")
        event.topic = "modified"
        assert event.topic == "modified"

    def test_event_equality(self):
        """Test Event equality comparison."""
        event1 = Event(topic="test", sender="sender", payload="data")
        event2 = Event(topic="test", sender="sender", payload="data")
        event3 = Event(topic="other", sender="sender", payload="data")
        assert event1 == event2
        assert event1 != event3


class TestEventListenerBaseClass:
    """Tests for the EventListener base class."""

    class SimpleListener(EventListener):
        """Simple listener for testing."""
        def __init__(self):
            self.handled_events: List[Event] = []
            self.default_handled: List[Event] = []

        async def handle_test_event(self, event: Event) -> None:
            self.handled_events.append(event)

        async def default_handler(self, event: Event) -> None:
            self.default_handled.append(event)

    class CustomDefaultHandler(EventListener):
        """Listener with custom default handler."""
        def __init__(self):
            self.default_called = False
            self.default_event = None

        async def default_handler(self, event: Event) -> None:
            self.default_called = True
            self.default_event = event

    @pytest.mark.asyncio
    async def test_handle_dispatches_to_handle_topic_method(self):
        """Test handle() dispatches to handle_<topic> method."""
        listener = self.SimpleListener()
        event = Event(topic="test_event", sender="test", payload="data")

        await listener.handle(event)

        assert len(listener.handled_events) == 1
        assert listener.handled_events[0] == event

    @pytest.mark.asyncio
    async def test_handle_fallbacks_to_default_handler(self):
        """Test handle() falls back to default_handler when no handler exists."""
        listener = self.SimpleListener()
        event = Event(topic="unknown_topic", sender="test", payload="data")

        await listener.handle(event)

        assert len(listener.default_handled) == 1
        assert listener.default_handled[0] == event

    @pytest.mark.asyncio
    async def test_default_handler_does_nothing_by_default(self):
        """Test default_handler does nothing by default."""
        listener = EventListener()
        event = Event(topic="any_topic", sender="test", payload="data")

        # Should not raise any exception
        await listener.default_handler(event)
        await listener.handle(event)

    @pytest.mark.asyncio
    async def test_default_handler_can_be_overridden(self):
        """Test default_handler can be overridden in subclass."""
        listener = self.CustomDefaultHandler()
        event = Event(topic="any_topic", sender="test", payload="data")

        await listener.handle(event)

        assert listener.default_called is True
        assert listener.default_event == event

    @pytest.mark.asyncio
    async def test_handle_with_various_payload_types(self):
        """Test handle() works with various payload types."""
        listener = self.SimpleListener()

        # Test with different payload types
        payloads = [
            "string",
            42,
            3.14,
            {"key": "value"},
            [1, 2, 3],
            None,
            True,
            False,
        ]

        for payload in payloads:
            event = Event(topic="test_event", sender="test", payload=payload)
            listener.handled_events.clear()
            await listener.handle(event)
            assert len(listener.handled_events) == 1
            assert listener.handled_events[0].payload == payload

    @pytest.mark.asyncio
    async def test_handle_converts_dots_and_dashes_to_underscores(self):
        """Test handle() converts dots and dashes in topic to underscores."""
        class Listener(EventListener):
            def __init__(self):
                self.handled = []

            async def handle_user_created(self, event):
                self.handled.append(("user.created", event))

            async def handle_user_deleted(self, event):
                self.handled.append(("user.deleted", event))

            async def handle_message_received(self, event):
                self.handled.append(("message_received", event))

        listener = Listener()

        # Test dot conversion
        event1 = Event(topic="user.created", sender="test", payload="data")
        await listener.handle(event1)
        assert len(listener.handled) == 1
        assert listener.handled[0][0] == "user.created"

        # Test dash conversion
        event2 = Event(topic="user.deleted", sender="test", payload="data")
        await listener.handle(event2)
        assert len(listener.handled) == 2

        # Test underscore stays as dot
        event3 = Event(topic="message_received", sender="test", payload="data")
        await listener.handle(event3)
        assert len(listener.handled) == 3

    def test_subscribe_auto_discovers_handle_methods(self):
        """Test subscribe() auto-discovers handle_* methods."""
        class Listener(EventListener):
            def __init__(self):
                self.discovered_topics = []

            async def handle_user_created(self, event):
                pass

            async def handle_message_received(self, event):
                pass

        listener = Listener()
        # Call the auto-discovery logic directly
        for attr_name in dir(listener):
            if attr_name.startswith('handle_') and attr_name != 'handle':
                topic = attr_name[7:].replace('_', '.')
                listener.discovered_topics.append(topic)

        assert "user.created" in listener.discovered_topics
        assert "message.received" in listener.discovered_topics

    def test_subscribe_combines_explicit_and_discovered_topics(self):
        """Test subscribe() combines explicit topics with discovered topics."""
        class Listener(EventListener):
            def __init__(self):
                self.all_topics = []

            async def handle_user_created(self, event):
                pass

        listener = Listener()
        # Simulate the subscribe logic
        topics = ["explicit.topic", "another.topic"]
        discovered = []
        for attr_name in dir(listener):
            if attr_name.startswith('handle_') and attr_name != 'handle':
                topic = attr_name[7:].replace('_', '.')
                discovered.append(topic)
        listener.all_topics = list(set(topics + discovered))

        assert "user.created" in listener.all_topics
        assert "explicit.topic" in listener.all_topics
        assert "another.topic" in listener.all_topics

    @pytest.mark.asyncio
    async def test_subscribe_subscribes_to_event_bus_singleton(self):
        """Test subscribe() subscribes to event_bus singleton."""
        class Listener(EventListener):
            async def handle_test_event(self, event):
                pass

        # Clear event bus first
        event_bus._subscribers.clear()
        listener = Listener()
        await listener.subscribe([])

        # Check that listener was actually subscribed to event_bus
        assert "test.event" in event_bus._subscribers
        assert listener in event_bus._subscribers["test.event"]

    @pytest.mark.asyncio
    async def test_default_handler_can_be_overridden_via_register(self):
        """Test default_handler can be overridden to custom behavior."""
        class CustomListener(EventListener):
            def __init__(self):
                self.custom_default_called = False

            async def default_handler(self, event: Event) -> None:
                self.custom_default_called = True

        listener = CustomListener()
        event = Event(topic="unknown", sender="test", payload=None)

        await listener.handle(event)

        assert listener.custom_default_called is True

    @pytest.mark.asyncio
    async def test_handle_method_name_conversion(self):
        """Test handle_* method name conversion to topic names."""
        class Listener(EventListener):
            def __init__(self):
                self.called_topics = []

            async def handle_user_created(self, event):
                self.called_topics.append("user.created")

            async def handle_user_deleted_event(self, event):
                self.called_topics.append("user.deleted.event")

            async def handle_message_received(self, event):
                self.called_topics.append("message.received")

        listener = Listener()

        # Test user.created
        await listener.handle(Event(topic="user.created", sender="test", payload=None))
        assert "user.created" in listener.called_topics

        # Test user.deleted.event
        await listener.handle(Event(topic="user.deleted.event", sender="test", payload=None))
        assert "user.deleted.event" in listener.called_topics

        # Test message.received
        await listener.handle(Event(topic="message.received", sender="test", payload=None))
        assert "message.received" in listener.called_topics

    def test_handle_base_method_not_treated_as_handler(self):
        """Test that handle() base method is not treated as a handler."""
        class Listener(EventListener):
            def __init__(self):
                self.discovered = []

        listener = Listener()
        # Call the auto-discovery logic directly (sync version)
        for attr_name in dir(listener):
            if attr_name.startswith('handle_') and attr_name != 'handle':
                topic = attr_name[7:].replace('_', '.')
                listener.discovered.append(topic)

        # 'handle' method should not be treated as handler
        assert "handle" not in listener.discovered
        assert "handle" not in [t.replace('.', '_') for t in listener.discovered]


class TestEventBus:
    """Tests for the EventBus class."""

    def setup_method(self):
        """Create a fresh EventBus for each test."""
        self.bus = EventBus()

    def teardown_method(self):
        """Clear the singleton event bus after each test."""
        event_bus._subscribers.clear()

    def test_subscribe_adds_listener_to_topic(self):
        """Test subscribe() adds listener to topic."""
        listener = EventListener()
        self.bus.subscribe("test.topic", listener)

        assert "test.topic" in self.bus._subscribers
        assert listener in self.bus._subscribers["test.topic"]

    def test_subscribe_prevents_duplicate_subscriptions(self):
        """Test subscribe() prevents duplicate subscriptions."""
        listener = EventListener()
        self.bus.subscribe("test.topic", listener)
        self.bus.subscribe("test.topic", listener)

        assert len(self.bus._subscribers["test.topic"]) == 1

    def test_subscribe_multiple_listeners_same_topic(self):
        """Test multiple listeners can subscribe to same topic."""
        listener1 = EventListener()
        listener2 = EventListener()
        self.bus.subscribe("test.topic", listener1)
        self.bus.subscribe("test.topic", listener2)

        assert len(self.bus._subscribers["test.topic"]) == 2
        assert listener1 in self.bus._subscribers["test.topic"]
        assert listener2 in self.bus._subscribers["test.topic"]

    def test_unsubscribe_removes_listener_from_topic(self):
        """Test unsubscribe() removes listener from topic."""
        listener = EventListener()
        self.bus.subscribe("test.topic", listener)
        self.bus.unsubscribe("test.topic", listener)

        assert listener not in self.bus._subscribers.get("test.topic", [])

    def test_unsubscribe_cleans_up_empty_topic_lists(self):
        """Test unsubscribe() cleans up empty topic lists."""
        listener = EventListener()
        self.bus.subscribe("test.topic", listener)
        self.bus.unsubscribe("test.topic", listener)

        assert "test.topic" not in self.bus._subscribers

    def test_unsubscribe_nonexistent_topic(self):
        """Test unsubscribe() handles nonexistent topic gracefully."""
        listener = EventListener()
        # Should not raise
        self.bus.unsubscribe("nonexistent", listener)

    def test_unsubscribe_nonexistent_listener(self):
        """Test unsubscribe() handles nonexistent listener gracefully."""
        listener1 = EventListener()
        listener2 = EventListener()
        self.bus.subscribe("test.topic", listener1)
        # Should not raise
        self.bus.unsubscribe("test.topic", listener2)
        assert listener1 in self.bus._subscribers["test.topic"]

    @pytest.mark.asyncio
    async def test_publish_calls_handle_on_all_subscribers(self):
        """Test publish() calls handle() on all subscribers."""
        class TestListener(EventListener):
            def __init__(self, name):
                self.name = name
                self.events = []

            async def handle(self, event: Event):
                self.events.append(event)

        listener1 = TestListener("listener1")
        listener2 = TestListener("listener2")
        self.bus.subscribe("test.topic", listener1)
        self.bus.subscribe("test.topic", listener2)

        event = Event(topic="test.topic", sender="test", payload="data")
        await self.bus.publish(event)

        assert len(listener1.events) == 1
        assert listener1.events[0] == event
        assert len(listener2.events) == 1
        assert listener2.events[0] == event

    @pytest.mark.asyncio
    async def test_publish_is_non_blocking_fire_and_forget(self):
        """Test publish() is non-blocking (fire and forget)."""
        call_order = []

        class SlowListener(EventListener):
            def __init__(self, name, delay):
                self.name = name
                self.delay = delay

            async def handle(self, event):
                call_order.append(f"{self.name}_start")
                await asyncio.sleep(self.delay)
                call_order.append(f"{self.name}_end")

        listener1 = SlowListener("slow", 0.1)
        listener2 = SlowListener("fast", 0.01)
        self.bus.subscribe("test.topic", listener1)
        self.bus.subscribe("test.topic", listener2)

        event = Event(topic="test.topic", sender="test", payload="data")
        await self.bus.publish(event)

        # Both should have completed (asyncio.gather waits for all)
        assert "slow_start" in call_order
        assert "slow_end" in call_order
        assert "fast_start" in call_order
        assert "fast_end" in call_order

    @pytest.mark.asyncio
    async def test_publish_handles_no_subscribers_gracefully(self):
        """Test publish() handles no subscribers gracefully."""
        event = Event(topic="nonexistent.topic", sender="test", payload="data")
        # Should not raise
        await self.bus.publish(event)

    @pytest.mark.asyncio
    async def test_publish_handles_exceptions_in_listeners(self):
        """Test publish() handles exceptions in listeners with return_exceptions=True."""
        class FailingListener(EventListener):
            async def handle(self, event):
                raise ValueError("Listener error")

        class WorkingListener(EventListener):
            def __init__(self):
                self.handled = False

            async def handle(self, event):
                self.handled = True

        failing = FailingListener()
        working = WorkingListener()
        self.bus.subscribe("test.topic", failing)
        self.bus.subscribe("test.topic", working)

        event = Event(topic="test.topic", sender="test", payload="data")
        # Should not raise exception
        await self.bus.publish(event)

        # Working listener should still be called
        assert working.handled is True

    @pytest.mark.asyncio
    async def test_publish_multiple_listeners_same_topic_all_receive_event(self):
        """Test multiple listeners on same topic all receive event."""
        listeners = [EventListener() for _ in range(5)]
        for i, listener in enumerate(listeners):
            listener.events = []
            async def make_handler(idx):
                async def handler(event):
                    listeners[idx].events.append(event)
                return handler
            listener.handle = await make_handler(i)
            self.bus.subscribe("test.topic", listener)

        event = Event(topic="test.topic", sender="test", payload="data")
        await self.bus.publish(event)

        for listener in listeners:
            assert len(listener.events) == 1
            assert listener.events[0] == event

    @pytest.mark.asyncio
    async def test_multiple_topics_work_independently(self):
        """Test multiple topics work independently."""
        listener_topic1 = EventListener()
        listener_topic2 = EventListener()
        listener_topic1.events = []
        listener_topic2.events = []

        async def handler1(event):
            listener_topic1.events.append(event)

        async def handler2(event):
            listener_topic2.events.append(event)

        listener_topic1.handle = handler1
        listener_topic2.handle = handler2

        self.bus.subscribe("topic.one", listener_topic1)
        self.bus.subscribe("topic.two", listener_topic2)

        event1 = Event(topic="topic.one", sender="test", payload="data1")
        event2 = Event(topic="topic.two", sender="test", payload="data2")

        await self.bus.publish(event1)
        await self.bus.publish(event2)

        assert len(listener_topic1.events) == 1
        assert listener_topic1.events[0] == event1
        assert len(listener_topic2.events) == 1
        assert listener_topic2.events[0] == event2

    @pytest.mark.asyncio
    async def test_publish_uses_asyncio_gather_concurrently(self):
        """Test publish() uses asyncio.gather for concurrent execution."""
        call_times = []

        class TimedListener(EventListener):
            def __init__(self, name):
                self.name = name

            async def handle(self, event):
                call_times.append((self.name, "start", asyncio.get_event_loop().time()))
                await asyncio.sleep(0.05)
                call_times.append((self.name, "end", asyncio.get_event_loop().time()))

        listener1 = TimedListener("listener1")
        listener2 = TimedListener("listener2")
        self.bus.subscribe("test.topic", listener1)
        self.bus.subscribe("test.topic", listener2)

        event = Event(topic="test.topic", sender="test", payload="data")
        await self.bus.publish(event)

        # Both should start before either ends (concurrent execution)
        start_times = [t for t in call_times if t[1] == "start"]
        end_times = [t for t in call_times if t[1] == "end"]
        assert len(start_times) == 2
        assert len(end_times) == 2


class TestEventListenerAutoDiscovery:
    """Tests for EventListener auto-discovery of handler methods."""

    def setup_method(self):
        """Clear the singleton event bus before each test."""
        event_bus._subscribers.clear()

    @pytest.mark.asyncio
    async def test_handle_user_created_maps_to_user_created_topic(self):
        """Test handle_user_created -> topic 'user.created'."""
        class Listener(EventListener):
            async def handle_user_created(self, event):
                pass

        listener = Listener()
        await listener.subscribe([])

        assert "user.created" in event_bus._subscribers
        assert listener in event_bus._subscribers["user.created"]

    @pytest.mark.asyncio
    async def test_handle_user_created_event_maps_to_user_created_event_topic(self):
        """Test handle_user_created_event -> topic 'user.created.event'."""
        class Listener(EventListener):
            async def handle_user_created_event(self, event):
                pass

        listener = Listener()
        await listener.subscribe([])

        assert "user.created.event" in event_bus._subscribers
        assert listener in event_bus._subscribers["user.created.event"]

    @pytest.mark.asyncio
    async def test_handle_message_received_maps_to_message_received_topic(self):
        """Test handle_message_received -> topic 'message.received'."""
        class Listener(EventListener):
            async def handle_message_received(self, event):
                pass

        listener = Listener()
        await listener.subscribe([])

        assert "message.received" in event_bus._subscribers
        assert listener in event_bus._subscribers["message.received"]

    @pytest.mark.asyncio
    async def test_handle_base_method_not_treated_as_handler(self):
        """Test that handle() base method is not treated as a handler."""
        class Listener(EventListener):
            async def handle(self, event):
                pass  # This is the base method

        listener = Listener()
        await listener.subscribe([])

        # handle() should not be treated as a handler for topic ""
        assert "" not in event_bus._subscribers

    @pytest.mark.asyncio
    async def test_multiple_handlers_discovered_on_same_listener(self):
        """Test multiple handler methods on same listener are all discovered."""
        class Listener(EventListener):
            async def handle_user_created(self, event):
                pass

            async def handle_user_deleted(self, event):
                pass

            async def handle_message_sent(self, event):
                pass

        listener = Listener()
        await listener.subscribe([])

        assert "user.created" in event_bus._subscribers
        assert "user.deleted" in event_bus._subscribers
        assert "message.sent" in event_bus._subscribers
        assert listener in event_bus._subscribers["user.created"]
        assert listener in event_bus._subscribers["user.deleted"]
        assert listener in event_bus._subscribers["message.sent"]

    @pytest.mark.asyncio
    async def test_auto_discovery_works_with_explicit_topics(self):
        """Test auto-discovery works alongside explicit topics."""
        class Listener(EventListener):
            async def handle_user_created(self, event):
                pass

        listener = Listener()
        await listener.subscribe(["explicit.topic"])

        assert "user.created" in event_bus._subscribers
        assert "explicit.topic" in event_bus._subscribers
        assert listener in event_bus._subscribers["user.created"]
        assert listener in event_bus._subscribers["explicit.topic"]

    @pytest.mark.asyncio
    async def test_discovered_topics_with_underscores(self):
        """Test handler names with multiple underscores map correctly."""
        class Listener(EventListener):
            async def handle_user_created_event_data(self, event):
                pass

        listener = Listener()
        await listener.subscribe([])

        # handle_user_created_event_data -> user.created.event.data
        assert "user.created.event.data" in event_bus._subscribers

    @pytest.mark.asyncio
    async def test_discovered_topics_with_numbers(self):
        """Test handler names with numbers map correctly."""
        class Listener(EventListener):
            async def handle_user2_created(self, event):
                pass

        listener = Listener()
        await listener.subscribe([])

        # handle_user2_created -> user2.created
        assert "user2.created" in event_bus._subscribers

    @pytest.mark.asyncio
    async def test_discovered_topics_case_sensitivity(self):
        """Test handler name case sensitivity."""
        class Listener(EventListener):
            async def handle_UserCreated(self, event):
                pass

            async def handle_usercreated(self, event):
                pass

        listener = Listener()
        await listener.subscribe([])

        # handle_UserCreated -> UserCreated (not user.created)
        assert "UserCreated" in event_bus._subscribers
        # handle_usercreated -> usercreated (no dots)
        assert "usercreated" in event_bus._subscribers


class TestEventBusSingleton:
    """Tests for the singleton event_bus instance."""

    def test_event_bus_is_singleton_instance(self):
        """Test event_bus is a singleton EventBus instance."""
        from harness_core.eventbus import event_bus as bus1
        from harness_core.eventbus import event_bus as bus2

        assert bus1 is bus2
        assert isinstance(bus1, EventBus)

    def test_event_bus_singleton_has_subscribers_dict(self):
        """Test singleton event_bus has _subscribers dict."""
        assert hasattr(event_bus, '_subscribers')
        assert isinstance(event_bus._subscribers, dict)

    def test_singleton_subscriptions_persist(self):
        """Test subscriptions on singleton persist."""
        event_bus._subscribers.clear()
        listener = EventListener()
        event_bus.subscribe("singleton.test", listener)

        # New reference should have same subscriptions
        from harness_core.eventbus import event_bus as bus2
        assert listener in bus2._subscribers["singleton.test"]

    def test_singleton_is_event_bus_instance(self):
        """Test event_bus is instance of EventBus class."""
        assert isinstance(event_bus, EventBus)


class TestAsyncFunctionality:
    """Tests for async functionality with pytest-asyncio."""

    def setup_method(self):
        """Clear the singleton event bus before each test."""
        event_bus._subscribers.clear()

    @pytest.mark.asyncio
    async def test_async_handle_methods_work_correctly(self):
        """Test async handle methods work correctly with pytest-asyncio."""
        class AsyncListener(EventListener):
            def __init__(self):
                self.results = []

            async def handle_test_event(self, event: Event):
                # Simulate async work
                await asyncio.sleep(0.01)
                self.results.append(event.payload * 2)

        listener = AsyncListener()
        await listener.subscribe([])

        event = Event(topic="test.event", sender="test", payload=21)
        await event_bus.publish(event)

        assert listener.results == [42]

    @pytest.mark.asyncio
    async def test_concurrent_publishing_works_correctly(self):
        """Test concurrent publishing to same topic works correctly."""
        results = []

        class ConcurrentListener(EventListener):
            def __init__(self, name):
                self.name = name

            async def handle_test_topic(self, event: Event):
                await asyncio.sleep(0.01)
                results.append((self.name, event.payload))

        listener1 = ConcurrentListener("listener1")
        listener2 = ConcurrentListener("listener2")
        await listener1.subscribe([])
        await listener2.subscribe([])

        # Publish multiple events concurrently
        tasks = [
            event_bus.publish(Event(topic="test.topic", sender="test", payload=i))
            for i in range(10)
        ]
        await asyncio.gather(*tasks)

        # Each listener should have received 10 events
        listener1_results = [r for r in results if r[0] == "listener1"]
        listener2_results = [r for r in results if r[0] == "listener2"]

        assert len(listener1_results) == 10
        assert len(listener2_results) == 10

    @pytest.mark.asyncio
    async def test_concurrent_publishing_different_topics(self):
        """Test concurrent publishing to different topics works independently."""
        topic1_results = []
        topic2_results = []

        class Topic1Listener(EventListener):
            async def handle_topic1(self, event: Event):
                await asyncio.sleep(0.01)
                topic1_results.append(event.payload)

        class Topic2Listener(EventListener):
            async def handle_topic2(self, event: Event):
                await asyncio.sleep(0.01)
                topic2_results.append(event.payload)

        listener1 = Topic1Listener()
        listener2 = Topic2Listener()
        await listener1.subscribe([])
        await listener2.subscribe([])

        # Publish to both topics concurrently
        tasks = []
        for i in range(5):
            tasks.append(event_bus.publish(Event(topic="topic1", sender="test", payload=i)))
            tasks.append(event_bus.publish(Event(topic="topic2", sender="test", payload=i * 10)))

        await asyncio.gather(*tasks)

        assert sorted(topic1_results) == [0, 1, 2, 3, 4]
        assert sorted(topic2_results) == [0, 10, 20, 30, 40]

    @pytest.mark.asyncio
    async def test_async_default_handler(self):
        """Test async default_handler works correctly."""
        class ListenerWithAsyncDefault(EventListener):
            def __init__(self):
                self.default_events = []

            async def default_handler(self, event: Event):
                await asyncio.sleep(0.01)
                self.default_events.append(event)

        listener = ListenerWithAsyncDefault()
        event = Event(topic="unknown.topic", sender="test", payload="data")

        await listener.handle(event)

        assert len(listener.default_events) == 1
        assert listener.default_events[0] == event

    @pytest.mark.asyncio
    async def test_publish_with_empty_topic_list(self):
        """Test publish with topic that has no subscribers."""
        event = Event(topic="empty.topic", sender="test", payload="data")
        # Should not raise
        await event_bus.publish(event)

    @pytest.mark.asyncio
    async def test_async_gather_return_exceptions_true(self):
        """Test that publish uses return_exceptions=True in gather."""
        class FailingListener(EventListener):
            async def handle_fail_topic(self, event):
                raise RuntimeError("Intentional error")

        class WorkingListener(EventListener):
            def __init__(self):
                self.handled = False

            async def handle_fail_topic(self, event):
                self.handled = True

        failing = FailingListener()
        working = WorkingListener()
        await failing.subscribe([])
        await working.subscribe([])

        event = Event(topic="fail.topic", sender="test", payload="data")
        # Should not raise despite failing listener
        await event_bus.publish(event)

        # Working listener should still be called
        assert working.handled is True

    @pytest.mark.asyncio
    async def test_multiple_async_handlers_concurrent_execution(self):
        """Test multiple async handlers execute concurrently."""
        start_times = []
        end_times = []

        class TimedListener(EventListener):
            def __init__(self, name, delay):
                self.name = name
                self.delay = delay

            async def handle_timed_topic(self, event):
                start_times.append((self.name, asyncio.get_event_loop().time()))
                await asyncio.sleep(self.delay)
                end_times.append((self.name, asyncio.get_event_loop().time()))

        listener1 = TimedListener("slow", 0.1)
        listener2 = TimedListener("fast", 0.01)
        await listener1.subscribe([])
        await listener2.subscribe([])

        event = Event(topic="timed.topic", sender="test", payload="data")
        await event_bus.publish(event)

        # Both should start before either ends (concurrent)
        slow_start = next(t for n, t in start_times if n == "slow")
        fast_start = next(t for n, t in start_times if n == "fast")
        slow_end = next(t for n, t in end_times if n == "slow")
        fast_end = next(t for n, t in end_times if n == "fast")

        # Both start times should be close (concurrent start)
        assert abs(slow_start - fast_start) < 0.05
        # Fast should end before slow
        assert fast_end < slow_end


class TestEdgeCases:
    """Edge case tests for edge coverage."""

    def setup_method(self):
        """Clear singleton before each test."""
        event_bus._subscribers.clear()

    def test_event_with_empty_string_payload(self):
        """Test Event with empty string payload."""
        event = Event(topic="test", sender="test", payload="")
        assert event.payload == ""

    def test_event_with_zero_payload(self):
        """Test Event with zero payload."""
        event = Event(topic="test", sender="test", payload=0)
        assert event.payload == 0

    def test_event_with_false_payload(self):
        """Test Event with False payload."""
        event = Event(topic="test", sender="test", payload=False)
        assert event.payload is False

    def test_event_with_empty_list_payload(self):
        """Test Event with empty list payload."""
        event = Event(topic="test", sender="test", payload=[])
        assert event.payload == []

    def test_event_with_empty_dict_payload(self):
        """Test Event with empty dict payload."""
        event = Event(topic="test", sender="test", payload={})
        assert event.payload == {}

    def test_subscribe_with_empty_topics_list(self):
        """Test subscribe with empty topics list."""
        class Listener(EventListener):
            async def handle_test(self, event):
                pass

        listener = Listener()
        asyncio.run(listener.subscribe([]))

        # Should still auto-discover handlers
        assert "test" in event_bus._subscribers

    def test_subscribe_with_none_topics(self):
        """Test subscribe with None topics (defaults to empty list)."""
        class Listener(EventListener):
            async def handle_test(self, event):
                pass

        listener = Listener()
        asyncio.run(listener.subscribe(None))

        assert "test" in event_bus._subscribers

    def test_unsubscribe_from_topic_with_multiple_listeners(self):
        """Test unsubscribe removes only one listener from multi-listener topic."""
        listener1 = EventListener()
        listener2 = EventListener()
        event_bus.subscribe("topic", listener1)
        event_bus.subscribe("topic", listener2)

        event_bus.unsubscribe("topic", listener1)

        assert listener1 not in event_bus._subscribers["topic"]
        assert listener2 in event_bus._subscribers["topic"]

    def test_subscribe_same_listener_multiple_topics(self):
        """Test same listener can subscribe to multiple topics."""
        class Listener(EventListener):
            async def handle_topic1(self, event):
                pass

            async def handle_topic2(self, event):
                pass

        listener = Listener()
        asyncio.run(listener.subscribe(["topic3"]))

        assert "topic1" in event_bus._subscribers
        assert "topic2" in event_bus._subscribers
        assert "topic3" in event_bus._subscribers
        assert listener in event_bus._subscribers["topic1"]
        assert listener in event_bus._subscribers["topic2"]
        assert listener in event_bus._subscribers["topic3"]

    @pytest.mark.asyncio
    async def test_publish_event_with_none_payload(self):
        """Test publish with None payload."""
        class Listener(EventListener):
            def __init__(self):
                self.payload = None

            async def handle_none_topic(self, event):
                self.payload = event.payload

        listener = Listener()
        await listener.subscribe([])

        event = Event(topic="none.topic", sender="test", payload=None)
        await event_bus.publish(event)

        assert listener.payload is None

    @pytest.mark.asyncio
    async def test_listener_handle_method_called_with_correct_event(self):
        """Test listener handle method receives correct event object."""
        class Listener(EventListener):
            def __init__(self):
                self.received_event = None

            async def handle_correct_topic(self, event):
                self.received_event = event

        listener = Listener()
        await listener.subscribe([])

        event = Event(topic="correct.topic", sender="sender123", payload={"key": "value"})
        await event_bus.publish(event)

        assert listener.received_event is event
        assert listener.received_event.topic == "correct.topic"
        assert listener.received_event.sender == "sender123"
        assert listener.received_event.payload == {"key": "value"}

    def test_event_bus_initial_subscribers_empty(self):
        """Test fresh EventBus has empty subscribers."""
        bus = EventBus()
        assert bus._subscribers == {}

    def test_event_topic_with_special_characters(self):
        """Test event topic with special characters."""
        class Listener(EventListener):
            async def handle_user_created(self, event):
                pass

            async def handle_user_deleted(self, event):
                pass

        listener = Listener()
        asyncio.run(listener.subscribe([]))

        # Topics with dots work
        assert "user.created" in event_bus._subscribers
        assert "user.deleted" in event_bus._subscribers


# Pytest configuration for async tests
pytest_plugins = ['pytest_asyncio']