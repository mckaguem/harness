---
name: "harness_core.agent.core.from_file"
description: "Create an Agent directly from a YAML agent config file."
source: "harness_core/agent/core.py"
---

Create an Agent directly from a YAML agent config file.

This is the recommended entry point for creating agents. It handles:
- Loading the agent YAML definition (model_name, system_prompt, agent_tools)
- Discovering skills and agents to inject into the system prompt
- Resolving provider configuration from harness_core.config.py defaults
- Getting context_length from the model/provider config
- Building the fully-injected system prompt

Args:
    path: Path to the agent YAML file (e.g., ``".harness_py/agents/main.yaml"``).
    tool_schemas: All available tool schemas. If None, uses AGENT_TOOLS from harness_core.tools module.
    extra_tools: Additional function_def dicts added after filtering. Useful for
                 runtime-injected tools like ``submit_results`` without modifying
                 agent YAML files.

Returns:
    A fully-constructed Agent instance ready for prompting.

## Signature
```python
from_file(cls, path: str, tool_schemas: list[Dict] | None, extra_tools: list[Dict] | None) -> 'Agent'
```

## References
- [Module: harness_core.agent.core](harness_core_agent_core) - Parent module
- [Class: Agent](harness_core_agent_core_Agent) - Parent class
