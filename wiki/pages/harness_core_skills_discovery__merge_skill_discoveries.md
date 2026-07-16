---
name: "harness_core.skills.discovery._merge_skill_discoveries"
description: "Merge multiple skill discovery results with precedence."
source: "harness_core/skills/discovery.py"
---

Merge multiple skill discovery results with precedence.

Discoveries are processed in order — the first source that provides a
given name wins. This means earlier entries in *discoveries* have higher
priority than later ones. The caller is responsible for ordering sources
from highest to lowest precedence (e.g. project before global).

Returns:
    A deduplicated list of ``(skill_name, metadata)`` tuples.

## Signature
```python
_merge_skill_discoveries(discoveries: list[list[Any]]) -> list[Tuple[str, Dict]]
```

## References
- [Module: harness_core.skills.discovery](harness_core_skills_discovery) - Parent module
