---
name: "harness_core.agent.types.inject_extra_system_prompt"
description: "Append additional text to the existing system prompt."
source: "harness_core/agent/types.py"
---

Append additional text to the existing system prompt.

This is useful for injecting context-specific instructions without
rebuilding the entire augmented prompt (which includes cwd name).

Args:
    text: The string to append. Leading/trailing whitespace should be
          provided by the caller if desired.

## Signature
```python
inject_extra_system_prompt(self, text: str) -> None
```

## References
- [Module: harness_core.agent.types](harness_core_agent_types) - Parent module
- [Class: AgentType](harness_core_agent_types_AgentType) - Parent class
