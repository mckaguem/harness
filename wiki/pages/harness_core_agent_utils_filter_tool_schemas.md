---
name: "harness_core.agent.utils.filter_tool_schemas"
description: "Filter tool schemas to include only those named in ``agent_type.agent_tools``."
source: "harness_core/agent/utils.py"
---

Filter tool schemas to include only those named in ``agent_type.agent_tools``.

If ``agent_type.agent_tools`` contains ``"*"``, all schemas are returned.
Otherwise, only schemas whose ``function.name`` is in the list are kept.

Args:
    agent_type: The agent definition specifying which tools to use.
    all_schemas: All available tool schema dicts (each must have a 
                 ``"function"`` key with a ``"name"`` field).
                 
Returns:
    Filtered list of tool schemas.
    
Raises:
    ValueError: If any name in ``agent_type.agent_tools`` is not in the 
                available schemas (and the name is not ``"*"``).

## Signature
```python
filter_tool_schemas(agent_type: AgentType, all_schemas: list[Dict]) -> list[Dict]
```

## References
- [Module: harness_core.agent.utils](harness_core_agent_utils) - Parent module
