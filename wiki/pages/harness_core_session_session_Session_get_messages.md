---
name: "harness_core.session.session.get_messages"
description: "Return the full message list for sending to the LLM."
source: "harness_core/session/session.py"
---

Return the full message list for sending to the LLM.

Returns:
    The complete conversation history (including system prompt).

## Signature
```python
get_messages(self) -> list[dict]
```

## References
- [Module: harness_core.session.session](harness_core_session_session) - Parent module
- [Class: Session](harness_core_session_session_Session) - Parent class
