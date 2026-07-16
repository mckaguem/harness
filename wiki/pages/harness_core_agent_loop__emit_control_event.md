---
name: "harness_core.agent.loop._emit_control_event"
description: "Emit a control event (e.g. agent.turn.start/stop) on the TUI event loop."
source: "harness_core/agent/loop.py"
---

Emit a control event (e.g. agent.turn.start/stop) on the TUI event loop.

These are lightweight control events without payload. They are only emitted
when the textual TUI is active; in non-TUI mode they are no-ops (the classic
REPL does not need spinner/turn control events).

## Signature
```python
_emit_control_event(agent, topic: str) -> None
```

## References
- [Module: harness_core.agent.loop](harness_core_agent_loop) - Parent module
