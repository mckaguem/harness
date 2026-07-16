---
name: "harness_core.agent.types._substitute_variables"
description: "Substitute template variables of the form ``${VAR_NAME}`` in *system_prompt*."
source: "harness_core/agent/types.py"
---

Substitute template variables of the form ``${VAR_NAME}`` in *system_prompt*.

The supported variable names are:

+-----------+-------------------------------------------------------+
| Variable  | Value                                                 |
+===========+=======================================================+
| ``CWD``   | Absolute path of the project root (detected via project markers). |
+-----------+-------------------------------------------------------+
| ``SKILLS``| One line per discovered skill (name: description),    |
|           | joined by newlines. Empty string if none discovered.  |
+-----------+-------------------------------------------------------+
| ``AGENTS``| One line per available agent (name: description),     |
|           | joined by newlines. Empty string if none discovered.  |
+-----------+-------------------------------------------------------+
| ``TOOLS`` | One line per available tool (tool name and short      |
|           | description from its function_def), joined by         |
|           | newlines. Empty string if none provided.              |
+-----------+-------------------------------------------------------+

Unsupported variable names are left intact so typos surface as literal
``${UNLIKELY_NAME}`` placeholders rather than silently disappearing.

Args:
    system_prompt: The raw prompt text sourced from the agent YAML.
    cwd: The project root directory to insert for ``$CWD``.
    skills: Optional list of ``(name, metadata)`` tuples (from
        :func:`skills_discovery.discover_skills`).
    agents: Optional list of dicts describing available agents,
        each with at least ``name`` and ``description`` keys.
    tools: Optional list of tool schema dicts. Each entry should have
        a ``function.description`` key; if missing, the bare function
        name is used.

Returns:
    The prompt text with all recognised variables substituted.

## Signature
```python
_substitute_variables(system_prompt: str, cwd: Path, skills: list[tuple] | None, agents: list[Dict] | None, tools: list[dict] | None) -> str
```

## References
- [Module: harness_core.agent.types](harness_core_agent_types) - Parent module
- [Class: AgentType](harness_core_agent_types_AgentType) - Parent class
