# Static Type Checking with mypy

`mypy` is the preferred static type checker for Python. It verifies that the
types you annotate actually line up at use sites — catching bugs before
runtime.

## Install

```bash
pip install mypy
# or, with uv:
uv add --dev mypy
```

## Project configuration

Add a `[tool.mypy]` section to `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.10"
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
warn_redundant_casts = true
warn_unused_ignores = true
strict_equality = true
exclude = ["tests/", "\\.venv/", "__pycache__/"]
```

Start stricter over time: begin with `disallow_untyped_defs`, then adopt full
`strict = true` once the codebase is clean.

## Running

```bash
mypy .                      # Check the whole project
mypy src/mypkg/core.py      # Check a single file
mypy . --strict             # Maximal checking
mypy . --follow-imports=silent   # Skip checking of imported libs
mypy . --show-error-codes   # Always show error codes for triage
```

If a command is provided by the repo, prefer it (e.g. `make typecheck` or
`npm run typecheck`). Check `README.md` or `pyproject.toml` first.

## Common patterns

Use PEP 604 unions and `from __future__ import annotations`:

```python
from __future__ import annotations
from pathlib import Path

def resolve(name: str, root: Path | None = None) -> Path: ...
```

For values that may be absent, prefer `str | None` over `Optional[str>` only if
the runtime supports it; otherwise `Optional` is fine. They are equivalent.

## Handling third-party types

Add type stubs if a dependency lacks them:

```bash
pip install types-requests types-PyYAML
```

Or silence specific import errors in config:

```toml
[[tool.mypy.overrides]]
module = ["some_untyped_lib.*"]
ignore_missing_imports = true
```

## Suppressing false positives

Use `# type: ignore[code]` with the specific error code — never a bare
`# type: ignore` in strict configs (mypy warns on unused ignores):

```python
result = risky_call()  # type: ignore[union-attr]
```

## CI integration

Run mypy as a gate in CI so type regressions are caught on every push. It is
cheap and deterministic compared to runtime test failures.
