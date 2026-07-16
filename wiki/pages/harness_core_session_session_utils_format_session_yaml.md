---
name: "harness_core.session.session_utils.format_session_yaml"
description: "Format session messages as YAML with human-readable comment lines."
source: "harness_core/session/session_utils.py"
---

Format session messages as YAML with human-readable comment lines.

Uses multiple YAML documents separated by ``---`` so each message is a clean,
independent mapping.  Human-readable comment markers are placed on their own
line between document separators — the YAML parser ignores them but humans
see them clearly in the file.

Args:
    messages: List of message dicts with role and content keys.
    agent_type_name: The name of the agent type (e.g., 'analyst', 'coder').

Returns:
    A string containing the formatted YAML session data.

## Signature
```python
format_session_yaml(messages: list[dict], agent_type_name: str) -> str
```

## References
- [Module: harness_core.session.session_utils](harness_core_session_session_utils) - Parent module
