---
name: "harness_core.skills.interceptor.extract_command_name"
description: "If *text* is a slash command, return its captured name (lowercase), else ``None``."
source: "harness_core/skills/interceptor.py"
---

If *text* is a slash command, return its captured name (lowercase), else ``None``.

## Signature
```python
extract_command_name(text: str) -> str | None
```

## References
- [Module: harness_core.skills.interceptor](harness_core_skills_interceptor) - Parent module
