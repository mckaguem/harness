# The plan

We are building an event bus system

## EventBus

Create a new file called `eventbus.py`

- Event Datclass:
    - topic: str
    - sender: str
    - payload: Any

- EventBus class:
    - Maintains a dict of topic: list of EventListeners
    - subscribe(self, topic: str, listener: EventListener)
        - Adds listener to list of listeners for this topic
    - publish(self, event: Event)
        - for each listener in the Event's topic creates an asyncio task to call the listener's handle() function
        - concurrently runs the tasks with asyncio

- Singleton EventBus object

- EventListener class:
    - base class with magic for dispatching events to handlers by topic
    - handle(self, event: Event)
        - if event.topic = 'topic_name' then calls `self.handle_topic_name(event)` and analogously for any topic
        - if no handler, then calls `self.default_handler(event)`
    - default_handler(event: Event)
        - does nothing in base class
    - subscribe(topics: List[str] = [])
        - finds all functions on the object that have names matching `handle_*`.  Extracts the topic name from the function name and adds it to list of topics to subscribe to.
        - subscribes self to each topic in `topics`, and topics discovered from function names, on the singleton EventBus

## Tests

- Create tests for 100% coverage of all functionality.
