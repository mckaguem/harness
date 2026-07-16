---
name: "harness_core.agent.loop._emit_agent_response_event"
description: "Emit an 'agent.turn.response' event so terminal_io can render it via display_agent_response."
source: "harness_core/agent/loop.py"
---

Emit an 'agent.turn.response' event so terminal_io can render it via display_agent_response.

## Signature
```python
_emit_agent_response_event(agent, content: str | None, ollama_response: dict | None, context_length: int, reasoning: str | None) -> None
```

## References
- [Module: harness_core.agent.loop](harness_core_agent_loop) - Parent module
