---
name: "harness_core.config.resolve_config_path"
description: "Resolve a relative path (e.g. ``"agents/main.yaml"``) to an absolute Path."
source: "harness_core/config.py"
---

Resolve a relative path (e.g. ``"agents/main.yaml"``) to an absolute Path.

Searches first in the project config directory (preferred), then falls back to
the global config directory.  Returns ``None`` if the file is not found in either
location.

Args:
    relative_path: A path relative to a config root, e.g. ``"agents/main.yaml"``.

Returns:
    The resolved absolute :class:`Path`, or ``None`` when neither directory
    contains the requested file.

## Signature
```python
resolve_config_path(relative_path: str) -> Path | None
```

## References
- [Module: harness_core.config](harness_core_config) - Parent module
