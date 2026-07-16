---
name: "harness_core.session.session._save_impl"
description: "Write messages to a specific filepath using the same YAML format"
source: "harness_core/session/session.py"
---

Write messages to a specific filepath using the same YAML format
as the normal session save (so compressed files match uncompressed ones).

## Signature
```python
_save_impl(self, new_filepath: str, save_state: bool) -> None
```

## References
- [Module: harness_core.session.session](harness_core_session_session) - Parent module
- [Class: Session](harness_core_session_session_Session) - Parent class
