---
name: "harness_core.skills.discovery.check_command_skill_collision"
description: "Check for name collisions between provided command names and discovered skills."
source: "harness_core/skills/discovery.py"
---

Check for name collisions between provided command names and discovered skills.

Args:
    command_names: Set of command names to check against discovered skills
    
Returns:
    List of collision message strings (empty if no collisions)

## Signature
```python
check_command_skill_collision(command_names: set) -> list
```

## References
- [Module: harness_core.skills.discovery](harness_core_skills_discovery) - Parent module
