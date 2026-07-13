# Project Memory

## Working Directory
- `/workspaces/harness` — root of the project under analysis.

## Session auto-save leak (resolved)
- Problem: `Session` auto-saves to `.sessions/` by default, so tests that build a
  Session (directly or via an `Agent`) leaked hundreds of timestamped `*.yaml`
  files into `.sessions/` each run.
- Fix (commit cda13df): added `tests/conftest.py` with an autouse fixture
  `_isolate_session_writes` that monkeypatches `harness_core.session.session.ensure_sessions_dir`
  to return `tmp_path / ".sessions"` and resets the run-folder global. Also changed
  `tests/test_session.py` to use `mkdir(exist_ok=True)`.
- `.sessions/` is git-ignored; leftover pre-existing artifacts were cleaned up.
