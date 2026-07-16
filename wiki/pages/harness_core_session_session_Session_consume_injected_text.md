---
name: "harness_core.session.session.consume_injected_text"
description: "Return and clear any queued injected text."
source: "harness_core/session/session.py"
---

Return and clear any queued injected text.

Returns the currently queued text (or ``None`` if nothing is queued)
and resets the queue so it is only applied to one user turn.

## Signature
```python
consume_injected_text(self) -> str | None
```

## References
- [Module: harness_core.session.session](harness_core_session_session) - Parent module
- [Class: Session](harness_core_session_session_Session) - Parent class
