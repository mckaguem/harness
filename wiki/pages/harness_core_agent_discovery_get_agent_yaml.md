---
name: "harness_core.agent.discovery.get_agent_yaml"
description: "Look up an agent YAML file by name."
source: "harness_core/agent/discovery.py"
---

Look up an agent YAML file by name.

Searches the directories in order — the first match wins (project before
global when using defaults).

Args:
    agent_name: Name of the agent to look up.
    agents_dirs: Ordered list of agent config directory paths to search.

Returns:
    A tuple of ``(yaml_path, error_message)``. If *error_message* is empty,
    ``yaml_path`` is the resolved Path; otherwise no matching agent was found.

## Signature
```python
get_agent_yaml(agent_name: str, agents_dirs: list[Path] | None) -> Tuple[Path | None, str]
```

## References
- [Module: harness_core.agent.discovery](harness_core_agent_discovery) - Parent module
