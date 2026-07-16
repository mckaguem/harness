---
name: "harness_core.session.session.Session"
description: "Owns the conversation state and handles message lifecycle."
source: "harness_core/session/session.py"
---

Owns the conversation state and handles message lifecycle.

The Session is responsible for:
- Storing and managing the list of conversation messages
- Queuing injected text to prepend to user input
- Preparing individual messages with task-state context before they enter the conversation

## Methods
- **__init__(self, system_prompt: str, task_list, auto_save: bool, provider, model_name: str, agent_type_name: str)** - Initialize a Session
- **add_user_message(self, content: str) -> None** - Append a user message to the conversation
- **add_assistant_message(self, message_dict: dict) -> None** - Append an assistant response (or tool-call response) to the conversation
- **add_tool_result(self, func_name: str, llm_text: str, tool_call_id: str) -> None** - Append a tool result message to the conversation
- **_auto_save_session(self) -> None** - Automatically save the current session to 
- **save(self) -> None** - Public method to trigger saving the session to disk
- **_save_impl(self, new_filepath: str, save_state: bool) -> None** - Write messages to a specific filepath using the same YAML format
as the normal session save (so compressed files match uncompressed ones)
- **get_messages(self) -> list[dict]** - Return the full message list for sending to the LLM
- **inject_text(self, s: str) -> None** - Queue *s* to be prepended to the next user input
- **consume_injected_text(self) -> str | None** - Return and clear any queued injected text
- **summarize(self, summary_prompt: str | None) -> str** - Ask the LLM to summarise the conversation accumulated so far
- **prepare_message_for_injection(self, message: dict) -> dict** - Take a single user message, inject task state if applicable, return modified copy
- **export_session(self, filename: str | None, directory: str | None, agent_type_name: str) -> tuple[bool, str]** - Export the current session to a YAML file
- **from_file(cls, filepath: str, task_list) -> 'Session'** - Load a session from a YAML file

## Class Variables
None

## References
- [Module: harness_core.session.session](harness_core_session_session) - Parent module
- [__init__](harness_core_session_session_Session___init__) - Initialize a Session
- [add_user_message](harness_core_session_session_Session_add_user_message) - Append a user message to the conversation
- [add_assistant_message](harness_core_session_session_Session_add_assistant_message) - Append an assistant response (or tool-call response) to the conversation
- [add_tool_result](harness_core_session_session_Session_add_tool_result) - Append a tool result message to the conversation
- [_auto_save_session](harness_core_session_session_Session__auto_save_session) - Automatically save the current session to 
- [save](harness_core_session_session_Session_save) - Public method to trigger saving the session to disk
- [_save_impl](harness_core_session_session_Session__save_impl) - Write messages to a specific filepath using the same YAML format
as the normal session save (so compressed files match uncompressed ones)
- [get_messages](harness_core_session_session_Session_get_messages) - Return the full message list for sending to the LLM
- [inject_text](harness_core_session_session_Session_inject_text) - Queue *s* to be prepended to the next user input
- [consume_injected_text](harness_core_session_session_Session_consume_injected_text) - Return and clear any queued injected text
- [summarize](harness_core_session_session_Session_summarize) - Ask the LLM to summarise the conversation accumulated so far
- [prepare_message_for_injection](harness_core_session_session_Session_prepare_message_for_injection) - Take a single user message, inject task state if applicable, return modified copy
- [export_session](harness_core_session_session_Session_export_session) - Export the current session to a YAML file
- [from_file](harness_core_session_session_Session_from_file) - Load a session from a YAML file
