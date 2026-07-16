---
name: "harness_core.terminal_io.event_listener.make_event_listener"
description: "Create a :class:`HarnessEventListener` filtered to ``agent_id``."
source: "harness_core/terminal_io/event_listener.py"
---

Create a :class:`HarnessEventListener` filtered to ``agent_id``.

The returned listener subscribes to the five ``agent.*`` topics.  Each
handler is decorated with :func:`harness_core.eventbus.filter_by_sender`
using a per-agent regex (e.g. ``^Agent\.main$``), so only events published
by that agent (sender == its id, e.g. ``Agent.main``) reach the TUI — other
agents' events are silently ignored.

Args:
    agent_id: The agent identifier to filter events for (e.g. "Agent.main")
    bus: Optional EventBus instance (defaults to global event_bus singleton)

## Signature
```python
make_event_listener(agent_id: str, bus: Optional[EventBus]) -> EventListener
```

## References
- [Module: harness_core.terminal_io.event_listener](harness_core_terminal_io_event_listener) - Parent module
