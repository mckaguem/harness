---
name: "harness_core.agent.loop._emit_turn_stats_event"
description: "Emit an 'agent.turn.stats' event so terminal_io can render it via display_turn_stats."
source: "harness_core/agent/loop.py"
---

Emit an 'agent.turn.stats' event so terminal_io can render it via display_turn_stats.

## Signature
```python
_emit_turn_stats_event(agent, ollama_response: dict | None, context_length: int, elapsed_seconds: float) -> None
```

## References
- [Module: harness_core.agent.loop](harness_core_agent_loop) - Parent module
