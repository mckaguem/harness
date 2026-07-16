---
name: "harness_core.agent.core.__init__"
description: "Initialize an Agent."
source: "harness_core/agent/core.py"
---

Initialize an Agent.

Args:
    agent_type: The agent definition (model, system prompt, tools).
    context_length: Model's context window size.
    provider: Optional Provider instance. When given, it is used directly.
              Otherwise the provider is resolved via the singleton registry
              from ``AgentType.provider_config`` (loaded from YAML).
    id: Optional explicit identifier for this agent. When given, the
        agent id is ``"Agent.{id}"``; otherwise a unique id is generated.

## Signature
```python
__init__(self, agent_type: 'AgentType', context_length: int, provider: Optional[Provider], tool_schemas: list[Dict] | None, extra_tools: list[Dict] | None, id: Optional[str])
```

## References
- [Module: harness_core.agent.core](harness_core_agent_core) - Parent module
- [Class: Agent](harness_core_agent_core_Agent) - Parent class
