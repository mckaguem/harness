---
name: "harness_core.session.session.add_user_message"
description: "Append a user message to the conversation."
source: "harness_core/session/session.py"
---

Append a user message to the conversation.

Each appended message carries a ``timestamp`` key for mtime-based compression checks.

Args:
    content: The text content of the user message.

## Signature
```python
add_user_message(self, content: str) -> None
```

## References
- [Module: harness_core.session.session](harness_core_session_session) - Parent module
- [Class: Session](harness_core_session_session_Session) - Parent class
