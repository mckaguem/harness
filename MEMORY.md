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


## Tool Test (2026-04-05)
This session was used to verify all available tools work end-to-end:
- `list_dir` — listed the project root successfully.
- `read_file` — read pyproject.toml successfully.
- `initialize_task_list` — created a 3-item task list.
- `update_task_status` — transitioned tasks through pending → in_progress → completed.
- `run_subagent (analyst)` — dispatched an analyst sub-agent that summarized the harness project and its modules.
- `update_memory` — this message was appended to MEMORY.md as a tool-test record.
