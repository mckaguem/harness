# Testing with pytest

`pytest` is the preferred testing framework. It is concise, auto-discovers
tests, and has rich fixture/assertion support.

## Install

```bash
pip install pytest
# or, with uv:
uv add --dev pytest
```

## Test layout

Mirror the source layout so each module has a clear test home:

```
mypkg/
├── core.py
└── utils.py
tests/
├── test_core.py
└── test_utils.py
```

Name files `test_*.py`, classes `Test*`, and functions `test_*`.

## A basic test

```python
from mypkg.core import process

def test_process_basic():
    assert process("hello") == "HELLO"
```

pytest's assertion rewriting means plain `assert` gives readable diffs — no
need for `assertEqual` style methods.

## Fixtures and isolation

Use fixtures for setup/teardown. `tmp_path` is a built-in fixture providing a
unique temporary directory:

```python
def test_writes_file(tmp_path):
    target = tmp_path / "out.txt"
    target.write_text("data")
    assert target.read_text() == "data"
```

For switching working directory or mocking external calls:

```python
from unittest.mock import patch

def test_calls_client():
    with patch("mypkg.core.OllamaClient") as client:
        client.return_value.chat.return_value = {"ok": True}
        result = run_chat()
    assert result == {"ok": True}
```

## Grouping with classes

Organize related cases into classes for readability:

```python
class TestEditFileSafety:
    def test_rejects_traversal(self):
        ...
    def test_atomic_rollback(self):
        ...
```

## Running

```bash
pytest                      # Run everything
pytest tests/test_core.py   # One file
pytest -k "safety"          # Filter by name substring
pytest -x                   # Stop on first failure
pytest --lf                 # Re-run last failures
pytest -q                   # Quiet summary
pytest --cov=mypkg          # Coverage (needs pytest-cov)
```

Prefer any repo-provided command (e.g. `make test` or `pytest tests/`) from
`README.md` or `pyproject.toml`.

## Best practices

- Assert on both return values **and** side effects (file content, directory
  state, mock call counts).
- Keep tests independent — no shared mutable global state between cases.
- Mock network/filesystem boundaries, not your own logic.
- One behavior per test; name tests by the behavior they verify.
- Run mypy and pytest together in CI before merging.
