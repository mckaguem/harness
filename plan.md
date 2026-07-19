# Remediation Plan — Recent Changes (`HEAD~5..HEAD`)

The codebase is **a bit of a mess after recent changes**: a recent revert left
dead response-chaining plumbing, several `AGENTS.md` hard-standard violations
slipped in (untyped public APIs, raw `print()` for user-facing text, an
import-time leak in `__all__`), and the headline defect — `run_subagents_parallel`
silently serializes work while still promising concurrency and embeds
`asyncio.run()` inside a worker thread. None of it is catastrophic individually,
but together they break documented contracts and the project's own style rules.

This plan turns the 8 findings from `code-review.md` into ordered,
engineer-readable steps grouped by priority. Cross-cutting verification steps and
a Definition of Done close it out.

---

## P0 — Correctness / Breaks Contracts

### P0-1. Fix `run_subagents_parallel` serialization + deadlock footgun
- **File(s):** `harness_core/tools/run_subagent.py` (lines 254–263)
- **Fixes:** HARD finding — `max_workers=1` serializes the gather (defeating the
  documented "concurrently" contract) and `asyncio.run()` inside a worker thread
  while a loop already runs is a deadlock footgun. Docstring (lines 27–30) also
  references a `_run_one_sync` that no longer exists (doc drift).
- **Action:**
  - Remove the `ThreadPoolExecutor(max_workers=1)` + `asyncio.run(...)` branch.
  - When called from an async context, `await asyncio.gather(*(run_subagent_async(...) for ...))`
    directly (the caller's loop already drives concurrency).
  - When called from a sync context (no running loop), do `return list(asyncio.run(_gather()))`
    exactly as the existing `except RuntimeError` fallback already does, but
    **without** the worker-thread `asyncio.run` wrapping.
  - Remove the in-method `import concurrent.futures` (it belongs at top of file if
    ever needed again).
  - Update the module docstring (lines 27–30) to drop the reference to the removed
    `_run_one_sync` sync wrapper and state the real async/sync entry points.

### P0-2. Remove leaked `Model` from `provider.py` `__all__`
- **File(s):** `harness_core/model/provider.py` (line 479, inside `__all__` at 474–480)
- **Fixes:** HARD correctness — `Model` is not defined in `provider.py` (it lives
  in `model.py`); it is leaked via an import. `from harness_core.model.provider import *`
  introspection and `mypy` will break.
- **Action:**
  - Delete `"Model",` from the `__all__` list.
  - Confirm `provider.py` does not otherwise rely on `Model` at module scope; if
    any internal reference exists it must be removed or correctly qualified.
  - Do **not** add a re-export — `Model` is already importable from `model.py`,
    which is the canonical location.

---

## P1 — Hard Standard Violations (`AGENTS.md`)

### P1-1. Type the `Model.responses` public API and move the lazy import
- **File(s):** `harness_core/model/model.py` (line 111 `responses(self, session)`,
  plus the mid-method `from harness_core.config import get_provider_config` at line 84)
- **Fixes:** HARD (`AGENTS.md` §4 — type hints on public APIs; imports top-of-file).
  `session` is untyped, the return is a bare `Dict` with no key typing, and the
  lazy import mid-method violates the "imports top-of-file" rule.
- **Action:**
  - Add `from harness_core.session.session import Session` (guarded under
    `TYPE_CHECKING` or imported at top since `model.py` already imports
    `provider.py` — verify no circular import; if circular, use `TYPE_CHECKING`
    plus a string annotation `"Session"`).
  - Annotate signature: `async def responses(self, session: Session) -> dict[str, Any]:`
    (or a precise `ResponseDict` TypedDict if one exists; otherwise a `dict[str, Any]`).
  - Move the `from harness_core.config import get_provider_config` to the top of
    `model.py` alongside the other top-of-file imports.

### P1-2. Route user-facing warnings through `terminal_io`, not `print()`
- **File(s):** `harness_core/agent/core.py` (lines 68 and 80 — the two
  `print(f"Warning: ...")` calls on provider/model build failure)
- **Fixes:** HARD (`AGENTS.md` §5 — Display). Raw `print()` for user-facing text
  must go through `terminal_io` helpers, and the current mixing of `print()` with
  `logging.exception()` in `_execute_single_tool` is inconsistent.
- **Action:**
  - Replace both `print(f"Warning: ...")` calls with the appropriate
    `terminal_io` helper (e.g. the warning/error printer used elsewhere). Keep the
    existing `logging.exception()` in `_execute_single_tool` as the structured
    log path, and use `terminal_io` for the user-facing surface so the two are
    consistent.
  - Verify there is no other raw `print()` for user-facing strings left in
    `core.py`; route any found ones through the same helper.

---

## P2 — Judgement Calls / Cleanup

### P2-1. Make `__main__` logging path CWD-portable and non-clobbering
- **File(s):** `harness_core/__main__.py` (lines 19–25 `logging.basicConfig(...)`)
- **Fixes:** Judgement (`AGENTS.md` §3/§4). Hard-coded absolute `/tmp/app.log`
  breaks CWD-portability/ethos, and `force=True` clobbers any caller-supplied
  logging config.
- **Action:**
  - Replace the absolute `/tmp/app.log` with a path resolved relative to the
    project/CWD (e.g. `Path.cwd() / "harness.log"` or a configurable env var).
  - Drop `force=True` so existing logging configuration is preserved when the
    harness is embedded as a library; only set a handler if none is already
    configured (check `logging.root.handlers` before calling `basicConfig`).

### P2-2. Verify `TaskList._emit` sync-safety and document the contract change
- **File(s):** `harness_core/agent/task_list.py` (line 104 `event_bus.publish(...)`)
- **Fixes:** Judgement — the review notes the prior `get_running_loop`/`create_task`
  guard was removed and `event_bus.publish(...)` is now called synchronously. This
  silently changes the concurrency contract (Divergent Change) and must be confirmed safe.
- **Action:**
  - Read `harness_core/eventbus.py` `EventBus.publish` (line 101) and confirm it is
    safe to call synchronously (no `await`, no `loop.call_soon_threadsafe` that
    requires a running loop). If it schedules onto a loop, restore a guard or
    document the constraint.
  - Update the `_emit` docstring (lines 97–102) to accurately state that emission
    is now **synchronous** and what happens when no listeners/loop are present.
  - If the synchronous call can raise in async contexts, wrap it so it degrades
    gracefully (skip emission, as the comment already intends).

---

## P3 — Baseline Smells / Polish

### P3-1. Remove vestigial `response_id` / `previous_response_id` plumbing
- **File(s):**
  - `harness_core/session/session.py` (line 52 `self.response_id: str | None = None`,
    plus comment lines 50–51)
  - `harness_core/model/provider.py` (`_normalize_response(response, response_id=None)`
    at line 255; the `response_id=` kwarg attaches `"response_id"` at line 327;
    the `getattr(response, "id", None)` callers at lines 424 and 445)
- **Fixes:** Smell — Dead Code / Speculative Generality. Commit `6611bc7` reverted
  `previous_response_id` chaining, yet `Session.response_id`, the
  `_normalize_response(response_id=...)` parameter, and `getattr(response,"id",None)`
  remain unused (Divergent Change — plumbing added then abandoned).
- **Action:**
  - Delete `self.response_id` and its comment from `session.py` (search callers
    first; if nothing reads it, remove it).
  - Remove the `response_id` parameter from `_normalize_response` and the
    `"response_id": response_id` key it adds; simplify the two callers
    (lines 424, 445) to `return _normalize_response(response)`.
  - Grep the whole tree for `response_id`/`previous_response_id` to confirm no
    remaining references before deleting.

### P3-2. Rename `Model.responses` to reflect it performs a single turn
- **File(s):** `harness_core/model/model.py` (`responses(self, session)` at line 111)
- **Fixes:** Smell — Mysterious Name. `responses()` is a verb-noun that actually
  performs one chat turn; arguably should be `chat_turn`.
- **Action:**
  - (Optional/baseline) Rename `responses` → `chat_turn` (or similar) and update
    all callers (e.g. `harness_core/agent/mixin.py` and any tests). Keep the old
    name as a deprecated alias only if external callers depend on it; otherwise
    rename outright and update references.

---

## Cross-Cutting Actions

1. **Mirror tests for new behavior.** Where a step changes observable behavior,
   add or update the corresponding test:
   - `run_subagent.py`: a test asserting `run_subagents_parallel` actually runs
     multiple sub-agents concurrently (not serial) and does not call
     `asyncio.run()` from inside a worker thread.
   - `provider.py` `__all__`: a test/introspection assertion that everything in
     `__all__` is actually defined in the module (would have caught P0-2).
   - `model.py`: a type-checking test or at least a contract note that
     `responses(self, session: Session)` is typed.
   - `task_list.py`: a test that `_emit` is safe when called with no running loop
     (covers P2-2).
2. **Run static + dynamic checks:**
   - `mypy harness_core tests` — must pass clean (validates P0-2, P1-1).
   - `pytest tests/` — must pass green (validates all behavior changes).
3. **Verify agent YAML tool lists unchanged.** The review flags that tool lists in
   agent YAMLs must not have been unintentionally altered by these changes. Re-run
   discovery / diff `.harness_py/agents/*.yaml` against `HEAD~5` and confirm
   `AGENT_TOOLS` (imported in `__main__.py` line 28) is unchanged.

---

## Definition of Done

- [ ] `run_subagents_parallel` runs sub-agents concurrently and contains no
      `asyncio.run()` inside a worker thread (P0-1).
- [ ] `provider.py` `__all__` contains only names defined in that module (P0-2).
- [ ] `Model.responses`/`chat_turn` has typed `session` + return, and no mid-method
      `config` import remains (P1-1).
- [ ] All user-facing warnings in `core.py` go through `terminal_io`, not `print()` (P1-2).
- [ ] `__main__.py` logging uses a CWD-relative path and no longer clobbers caller
      config with `force=True` (P2-1).
- [ ] `TaskList._emit` sync-safety is confirmed and documented (P2-2).
- [ ] Vestigial `response_id` plumbing removed with no dangling references (P3-1).
- [ ] `responses` → `chat_turn` rename applied or explicitly deferred with a note (P3-2).
- [ ] New/updated mirror tests cover the changed behaviors (Cross-Cutting #1).
- [ ] `mypy harness_core tests` passes clean.
- [ ] `pytest tests/` is green.
- [ ] Agent YAML tool lists (`AGENT_TOOLS`) verified unchanged from `HEAD~5`.
