---
name: "harness_core.skills.discovery.discover_skills"
description: "Discover and validate all skills across the specified directories."
source: "harness_core/skills/discovery.py"
---

Discover and validate all skills across the specified directories.

Args:
    skills_dirs: Ordered list of skill directory paths to scan. The first
        entry has highest precedence — if a skill name exists in multiple
        directories, its metadata from the earlier directory wins.
        Defaults to ``[cwd/.harness_py/skills, ~/.harness_py/skills]``
        (project first).
    command_names: Optional set of command names to check for collisions.
        If provided and any skill names match command names, raises
        RuntimeError with collision details.

Returns:
    A list of ``(skill_name, metadata)`` tuples for valid skills. Invalid
    skills are skipped with warnings printed to stderr.

Raises:
    RuntimeError: If command_names is provided and there are name collisions
                  between commands and skills.

## Signature
```python
discover_skills(skills_dirs: list[Path] | None, command_names: set | None) -> list[Tuple[str, Dict]]
```

## References
- [Module: harness_core.skills.discovery](harness_core_skills_discovery) - Parent module
