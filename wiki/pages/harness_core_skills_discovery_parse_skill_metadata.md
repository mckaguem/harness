---
name: "harness_core.skills.discovery.parse_skill_metadata"
description: "Parse a skill directory's SKILL.md file and validate metadata."
source: "harness_core/skills/discovery.py"
---

Parse a skill directory's SKILL.md file and validate metadata.

Args:
    skill_dir: Path to the skill directory containing SKILL.md

Returns:
    A tuple of (metadata_dict, errors_list). If errors is non-empty,
    the skill should be skipped.

## Signature
```python
parse_skill_metadata(skill_dir: Path) -> Tuple[Dict, list[str]]
```

## References
- [Module: harness_core.skills.discovery](harness_core_skills_discovery) - Parent module
