---
name: "harness_core.session.session.from_file"
description: "Load a session from a YAML file."
source: "harness_core/session/session.py"
---

Load a session from a YAML file.

Args:
    filepath: Path to the YAML session file.
    task_list: Optional TaskList instance for context injection.

Returns:
    A new :class:`Session` instance loaded from the file.

Raises:
    FileNotFoundError: If *filepath* does not exist.
    ValueError: If the file cannot be parsed or contains invalid data.

## Signature
```python
from_file(cls, filepath: str, task_list) -> 'Session'
```

## References
- [Module: harness_core.session.session](harness_core_session_session) - Parent module
- [Class: Session](harness_core_session_session_Session) - Parent class
