---
name: "harness_core.config.get_discovery_dirs"
description: "Return ordered discovery directories for a given component (skills/agents)."
source: "harness_core/config.py"
---

Return ordered discovery directories for a given component (skills/agents).

This helper centralizes the repeated pattern of resolving both project and
global .harness_py subdirectories in one call, ensuring consistent ordering
(project first) across all discovery modules.

Args:
    subdir: The subdirectory name within ``.harness_py/`` to discover
        (e.g. ``"skills"`` or ``"agents"``).

Returns:
    An ordered list of :class:`Path` objects — project first, then global.

## Signature
```python
get_discovery_dirs(subdir: str) -> list[Path]
```

## References
- [Module: harness_core.config](harness_core_config) - Parent module
