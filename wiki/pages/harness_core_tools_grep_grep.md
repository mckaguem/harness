---
name: "harness_core.tools.grep.grep"
description: "Search for *pattern* inside files under the cwd."
source: "harness_core/tools/grep.py"
---

Search for *pattern* inside files under the cwd.

Returns a structured string of matches — one block per hit — plus a summary
count so you can decide whether to narrow the search.

Parameters
----------
pattern : str
    Literal substring (default) or Python regex when ``use_regex=True``.
path : str
    File or directory within cwd to search. Directories are searched
    recursively; binary files and paths under ``__pycache__`` / `.git/` are
    skipped automatically.
use_regex : bool, optional
    Treat *pattern* as a regex. Defaults to False.
file_filter : str | None, optional
    Optional glob/suffix filter on filenames (e.g. ``"*.py"``, ``"test_*"``).
max_matches : int, optional
    Cap the number of matches returned. Defaults to 50.

Returns
-------
ToolResult
    A ``ToolResult`` containing search results or error messages.

## Signature
```python
grep(pattern: str, path: str, use_regex: bool, file_filter: str | None, max_matches: int) -> ToolResult
```

## References
- [Module: harness_core.tools.grep](harness_core_tools_grep) - Parent module
