---
name: "harness_core.agent.types.from_file"
description: "Load agent definition from a YAML file and build its system prompt."
source: "harness_core/agent/types.py"
---

Load agent definition from a YAML file and build its system prompt.

Expected format::

    name: "my_agent"                              # optional display name
    model_name: "model/identifier"
    system_prompt: "You are an autonomous coding assistant..."
    agent_tools: [execute_bash, write_file]       # or ["*"] for all

The ``system_prompt`` is read directly from the YAML and augmented by
appending the current working directory name.

Args:
    path: Path to the YAML file.
    
Returns:
    An AgentType instance with its system prompt fully built.
    
Raises:
    FileNotFoundError: If the YAML file does not exist.
    ValueError: If required fields are absent or malformed, or if 
                ``system_prompt`` is missing from the YAML.

## Signature
```python
from_file(cls, path: str) -> 'AgentType'
```

## References
- [Module: harness_core.agent.types](harness_core_agent_types) - Parent module
- [Class: AgentType](harness_core_agent_types_AgentType) - Parent class
