# Structuring a Python Module

A well-organized Python module is readable, discoverable, and easy to test.
Follow these conventions.

## Package vs. single file

- Use a **package** (a directory with `__init__.py`) when a module grows past
  ~300 lines or has multiple cohesive concerns.
- Keep a **single file** for small, single-purpose utilities.

```
mypkg/
├── __init__.py        # Public API surface; re-export the safe subset
├── core.py            # Primary logic
├── utils.py           # Shared pure helpers
├── types.py           # Dataclasses / TypedDicts / enums
├── errors.py          # Module-specific exceptions
└── _internal.py       # Mark private modules with a leading underscore
```

## `__init__.py` discipline

Only re-export the public API. This keeps `import mypkg` cheap and signals
intent:

```python
from .core import process, Manager
from .types import Config

__all__ = ["process", "Manager", "Config"]
```

## Import ordering

Group imports in this order, with a blank line between groups:

1. Standard library (`os`, `pathlib`, `dataclasses`)
2. Third-party (`rich`, `pyyaml`, `ollama`)
3. Local application (`from agent import core`)

Use `from __future__ import annotations` at the top so PEP 604 union syntax
(`str | None`) works on all supported interpreters.

## Public vs. private

- Prefix internal names with a single underscore: `_resolve_path()`.
- A module prefixed with `_` is private to the package.
- Use double underscores only for name-mangling class internals; avoid
  elsewhere.

## Function and class design

- Prefer small, pure functions with explicit type hints on public APIs.
- Keep one class per responsibility. Group related behavior as methods.
- Document non-obvious behavior in docstrings; let code stay self-documenting.
- Return typed tuples or dataclasses rather than mutating inputs in place.

## Error handling

- Catch specific exceptions (`FileNotFoundError`, `PermissionError`,
  `TimeoutExpired`), not bare `except:`.
- Fail closed on security-sensitive operations (path traversal, secrets).
- Wrap low-level errors with descriptive context; never leak internals to logs.

## Module size and boundaries

- A module should have one clear reason to change.
- Separate logic from I/O and from presentation: keep business logic out of
  display/print code.
- Auto-discovery patterns (scanning a directory for modules) avoid central
  registration and reduce coupling.
