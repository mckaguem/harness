---
name: "harness_core.agent.types.AgentType"
description: "Definition of an agent — its model, tools, and system prompt."
source: "harness_core/agent/types.py"
---

Definition of an agent — its model, tools, and system prompt.

## Methods
- **_substitute_variables(system_prompt: str, cwd: Path, skills: list[tuple] | None, agents: list[Dict] | None, tools: list[dict] | None) -> str** - Substitute template variables of the form ``${VAR_NAME}`` in *system_prompt*
- **_build_system_prompt(raw_prompt: str, cwd: Path | None, skills: list[tuple] | None, agents: list[Dict] | None, tools: list[dict] | None) -> str** - Build the final system prompt for an agent
- **from_file(cls, path: str) -> 'AgentType'** - Load agent definition from a YAML file and build its system prompt
- **inject_extra_system_prompt(self, text: str) -> None** - Append additional text to the existing system prompt

## Class Variables
- `name`: str
- `model_name`: str
- `provider_model_name`: str
- `system_prompt`: str
- `provider_config`: ProviderConfig | None
- `agent_tools`: list[str]

## References
- [Module: harness_core.agent.types](harness_core_agent_types) - Parent module
- [_substitute_variables](harness_core_agent_types_AgentType__substitute_variables) - Substitute template variables of the form ``${VAR_NAME}`` in *system_prompt*
- [_build_system_prompt](harness_core_agent_types_AgentType__build_system_prompt) - Build the final system prompt for an agent
- [from_file](harness_core_agent_types_AgentType_from_file) - Load agent definition from a YAML file and build its system prompt
- [inject_extra_system_prompt](harness_core_agent_types_AgentType_inject_extra_system_prompt) - Append additional text to the existing system prompt
- `name`: str
- `model_name`: str
- `provider_model_name`: str
- `system_prompt`: str
- `provider_config`: ProviderConfig | None
- `agent_tools`: list[str]
