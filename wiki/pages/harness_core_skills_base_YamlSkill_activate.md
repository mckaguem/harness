---
name: "harness_core.skills.base.activate"
description: "Activate the skill by running a script."
source: "harness_core/skills/base.py"
---

Activate the skill by running a script.

Args:
    script_name: Which script to run (default: "main")
    **kwargs: Script arguments
    
Returns:
    Dictionary with script execution results

## Signature
```python
activate(self, script_name: str, **kwargs) -> dict[str, Any]
```

## References
- [Module: harness_core.skills.base](harness_core_skills_base) - Parent module
- [Class: YamlSkill](harness_core_skills_base_YamlSkill) - Parent class
