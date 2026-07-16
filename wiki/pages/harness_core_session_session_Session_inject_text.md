---
name: "harness_core.session.session.inject_text"
description: "Queue *s* to be prepended to the next user input."
source: "harness_core/session/session.py"
---

Queue *s* to be prepended to the next user input.

The text is wrapped in a delimiter so that when it is injected into the
conversation the agent (and any downstream logic) can tell it apart from
genuine user input.

Args:
    s: The string to inject. Leading/trailing whitespace is preserved.

## Signature
```python
inject_text(self, s: str) -> None
```

## References
- [Module: harness_core.session.session](harness_core_session_session) - Parent module
- [Class: Session](harness_core_session_session_Session) - Parent class
