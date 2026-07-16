---
name: "harness_core.session.session_utils.create_session_filename"
description: "Create a unique filename for session export based on timestamp and agent type."
source: "harness_core/session/session_utils.py"
---

Create a unique filename for session export based on timestamp and agent type.

Args:
    agent_type_name: The agent type name (e.g., 'analyst', 'coder').
    extension: File extension (default '.yaml').

Returns:
    A filename string in the format YYYYMMDD_HHMMSS_μs_agenttype.ext
    Uses nanosecond precision to ensure uniqueness even for rapid successive saves.

## Signature
```python
create_session_filename(agent_type_name: str, extension: str) -> str
```

## References
- [Module: harness_core.session.session_utils](harness_core_session_session_utils) - Parent module
