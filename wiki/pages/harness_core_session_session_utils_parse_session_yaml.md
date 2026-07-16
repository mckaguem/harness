---
name: "harness_core.session.session_utils.parse_session_yaml"
description: "Parse YAML session data back into a list of message dicts."
source: "harness_core/session/session_utils.py"
---

Parse YAML session data back into a list of message dicts.

Expects the format produced by :func:`format_session_yaml`, which uses
``---`` document separators so each message is an independent YAML mapping.

Returns:
    A tuple of ``(messages_list, error_string)``. If *error* is ``None``,
    parsing succeeded.

## Signature
```python
parse_session_yaml(yaml_content: str) -> tuple[list[dict], str | None]
```

## References
- [Module: harness_core.session.session_utils](harness_core_session_session_utils) - Parent module
