---
name: "harness_core.session.context_compression.build_compressed_filepath"
description: "Build a new filepath for a compressed session file."
source: "harness_core/session/context_compression.py"
---

Build a new filepath for a compressed session file.

Args:
    filepath: The original session filepath (e.g., '/tmp/session.json').

Returns:
    A tuple containing:
        - New filepath with '-compressed-<timestamp>' inserted before the extension
        - Boolean indicating if the input was already a compressed filepath

## Signature
```python
build_compressed_filepath(filepath: str) -> tuple[str, bool]
```

## References
- [Module: harness_core.session.context_compression](harness_core_session_context_compression) - Parent module
