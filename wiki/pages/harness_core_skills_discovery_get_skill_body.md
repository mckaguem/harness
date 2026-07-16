---
name: "harness_core.skills.discovery.get_skill_body"
description: "Get the body content of a specific skill's SKILL.md file."
source: "harness_core/skills/discovery.py"
---

Get the body content of a specific skill's SKILL.md file.

Args:
    skill_name: Name of the skill to activate.
    skills_dirs: Ordered list of skill directory paths to search. Defaults
        to ``[cwd/.harness_py/skills, ~/.harness_py/skills]``.

Returns:
    A tuple of (body_content, error_message). If *error_message* is non-empty,
    activation failed.

## Signature
```python
get_skill_body(skill_name: str, skills_dirs: list[Path] | None) -> Tuple[str, str]
```

## References
- [Module: harness_core.skills.discovery](harness_core_skills_discovery) - Parent module
