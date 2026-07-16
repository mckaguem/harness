---
name: "harness_core.agent.discovery.get_agent_yaml_paths"
description: "Return the absolute paths to all available agents/ directories."
source: "harness_core/agent/discovery.py"
---

Return the absolute paths to all available agents/ directories.

Useful for injecting into tool descriptions or system prompts so models
know where to look for agent definitions.

## Signature
```python
get_agent_yaml_paths() -> list[Path]
```

## References
- [Module: harness_core.agent.discovery](harness_core_agent_discovery) - Parent module
