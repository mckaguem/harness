# Code Review — Recent Changes (`HEAD~5..HEAD`)

**`harness_core/tools/run_subagent.py` — `run_subagents_parallel` (lines 254-263)**
- **HARD (`AGENTS.md` §5, Breaking changes/architectural boundaries):** `max_workers=1` serializes the gather, defeating the stated "concurrently" contract; and `asyncio.run()` inside a worker thread while a loop already runs is a deadlock/footgun. The function's docstring still promises parallel execution.
- **Smell — Shotgun Surgery / Speculative Generality:** fallback branches (`get_running_loop` + ThreadPoolExecutor) duplicate concurrency plumbing that belongs in one place. The sync `_run_one_sync` mentioned in the docstring (line 29) no longer exists — doc drift.

**`harness_core/model/model.py` — `responses(self, session)` (line ~95)**
- **HARD (`AGENTS.md` §4, Type hints on public APIs):** `session` param is untyped; return is `Dict` without precise key typing. `from harness_core.config import ...` is a mid-method lazy import, violating §4 "Imports top-of-file."

**`harness_core/agent/core.py` — `print(f"Warning: ...")` (model-build failure)**
- **HARD (`AGENTS.md` §5, Display):** raw `print()` for user-facing text; must route through `terminal_io` helpers. Mixed with `logging.exception()` in `_execute_single_tool` — inconsistent strategy.

**`harness_core/__main__.py` — `logging.basicConfig(filename='/tmp/app.log', force=True)`**
- **Judgement (`AGENTS.md` §3/§4):** hard-coded absolute `/tmp` path breaks CWD-portability and CWD-boundary ethos; `force=True` clobbers caller config. Not a security leak, but poor.

**`harness_core/model/provider.py` / `session/session.py` — vestigial `response_id`**
- **Smell — Dead Code / Speculative Generality:** `6611bc7` reverted `previous_response_id` chaining, yet `Session.response_id`, `_normalize_response(response_id=...)`, and `getattr(response,"id",None)` remain unused. Divergent change — plumbing added then abandoned.

**`harness_core/agent/task_list.py` (publish hunk)**
- **Judgement:** removed `get_running_loop`/`create_task` guard, now calls `event_bus.publish(...)` synchronously. Verify `EventBus.publish` is sync-safe; this silently changes the concurrency contract (Divergent Change).

**`harness_core/model/provider.py` — `__all__` includes `"Model"`**
- **HARD (correctness):** `Model` is not defined in `provider.py`; leaked from `model.py` import. Will break `*`-style introspection / mypy.

**Smell — Mysterious Name:** `model.py` `responses()` is a verb noun that actually performs one chat turn; arguably should be `chat_turn`. Baseline only.

---

Total findings: 8 (3 hard standard violations, 1 correctness hard, 2 judgement calls, 2 baseline smells). Worst issue: `run_subagents_parallel` silently serializes (`max_workers=1`) while promising concurrency and embedding `asyncio.run()` in a worker thread — a deadlock footgun that breaks the documented parallel contract.
