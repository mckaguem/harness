---
name: "harness_core.skills.discovery.format_skill_catalog"
description: "Format a list of skills into a concise catalog for system prompt injection."
source: "harness_core/skills/discovery.py"
---

Format a list of skills into a concise catalog for system prompt injection.

Args:
    skills: List of (skill_name, metadata) tuples from discover_skills()

Returns:
    A formatted string suitable for inclusion in the agent's system prompt.

## Signature
```python
format_skill_catalog(skills: list[Tuple[str, Dict]]) -> str
```

## References
- [Module: harness_core.skills.discovery](harness_core_skills_discovery) - Parent module
