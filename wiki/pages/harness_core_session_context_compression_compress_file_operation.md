---
name: "harness_core.session.context_compression.compress_file_operation"
description: "Truncate a file-operating tool-result (read/write/edit) iff the underlying"
source: "harness_core/session/context_compression.py"
---

Truncate a file-operating tool-result (read/write/edit) iff the underlying
file has been modified since the message was created.

Steps:
  1. Shallow-copy ``msg`` and attempt to locate the relevant filename.
  2. Parse the message timestamp (treating naive datetimes as UTC).
     On parse failure, treat the timestamp as "old" so truncation is
     conservative.
  3. If the file exists and its mtime exceeds the parsed timestamp, it has
     been modified since this result was produced → return a copy whose
     content is replaced with :data:`TRUNCATED_PREFIX`.
  4. Otherwise return ``new_msg`` unchanged (content left alone).

If no filename can be located reliably (e.g. for write_file / edit_file
results that don't carry the path in their output), the message is returned
unchanged — it's safer not to truncate a fresh write/edit result based on
stale or nonexistent filenames.

## Signature
```python
compress_file_operation(msg: dict, filename_by_tool_id: dict[str, str] | None) -> dict
```

## References
- [Module: harness_core.session.context_compression](harness_core_session_context_compression) - Parent module
