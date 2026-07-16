---
name: "harness_core.agent.core"
description: "Agent class — owns the conversation and processes one user prompt to completion."
source: "harness_core/agent/core.py"
---

Agent class — owns the conversation and processes one user prompt to completion.

## References
- [Agent](harness_core_agent_core_Agent) - Owns the conversation state and handles a single user turn
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
- [Module Index](../index/harness_core_agent.md) - Parent module index
