---
name: "harness_core.agent.loop.user_loop"
description: "Run the interactive chat loop."
source: "harness_core/agent/loop.py"
---

Run the interactive chat loop.

Args:
    agent: An initialized :class:`Agent` instance with its configuration.
    on_exit: Optional callback invoked just before the loop breaks due to 
             ``/exit`` or ``/quit``. Receives ``(agent, messages)``. Return
             value is ignored — the callback can mutate whatever it needs.

## Signature
```python
user_loop(agent: 'Agent', on_exit) -> None
```

## References
- [Module: harness_core.agent.loop](harness_core_agent_loop) - Parent module
