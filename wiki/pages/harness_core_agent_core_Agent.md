---
name: "harness_core.agent.core.Agent"
description: "Owns the conversation state and handles a single user turn."
source: "harness_core/agent/core.py"
---

Owns the conversation state and handles a single user turn.

## Methods
- **__init__(self, agent_type: 'AgentType', context_length: int, provider: Optional[Provider], tool_schemas: list[Dict] | None, extra_tools: list[Dict] | None, id: Optional[str])** - Initialize an Agent
- **id(self) -> str** - Unique identifier for this agent (prefixed with 'Agent
- **task_list(self) -> 'Optional[TaskList]'** - Public accessor for the agent's task list
- **provider(self)** - Public accessor for the Provider instance
- **context_length(self) -> int** - Public accessor for the model's context window size
- **session(self) -> 'Session'** - Public accessor for the underlying Session object
- **messages(self) -> list[dict]** - Public accessor for the session's message list
- **inject_text(self, s: str) -> None** - Queue *s* to be prepended to the next user input
- **_chat(self, messages: list[dict]) -> dict** - Send *messages* to the provider and return a normalized response dict
- **handle_prompt(self, user_input: str) -> Generator[tuple[str, Any, Any, Optional[dict[str, Any]]], None, None]** - Process a single user prompt to completion
- **spawn_subagent(cls, sub_name: str, tool_schemas: list[Dict] | None, extra_tools: list[Dict] | None)** - Build and return a configured ``Agent`` for the named sub-agent
- **from_file(cls, path: str, tool_schemas: list[Dict] | None, extra_tools: list[Dict] | None) -> 'Agent'** - Create an Agent directly from a YAML agent config file

## Class Variables
None

## References
- [Module: harness_core.agent.core](harness_core_agent_core) - Parent module
- [__init__](harness_core_agent_core_Agent___init__) - Initialize an Agent
- [id](harness_core_agent_core_Agent_id) - Unique identifier for this agent (prefixed with 'Agent
- [task_list](harness_core_agent_core_Agent_task_list) - Public accessor for the agent's task list
- [provider](harness_core_agent_core_Agent_provider) - Public accessor for the Provider instance
- [context_length](harness_core_agent_core_Agent_context_length) - Public accessor for the model's context window size
- [session](harness_core_agent_core_Agent_session) - Public accessor for the underlying Session object
- [messages](harness_core_agent_core_Agent_messages) - Public accessor for the session's message list
- [inject_text](harness_core_agent_core_Agent_inject_text) - Queue *s* to be prepended to the next user input
- [_chat](harness_core_agent_core_Agent__chat) - Send *messages* to the provider and return a normalized response dict
- [handle_prompt](harness_core_agent_core_Agent_handle_prompt) - Process a single user prompt to completion
- [spawn_subagent](harness_core_agent_core_Agent_spawn_subagent) - Build and return a configured ``Agent`` for the named sub-agent
- [from_file](harness_core_agent_core_Agent_from_file) - Create an Agent directly from a YAML agent config file
