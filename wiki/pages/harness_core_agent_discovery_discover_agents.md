---
name: "harness_core.agent.discovery.discover_agents"
description: "Discover all agent YAML files across the specified directories."
source: "harness_core/agent/discovery.py"
---

Discover all agent YAML files across the specified directories.

Args:
    agents_dirs: Ordered list of agent config directory paths to scan.
        The first entry has highest precedence — if an agent name exists
        in multiple directories, its YAML from the earlier directory wins.
        Defaults to ``[cwd/.harness_py/agents, ~/.harness_py/agents]``
        (project first).

Returns:
    A list of ``(agent_name, yaml_path)`` tuples for valid agent files.
    Invalid or unreadable YAML files are skipped with warnings printed
    to stderr.

## Signature
```python
discover_agents(agents_dirs: list[Path] | None) -> list[Tuple[str, Path]]
```

## References
- [Module: harness_core.agent.discovery](harness_core_agent_discovery) - Parent module
