---
name: "harness_core.utils.project_root"
description: "Detect the project root directory by looking for common project markers."
source: "harness_core/utils.py"
---

Detect the project root directory by looking for common project markers.

This function searches upwards from the starting path for common project
markers (.git directory, pyproject.toml file, .harness_py directory) and
returns the Path object for the project root.

Args:
    start_path: The starting path for the search. If None, uses the
        current working directory. Can be a string path or a Path object.

Returns:
    Path: The project root directory.
    
Raises:
    FileNotFoundError: If no project markers can be found after reaching
        the filesystem root.

Examples:
    >>> # From within a module:
    >>> root = project_root()
    >>> # From a specific location:
    >>> root = project_root("/some/path/to/start/from")

## Signature
```python
project_root(start_path: str | Path | None) -> Path
```

## References
- [Module: harness_core.utils](harness_core_utils) - Parent module
