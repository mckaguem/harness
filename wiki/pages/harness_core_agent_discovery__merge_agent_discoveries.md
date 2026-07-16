---
name: "harness_core.agent.discovery._merge_agent_discoveries"
description: "Merge multiple agent discovery results with precedence."
source: "harness_core/agent/discovery.py"
---

Merge multiple agent discovery results with precedence.

Discoveries are processed in order — the first source that provides a
given name wins. The caller is responsible for ordering sources from
highest to lowest precedence (e.g. project before global).

Returns:
    A deduplicated list of ``(agent_name, yaml_path)`` tuples.

## Signature
```python
_merge_agent_discoveries(discoveries: list[tuple[Path, list[Tuple[str, Path]]]]) -> list[Tuple[str, Path]]
```

## References
- [Module: harness_core.agent.discovery](harness_core_agent_discovery) - Parent module
