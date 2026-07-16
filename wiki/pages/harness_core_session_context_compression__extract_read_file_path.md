---
name: "harness_core.session.context_compression._extract_read_file_path"
description: "Best-effort extraction of a file path from a read_file result's content."
source: "harness_core/session/context_compression.py"
---

Best-effort extraction of a file path from a read_file result's content.

The read_file output wraps the body in ``<file path="...">...</file>``; this
function parses that attribute out via regex and returns the path, or None
if it cannot be found.

## Signature
```python
_extract_read_file_path(content: str | None) -> str | None
```

## References
- [Module: harness_core.session.context_compression](harness_core_session_context_compression) - Parent module
