---
name: "harness_core.agent.loop._emit_system_event"
description: "Emit a system-notification event, or render it directly when no TUI is active."
source: "harness_core/agent/loop.py"
---

Emit a system-notification event, or render it directly when no TUI is active.

When the textual TUI is active the event is published on the registered app
loop (set via ``set_event_loop`` in ``TextualHarnessApp.on_mount``) so the
subscribed :class:`~harness_core.terminal_io.event_listener.HarnessEventListener`
can render it through the TUI output pane.  In the classic REPL (and other
non-TUI contexts) there is no event listener subscribed, so we fall back to
calling :func:`harness_core.terminal_io.display.print_system` directly.

## Signature
```python
_emit_system_event(agent, topic: str, title: str, message: str) -> None
```

## References
- [Module: harness_core.agent.loop](harness_core_agent_loop) - Parent module
