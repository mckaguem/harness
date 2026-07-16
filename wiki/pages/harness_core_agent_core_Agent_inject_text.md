---
name: "harness_core.agent.core.inject_text"
description: "Queue *s* to be prepended to the next user input."
source: "harness_core/agent/core.py"
---

Queue *s* to be prepended to the next user input.

The text is wrapped in a delimiter so that when it is injected into the
conversation the agent (and any downstream logic) can tell it apart from
genuine user input.

Args:
    s: The string to inject. Leading/trailing whitespace is preserved.

## Signature
```python
inject_text(self, s: str) -> None
```

## References
- [Module: harness_core.agent.core](harness_core_agent_core) - Parent module
- [Class: Agent](harness_core_agent_core_Agent) - Parent class
