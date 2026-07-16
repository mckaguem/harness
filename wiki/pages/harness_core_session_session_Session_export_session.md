---
name: "harness_core.session.session.export_session"
description: "Export the current session to a YAML file."
source: "harness_core/session/session.py"
---

Export the current session to a YAML file.

Args:
    filename: Optional custom filename. If not provided, generates one
        using :func:`create_session_filename` with timestamp and agent type.
    directory: Optional directory path. Defaults to ``.sessions/`` in cwd.
    agent_type_name: The agent type name for the default filename.

Returns:
    A tuple ``(success, message)`` where *message* is either the file path
    on success or an error description.

## Signature
```python
export_session(self, filename: str | None, directory: str | None, agent_type_name: str) -> tuple[bool, str]
```

## References
- [Module: harness_core.session.session](harness_core_session_session) - Parent module
- [Class: Session](harness_core_session_session_Session) - Parent class
