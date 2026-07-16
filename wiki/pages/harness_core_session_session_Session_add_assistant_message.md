---
name: "harness_core.session.session.add_assistant_message"
description: "Append an assistant response (or tool-call response) to the conversation."
source: "harness_core/session/session.py"
---

Append an assistant response (or tool-call response) to the conversation.

Each appended message carries a ``timestamp`` key for mtime-based compression checks.
If ``message_dict`` already has a ``timestamp``, it is preserved as-is (e.g., when replayed from file).

Args:
    message_dict: The full message dictionary with 'role', 'content', etc.

## Signature
```python
add_assistant_message(self, message_dict: dict) -> None
```

## References
- [Module: harness_core.session.session](harness_core_session_session) - Parent module
- [Class: Session](harness_core_session_session_Session) - Parent class
