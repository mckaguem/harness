---
name: "harness_core.session.session.add_tool_result"
description: "Append a tool result message to the conversation."
source: "harness_core/session/session.py"
---

Append a tool result message to the conversation.

Each appended message carries a ``timestamp`` key for mtime-based compression checks.

Args:
    func_name: The name of the tool that was called.
    llm_text: The text content for the LLM (ToolResult.llm_text).

## Signature
```python
add_tool_result(self, func_name: str, llm_text: str, tool_call_id: str) -> None
```

## References
- [Module: harness_core.session.session](harness_core_session_session) - Parent module
- [Class: Session](harness_core_session_session_Session) - Parent class
