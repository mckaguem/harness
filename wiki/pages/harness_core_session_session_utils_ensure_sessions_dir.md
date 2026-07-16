---
name: "harness_core.session.session_utils.ensure_sessions_dir"
description: "Ensure the .sessions/ directory (or current run folder) exists."
source: "harness_core/session/session_utils.py"
---

Ensure the .sessions/ directory (or current run folder) exists.

Args:
    base_path: Base path to create .sessions/ under.
        Defaults to project root (detected via project_root()).

Returns:
    The Path object for the .sessions/ directory (or the current run folder
    when one is active).

## Signature
```python
ensure_sessions_dir(base_path: str | None) -> Path
```

## References
- [Module: harness_core.session.session_utils](harness_core_session_session_utils) - Parent module
