---
name: "harness_core.tools.grep._matches_file_filter"
description: "Check whether *name* matches *file_filter*."
source: "harness_core/tools/grep.py"
---

Check whether *name* matches *file_filter*.

Supports two forms:
  - glob patterns (e.g. ``"*.py"``, ``"test_*"``) via :func:`fnmatch.fnmatch`.
  - plain suffixes — if the filter has no special characters it's matched as
    a simple suffix, so ``".txt"`` matches any file ending in .txt.

## Signature
```python
_matches_file_filter(name: str, file_filter: str) -> bool
```

## References
- [Module: harness_core.tools.grep](harness_core_tools_grep) - Parent module
