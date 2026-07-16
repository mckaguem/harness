---
name: "harness_core.agent.types._build_system_prompt"
description: "Build the final system prompt for an agent."
source: "harness_core/agent/types.py"
---

Build the final system prompt for an agent.

The supplied *raw_prompt* is sourced from the agent's YAML file. Any
template variables (e.g. ``${CWD}``, ``${SKILLS}``, ``${AGENTS}``,
``${TOOLS}``) are substituted with runtime data from discovery
mechanisms. If no template variables are present, a small backwards-
compatible "current working directory name" footer is still appended so
existing prompts continue to work unchanged.

Args:
    raw_prompt: The base prompt text sourced from the agent YAML.
    cwd: Current working directory (defaults to project root via ``utils.project_root()``).
    skills: Optional list of ``(name, metadata)`` tuples from skill discovery.
    agents: Optional list of dicts describing available agents.
    tools: Optional list of tool schema dicts from the tool registry.

Returns:
    The fully-built system prompt with variables substituted.

## Signature
```python
_build_system_prompt(raw_prompt: str, cwd: Path | None, skills: list[tuple] | None, agents: list[Dict] | None, tools: list[dict] | None) -> str
```

## References
- [Module: harness_core.agent.types](harness_core_agent_types) - Parent module
- [Class: AgentType](harness_core_agent_types_AgentType) - Parent class
