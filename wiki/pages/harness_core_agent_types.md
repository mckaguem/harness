---
name: "harness_core.agent.types"
description: "Agent type definition — model, tools, and system prompt configuration."
source: "harness_core/agent/types.py"
---

Agent type definition — model, tools, and system prompt configuration.

## References
- [AgentType](harness_core_agent_types_AgentType) - Definition of an agent — its model, tools, and system prompt
  - [_substitute_variables](harness_core_agent_types_AgentType__substitute_variables) - Substitute template variables of the form ``${VAR_NAME}`` in *system_prompt*
  - [_build_system_prompt](harness_core_agent_types_AgentType__build_system_prompt) - Build the final system prompt for an agent
  - [from_file](harness_core_agent_types_AgentType_from_file) - Load agent definition from a YAML file and build its system prompt
  - [inject_extra_system_prompt](harness_core_agent_types_AgentType_inject_extra_system_prompt) - Append additional text to the existing system prompt
- [_SYSTEM_VARIABLES](harness_core_agent_types__SYSTEM_VARIABLES) - Constant
- [Module Index](../index/harness_core_agent.md) - Parent module index
