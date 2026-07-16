---
name: "harness_core.agent.core._chat"
description: "Send *messages* to the provider and return a normalized response dict."
source: "harness_core/agent/core.py"
---

Send *messages* to the provider and return a normalized response dict.

Tracks timing data alongside token counts for performance metrics. Returns
both the message content and usage statistics in a single dict.

## Signature
```python
_chat(self, messages: list[dict]) -> dict
```

## References
- [Module: harness_core.agent.core](harness_core_agent_core) - Parent module
- [Class: Agent](harness_core_agent_core_Agent) - Parent class
