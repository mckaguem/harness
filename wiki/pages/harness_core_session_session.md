---
name: "harness_core.session.session"
description: "No module docstring available."
source: "harness_core/session/session.py"
---

No module docstring available.

## References
- [Session](harness_core_session_session_Session) - Owns the conversation state and handles message lifecycle
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
- [Module Index](../index/harness_core_session.md) - Parent module index
