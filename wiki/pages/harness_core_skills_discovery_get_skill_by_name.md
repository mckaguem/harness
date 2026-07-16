---
name: "harness_core.skills.discovery.get_skill_by_name"
description: "Look up a skill by name and return its parsed metadata."
source: "harness_core/skills/discovery.py"
---

Look up a skill by name and return its parsed metadata.

Searches the directories in order — the first match wins (project before
global when using defaults).

Args:
    skill_name: Name of the skill to look up.
    skills_dirs: Ordered list of skill directory paths to search. Defaults
        to ``[cwd/.harness_py/skills, ~/.harness_py/skills]``.

Returns:
    A tuple of (metadata_dict, error_message). If *error_message* is non-empty,
    no matching skill was found or validation failed.

## Signature
```python
get_skill_by_name(skill_name: str, skills_dirs: list[Path] | None) -> Tuple[dict[str, object], str]
```

## References
- [Module: harness_core.skills.discovery](harness_core_skills_discovery) - Parent module
