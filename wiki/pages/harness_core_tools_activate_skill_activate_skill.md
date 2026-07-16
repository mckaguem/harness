---
name: "harness_core.tools.activate_skill.activate_skill"
description: "Activate a skill by reading its SKILL.md body and returning instructions."
source: "harness_core/tools/activate_skill.py"
---

Activate a skill by reading its SKILL.md body and returning instructions.

This is Phase 2 of the Progressive Disclosure pattern. The agent uses this 
tool after discovering skills via the system prompt catalog (Phase 1). When 
called, it returns the Markdown body from the skill's SKILL.md file, prefixed 
with the absolute path so the agent knows where to run scripts and read files.

Args:
    skill_name: The name of the skill to activate (must match directory name)
    
Returns:
    A ``ToolResult`` with the formatted skill instructions, or an error result
    on failure.

## Signature
```python
activate_skill(skill_name: str) -> ToolResult
```

## References
- [Module: harness_core.tools.activate_skill](harness_core_tools_activate_skill) - Parent module
