# Code Review: harness_core/

**Date:** 2026-03-14  
**Scope:** All Python files under `harness_core/` (~75 files)  
**Standards Applied:** AGENTS.md §4 coding conventions + Fowler code smells baseline (from *Refactoring*, ch.3)

---

## Executive Summary

The `harness_core/` module is functionally robust but carries significant technical debt across maintainability, security, and consistency dimensions. Three issues rise to **security-critical**: two path-related vulnerabilities in `session.py` and `context_compression.py` that could expose file paths or allow reading arbitrary files on disk. Beyond security, the codebase exhibits pervasive Fowler anti-patterns — *Divergent Change* in `eventbus.py` and `loop.py`, *Repeated Switches* in `task_list.py`, and *Message Chains* across multiple modules — all of which increase the cost of future changes and risk silent regressions. Style violations (import ordering, dead code, primitive obsession) are scattered throughout but collectively degrade readability and make automated tooling less effective. Prioritized remediation would yield measurable gains in both developer confidence and testability.

---

## Findings by Severity

### Critical / High Security Issues

#### 1. Path Traversal on `from_file` — `session.py:397–406`
- **File:** `harness_core/session.py`, lines 397–406
- **Issue:** `from_file` reads a YAML session file at an arbitrary user-supplied path with zero safety validation. Unlike `harness_core/tools/utils.py:9` which has `is_safe_path()`, this codepath can read any file on disk (e.g., `/etc/passwd`) if called with a malicious filepath. It also raises raw `FileNotFoundError` / `ValueError` that could leak paths to the LLM via traceback.
- **Excerpt:**
  ```python
  # from_file at lines 397–406 — no is_safe_path() guard, raw exceptions possible
  def from_file(filepath: Path) -> "Session": ...
  ```
- **Fix:** Call `is_safe_path(filepath)` before any file operation; catch and wrap exceptions in a typed error tuple or sanitized exception class that doesn't leak the path string to untrusted consumers (the LLM).

#### 2. Path Leak to LLM via Display Stream — `context_compression.py:19, 460`
- **File:** `harness_core/session/context_compression.py`, lines 19 and 460
- **Issue:** The comment on lines 458–459 acknowledges a rule against leaking paths to the LLM, but the code does not follow it. `print_system("Compress", ...)` emits messages directly into the agent's display stream which includes file paths via `_auto_save_session` setting `self.filepath`. While this specific call doesn't print a path directly, it is inconsistent with the documented "fail closed" requirement and uses a `print` side-effect instead of returning a typed error tuple.
- **Excerpt:**
  ```python
  # Lines 458–459 comment acknowledges rule but code diverges:
  print_system("Compress", ...)  # emits into display stream that includes file paths
  ```
- **Fix:** Return a typed `Result`-style tuple or raise a specific handled exception that callers can translate to a non-leaking user message.

#### 3. Overly Broad Exception Catch Swallows Shutdown Signals — `session.py:133`
- **File:** `harness_core/session.py`, line 133
- **Issue:** `_auto_save_session` catches bare `Exception` which includes `KeyboardInterrupt` and `SystemExit`. This means Ctrl+C during auto-save is silently swallowed, leaving the process in an inconsistent state. The comment acknowledges this should surface but the code contradicts it by catching all exceptions.
- **Excerpt:**
  ```python
  # Line 133 — bare Exception swallows KeyboardInterrupt/SystemExit
  try: ...
  except Exception as e:
      print_system("Warn", ...)
  ```
- **Fix:** Catch `(OSError, IOError)` specifically; let `KeyboardInterrupt` propagate naturally. Also wrap the warning message in a safe error tuple instead of leaking the filepath directly.

---

### Medium — Maintainability & Architecture

#### Fowler Anti-Patterns

##### Divergent Change — `eventbus.py:306–346`
- **File:** `harness_core/eventbus.py`, lines 306–346
- **Issue:** `publish()` has five nested try/except levels for thread-safe delivery; partially duplicated in `send_direct()` and `publish_to_topic()` which don't handle threading. This inconsistency could hide real bugs if callers run off-thread.
- **Fix:** Extract `_deliver_to_agent(self, event, agent_id)` helper so all paths share identical safety semantics.

##### Repeated Switches — `task_list.py:21, 130–131, 219, 224`
- **File:** `harness_core/task_list.py`, lines 21, 130–131, 219, 224
- **Issue:** The tuple `("pending", "in_progress")` appears in four places: constant definition (line 21), `initialize_tasks()` guard (lines 130–131), `all_complete()` (line 219), and `next_uncompleted_task()` (line 224). Every time you add a new active status, you must update three call sites — textbook *Repeated Switches*.
- **Fix:** Add a property or method on `Task`:

  ```python
  @property
  def is_active(self) -> bool:
      return self.status in ("pending", "in_progress")
  ```

  Then all four sites become `t.is_active`, which is more readable and has one edit point. Alternatively, add a classmethod `TaskList.active_statuses()` returning the tuple.

##### Large Method / Divergent Change — `core.py:216`
- **File:** `harness_core/agent/core.py`, line 216
- **Issue:** `handle_prompt()` runs ~130 lines and handles at least six distinct concerns: input preparation, LLM response loop, block-when-tasks-incomplete logic, JSON parsing errors, parallel sub-agent dispatch, termination circuit breaking. One logical change (e.g., adding a new tool) forces edits in multiple places within this method.
- **Fix:** Extract at least three methods: `_run_response_loop()`, `_execute_tool_call(tool_call, args, response)`, and `_handle_parallel_subagents(pending_parallel, response)`. Aim for ~30-line methods.

##### Message Chain — `eventbus.py:148–150`
- **File:** `harness_core/eventbus.py`, lines 148–150
- **Issue:** Unnamed tuple `Tuple[Queue, Optional[Loop]]` stored in `_mailboxes`; every access site unpacks as `mailbox, loop = entry`, obscuring intent.
- **Fix:** Replace with:

  ```python
  @dataclass(frozen=True)
  class AgentEntry:
      mailbox: Queue[Any]
      loop: Optional[asyncio.AbstractEventLoop]
  ```

##### Message Chain — `task_list.py:188–205`
- **File:** `harness_core/task_list.py`, lines 188–205
- **Issue:** `_build_next_task_info()` chains `self.next_uncompleted_task()` then manually copies fields into new `NextTaskInfo`. Method could be simpler if `next_uncompleted_task()` returned `NextTaskInfo` directly; currently callers that only need "any incomplete?" (`has_incomplete_tasks`) still trigger full info construction.
- **Fix:** Refactor so the task lookup and info assembly are decoupled, or have `next_uncompleted_task()` accept a flag for full vs minimal return.

##### Message Chain — `context_compression.py:278–316`
- **File:** `harness_core/session/context_compression.py`, lines 278–316
- **Issue:** `filename_by_tool_id` accumulation only happens for messages BEFORE the compression split point (`tail_start_index`). Any tool_calls in preserved last messages are never indexed. While semantically correct (preserved messages won't be compressed so lookups aren't needed), comments imply more general purpose than what's actually used.
- **Fix:** Rename to clarify scope — e.g., `filename_by_tool_id_for_compressible_messages` — or add clarifying comment noting that only prefix messages are indexed because suffix messages are preserved verbatim.

##### Message Chain — `session.py:165–171`
- **File:** `harness_core/session.py`, lines 165–171
- **Issue:** `get_messages()` simply returns `self.messages` with no additional logic; callers could access the attribute directly. Indirection exists only because callers might want to add filtering/transformation later, but that hasn't materialized.
- **Fix:** Either remove this accessor (callers use `session.messages` directly) or give it purpose — e.g., auto-inject pending text filter system messages. Right now it's a pure passthrough.

##### Middle Man — `core.py:353–367`
- **File:** `harness_core/agent/core.py`, lines 353–367
- **Issue:** `Agent.user_loop()` is a wrapper that only calls `loop.user_loop(self, ...)`. Callers can reach the same function directly via `from harness_core.agent.loop import user_loop`. The instance method adds nothing and creates confusion about which one is "real".
- **Fix:** Remove `Agent.user_loop()` entirely; update callers (e.g., `__main__.py`, TUI code) to call `loop.user_loop(agent)` directly. If a polymorphic surface is needed for sub-agents, keep it as one-liner but document it clearly.

##### Middle Man — `session.py:165–171`
- (See Message Chain entry above; same method exhibits both patterns.)

#### Standard Violations & Other Medium Issues

##### Fragile Invariant Placement — `eventbus.py:419`
- **File:** `harness_core/eventbus.py`, line 419
- **Issue:** `task_done()` sits outside the try/except block; if an exception slips through `_handle_incoming` that isn't caught, `task_done()` never fires, leaking queue backpressure tracking.
- **Fix:** Move into a `finally` block.

##### Fragile Accessing Private `_thread` Attribute — `eventbus.py:320–322 & 336–346`
- **File:** `harness_core/eventbus.py`, lines 320–322 and 336–346
- **Issue:** Two fallback paths (`call_soon_threadsafe` → direct `put_nowait`) mean no single documented contract for cross-thread delivery; different loop implementations behave differently.
- **Fix:** Use `asyncio.current_task()` + thread ID comparison as a more portable check, or rely on `call_soon_threadsafe` alone which is the documented API.

##### Speculative Generality — `eventbus.py:27–48`
- **File:** `harness_core/eventbus.py`, lines 27–48
- **Issue:** `_event_loop` global with dead public API `set_event_loop()`/`get_event_loop()` advertised in module docstring but the actual publish path never reads it; the publish method determines thread affinity via `loop._thread` attribute (line 320), not by consulting this global.
- **Fix:** Either wire `_event_loop` into publish path as fallback when `loop._thread` is unavailable, or remove it along with public API.

##### Speculative Generality — `loop.py:15–42`
- **File:** `harness_core/agent/loop.py`, lines 15–42
- **Issue:** `_check_and_compress_if_needed()` is a module-level function with its own `getattr`-based resilience pattern trying both `agent.session` and `agent._session`; the `getattr` dance suggests compression check doesn't trust public API, indicating either future compatibility concern or that current Session interface is incomplete.
- **Fix:** If `agent.session` and `agent.context_length` are guaranteed to exist for any Agent passed here (which they should be per public API), remove the `getattr` fallbacks; if not, put this logic on `Agent` itself where it belongs — don't let module-level function introspect private attributes.

##### Divergent Change Risk — `context_compression.py:473–482`
- **File:** `harness_core/session/context_compression.py`, lines 473–482
- **Issue:** Change-detection logic compares string lengths to decide whether compression made any modifications; this is fragile if `TRUNCATED_PREFIX` (61 chars) happens to equal the length of some original content. Function returns `None` (no change) even though semantic content was altered. It also fails to detect cases where halved-content truncation preserves byte length through coincidental alignment.
- **Fix:** Compare content equality (`orig_content != comp_content`) instead of length; this is semantically correct and eliminates the edge case entirely.

##### Divergent Change — `session.py:430`
- **File:** `harness_core/session.py`, line 430
- **Issue:** `_agent_type_name` set via constructor (lines 425–426) and then overridden on line 430 if comment was found in file; two separate code paths set same attribute making logic harder to follow and test.
- **Fix:** Remove redundant assignment — constructor already receives `loaded_agent_type` or `"main"`; delete lines 429–430.

##### Divergent Change — `session_utils.py:206–221`
- **File:** `harness_core/session/session_utils.py`, lines 206–221
- **Issue:** `create_run_folder` both creates a timestamped directory AND sets global `_CURRENT_RUN_FOLDER`; these are two distinct responsibilities. If someone wants to create run folder without setting it as "current" (e.g., for archival purposes), they can't — side effect is baked in.
- **Fix:** Split into `_create_run_folder_path()` (pure, returns `Path`) and `activate_run_folder(path)` (sets global); callers compose as needed.

##### Speculative Generality + Primitive Obsession — `session_utils.py:226–237`
- **File:** `harness_core/session/session_utils.py`, lines 226–237
- **Issue:** `_CURRENT_RUN_FOLDER` is a module-level mutable global; while documented as "no active run", this pattern makes the module stateful and non-reentrant. Two concurrent threads/processes using same Python interpreter would clobber each other's `run_folder`; also means tests can't easily isolate session behavior — a test that calls `create_run_folder()` affects all subsequent calls in same process.
- **Fix:** Use `contextlib.contextmanager` or `threading.local()` for scoped run-folder tracking, or make run folder parameter passed explicitly through call chains rather than hidden global.

##### Message Chain — `session_utils.py:179–203`
- **File:** `harness_core/session/session_utils.py`, lines 179–203
- **Issue:** `ensure_sessions_dir` has three branches for determining base path (1) `base_path is None` and run_folder exists, (2) `base_path is None` and no run_folder, (3) `base_path provided`. This isn't switch on discriminated type — it's just conditional logic that could be flattened with early returns.
- **Fix:** Use early returns or single assignment with `or`:

  ```python
  return get_current_run_folder() or (project_root() / ".sessions")
  ```

##### Primitive Obsession — `event_types.py:167`
- **File:** `harness_core/eventbus/event_types.py`, line 167
- **Issue:** Hardcoded error title `title: str = "Auto-Compression Error"`; class docstring says carries generic title and message yet default is pinned to one specific use case. Every consumer wanting different title must override explicitly, suggesting design should either have no default so callers always specify, or be split into dedicated `AutoCompressionErrorPayload`.
- **Fix:** Remove the hardcoded default, or split into a dedicated payload type for auto-compression errors.

##### Primitive Obsession — `types.py:319–329`
- **File:** `harness_core/agent/types.py`, lines 319–329
- **Issue:** `inject_extra_system_prompt()` mutates the `system_prompt` field of a dataclass using string concatenation. While technically valid (dataclasses are mutable), this is a primitive string standing in for domain concept "the augmented system prompt" that deserves its own type or at least validation; method also provides no way to undo the injection, making tests hard.
- **Fix:** Consider a `SystemPrompt` dataclass with `.append()` method that tracks versions, or at minimum validate non-empty input. Rename to `_augment_system_prompt` and document that it's irreversible (which callers should know before invoking).

##### Primitive Obsession — `session_utils.py:91–157`
- **File:** `harness_core/session/session_utils.py`, lines 91–157
- **Issue:** `parse_session_yaml` returns `(list[dict], str | None)` where `None` means success and string means failure; this is the project's documented pattern but inconsistently applied. Most other functions raise exceptions or return `True/False` tuples (e.g., `export_session`). While not a violation of stated standard, inconsistency across module makes error handling unpredictable for callers.
- **Fix:** Either adopt consistent `Result` dataclass across module (`result.success` / `result.error`) or convert this function to raise specific `SessionParseError`. Don't mix styles.

##### Refused Bequest / Speculative Generality — `core.py:48–49`
- **File:** `harness_core/agent/core.py`, lines 48–49
- **Issue:** Provider creation swallows any exception with `print()` warning but agent then proceeds to use `self._provider` which is `None`. If `_chat()` called before real error surfaces (e.g., at line 145 where it checks for None), failure mode is `RuntimeError` deep in call stack with no context about original provider issue.
- **Fix:** Either (a) re-raise a typed error (`ProviderError`) and fail agent construction loudly, or (b) store the exception for later surfacing. Current pattern is speculative — assumes any failure is recoverable without proving it.

##### Mysterious Name — `core.py:135`
- **File:** `harness_core/agent/core.py`, line 135
- **Issue:** `_chat()` doesn't just chat — it normalizes provider responses, extracts timing data, assembles complex `resp_dict`. The name hides its breadth; also missing return type hint (only `_provider: Optional[Provider]` is hinted).
- **Fix:** Rename to `_request_completion()` or `_call_provider_and_normalize()`. Add typed return `-> dict[str, Any]` at minimum.

##### Long Lines / Repeated Switch Shape — `loop.py:125–139`
- **File:** `harness_core/agent/loop.py`, lines 125–139
- **Issue:** Lines 131 and 139 are 160+ characters; `elif kind == TOOL_CALL:` and `elif kind == TOOL_RESULT:` branches both extract fields from output tuple, build payload, publish — this pattern repeats for each kind and should be factored into per-kind handler methods or dispatch table.
- **Fix:** Extract `_handle_response()`, `_handle_tool_call()`, `_handle_tool_result()` methods that take the output tuple and call `agent.publish`; this also makes adding new event kinds a single new method rather than editing loop.

##### Hidden Concurrency Bug — `task_list.py:98–106`
- **File:** `harness_core/task_list.py`, lines 98–106
- **Issue:** `_emit()` uses `loop.create_task(event_bus.publish(...))` but never awaits it; if loop exits before task completes, event is silently dropped. Worse, if two emits happen in rapid succession both tasks share same `event_bus.publish()` coroutine reference without synchronization — depending on `EventPublisher.publish()`'s internals this could produce lost or duplicated events.
- **Fix:** Either await publish (if caller can be async), or use fire-and-forget with error handling (`create_task` + `add_done_callback` logging failures); document semantics explicitly. For tests that mock `_emit`, this should also have optional synchronous path for deterministic testing.

##### Overly Broad except Exception — `loop.py:160–161`
- **File:** `harness_core/agent/loop.py`, lines 160–161
- **Issue:** Catches everything including `KeyboardInterrupt`, `SystemExit`. Any future Python exception added to output protocol (e.g., cancellation signal) would be silently caught and formatted as tool error rather than propagated. Comment says "defensive" but defensive doesn't mean universal — specific exceptions should be listed.
- **Fix:** Use narrower catch e.g., `except (RuntimeError, json.JSONDecodeError)`, or explicitly exclude `BaseException` subclasses that should propagate; document which exceptions are expected from `handle_prompt`.

---

### Low — Style & Minor Improvements

#### Import Ordering Violations

| File | Line(s) | Issue |
|------|---------|-------|
| `config.py` | 8–9 | `yaml` import sits between stdlib and local `harness_core.utils` import, breaking documented convention: stdlib → third-party → local. Fix: move `import yaml` above the local import. |
| `loop.py` | 9 | `json` imported on line 9 but used at line 135 inside loop body; should be grouped with other stdlib imports at top (`time`, `traceback`) and sorted before first local import per AGENTS.md convention. Fix: move `import json` to line 3 after `traceback`, before first local import. |
| `context_compression.py` | 100 | Local import of stdlib inside function body — `json` imported only because used in one branch; micro-optimization with no real benefit, adds cognitive overhead. Fix: move to top-of-file alongside `import os`, `re`. |

#### Dead Code & Unused Imports

| File | Line(s) | Issue |
|------|---------|-------|
| `__main__.py` | 180 | Ternary always returns 0 — `return 0 if result is True else 0`; both branches return 0, the `if` is dead code. Either `/exit` and `/quit` should return non-zero exit codes (and that logic was lost) or this line should simply be `return 0`. |
| `session_utils.py` | 171 | Dead import — `import time` is never used; function uses `datetime.now().microsecond` (line 174) for nanosecond-like uniqueness, not `time.time()`. Likely left from earlier version that used `time.time_ns()` or similar. Fix: delete the line. |

#### Speculative Generality — Module-Level Globals

| File | Lines | Issue |
|------|-------|-------|
| `eventbus.py` | 27–48 | `_event_loop` global with dead public API `set_event_loop()`/`get_event_loop()` advertised in module docstring but ACTUAL publish path never reads it; the publish method determines thread affinity via `loop._thread` attribute (line 320), not by consulting this global. Fix: either wire into publish path as fallback, or remove along with public API. |

#### Primitive Obsession — Hardcoded Values

| File | Lines | Issue |
|------|-------|-------|
| `config.py` | 237 | Magic number for default context length `cl_value = 262144` (which is `256 * 1024`). Surrounding comment says "conservative context length" but doesn't explain value, units, or why this specific number was chosen; future readers will wonder if it's correct. Fix: replace with `DEFAULT_CONTEXT_LENGTH = 256 * 1024` as module constant then reference the constant here and at line 237. |
| `session.py` | 319–328 | Hardcoded delimiters `[SYSTEM STATE]` and `[USER NEW INSTRUCTION]` embedded directly in string; if caller wants different delimiters (e.g., XML-style) they can't. Not configurable, not referenced elsewhere as shared contract. Fix: extract delimiter strings to module-level constants making them discoverable and single-source, or parameterize if extensibility intended. |

#### Type Annotation Issues

| File | Lines | Issue |
|------|-------|-------|
| `eventbus.py` | 210 | `# type: ignore[assignment]` suppressing real type issue — `register_agent` return annotation says returns `Queue` but actual returned value is tuple `(Queue, Optional[Loop])`. Fix: fix return annotation to match reality or return just mailbox and track loop binding separately. |
| `types.py` | 76–123 | `_replace()` inner function has three nearly-identical blocks for SKILLS, AGENTS, TOOLS — iterate items, truncate descriptions at 200 chars, build "- {name}: {desc}" lines, join with `\n`. Duplication is a smell; wants extraction into helper like `_format_items(items, name_fn, desc_fn)`. Reduces code by ~15 lines and makes adding new variables cheaper. |
| `types.py` | 270–299 | `from_file()` has five inline imports (`yaml`, `get_default_model`, `get_model_config`, `get_provider_config`, `load_harness_config`) plus three more discovery-related ones; if import structure changes this one method needs updating. Function is also edited for at least four unrelated reasons (YAML parsing, provider resolution, context-length resolution, description-building). Fix: move all imports to top of file (AGENTS.md standard); split `from_file()` into smaller helpers `_resolve_model_config()`, `_build_agent_descriptions()`. |

#### Inconsistent Error Handling

| File | Lines | Issue |
|------|-------|-------|
| `__main__.py` | 87–103 | Inconsistent error handling across discovery steps — first block has specific `RuntimeError` handler followed by broad `Exception`; second block is pure `Exception`; both swallow unexpected errors silently. Why does one get special treatment and the other doesn't? Both catch everything below `RuntimeError` including `KeyboardInterrupt`, `MemoryError`, `SystemExit` which hides real failures from operators. Fix: catch specific exception tuples (`RuntimeError`, `OSError`) in both blocks; let truly unexpected errors propagate to outer handler so they're visible in logs rather than discarded. |

#### Code Smell — Combined Imports

| File | Line(s) | Issue |
|------|---------|-------|
| `context_compression.py` | 15–16 | `import os, re` combines two stdlib imports on one line; while not a violation per se, inconsistent with project's general style of single imports and makes future import management (e.g., adding `json`) messier to track visually. Fix: split into separate lines for consistency with typical Python style guides (PEP 8). |

#### Duplicate Initialization Logic

| File | Lines | Issue |
|------|-------|-------|
| `session.py` | 56–57 vs 129–130 | `__init__` lines 54–57 and `_auto_save_session` lines 126–130 both perform exact same sequence: build YAML, write to disk at filepath derived from `ensure_sessions_dir()`. Only difference is that `__init__` constructs filepath inline while `_auto_save_session` re-computes it. This means any future change to save format (e.g., adding metadata) must be duplicated in two places. Fix: extract private `_write_to_disk(self, filepath)` helper and call it from both places. |

#### Feature Envy — Coupling Discovery to Display

| File | Lines | Issue |
|------|-------|-------|
| `discovery.py` | 91–95 | `discover_agents()` calls `print_system()` (from terminal_io) to format its warning message inline, coupling discovery module to display layer; discovery module should return structured data, formatting is a display concern. Fix: have `discover_agents()` return list of warnings as structured objects (e.g., `tuple[Path, str]`) and let caller decide how to display them; or remove this warning entirely — function already returns empty list for missing dirs which is sufficient signal. |

#### Cache Key Fragility — `discovery.py:63–64`
- **File:** `harness_core/agent/discovery.py`, lines 63–64
- **Issue:** Cache key built from stringified paths; if two `Path` objects represent same directory (e.g., `/home/user/project` vs `/home/user/./project`) they produce different cache keys and both will trigger filesystem scan. Cache also lives at module level in multi-threaded contexts — concurrent calls to `discover_agents()` with different `agents_dirs` could race on `_AGENT_DISCOVERY_CACHE`.
- **Fix:** Use `pathlib.Path.resolve()` for cache keys (canonicalizes symlinks/dots); add `asyncio.Lock` or `threading.Lock` if this module can be called from multiple threads concurrently; at minimum document single-threaded assumption.

---

## Patterns Across Modules

Several recurring patterns cut across the modules reviewed:

1. **Broad `except Exception` with silent swallowing.** Found in `eventbus.py`, `session.py`, `loop.py`, and `__main__.py`. This pattern hides real failures from operators — unexpected exceptions like `MemoryError`, `SystemExit`, or new framework-specific errors become indistinguishable from expected ones. The codebase would benefit from a documented exception taxonomy: which errors are safe to suppress, which should be logged-and-retried, and which must propagate.

2. **Missing type hints on internal/protected members.** `_chat()`, module-level helpers in `loop.py` and `context_compression.py`, and several private attributes across modules lack return type annotations. While public API is generally well-typed, the undocumented internals make it harder for static analyzers to catch bugs and for new contributors to understand expected contracts.

3. **Message Chains as a structural smell.** At least six locations use intermediate method calls that add no value (or obscuring value) between callers and data — `eventbus.py`'s mailbox tuple unpacking, `task_list.py`'s manual field copying into `NextTaskInfo`, `session.py`'s passthrough `get_messages()`. Each represents an opportunity to flatten the call graph and reduce indirection cost.

4. **Divergent Change as a maintenance risk.** `eventbus.py`, `context_compression.py`, `loop.py`, and `session_utils.py` all exhibit methods that change for multiple unrelated reasons, forcing editors to touch many lines for small logical changes. This is the single most impactful pattern because it directly drives developer time spent on edits and regression probability.

5. **Speculative Generality via globals and fallbacks.** `_event_loop` in `eventbus.py`, `getattr`-based resilience patterns in `loop.py`'s compression check, and module-level mutable global `_CURRENT_RUN_FOLDER` in `session_utils.py` all add code for hypothetical future scenarios without current benefit. They should be removed unless a concrete use case justifies them.

---

## Recommendations by Priority

1. **Fix security violations first.** Path traversal in `session.py:397–406` (missing `is_safe_path()` guard) and path leak risk in `context_compression.py:458–459` (display stream includes file paths via `_auto_save_session.filepath`) are the highest-impact items. Both can be addressed with small targeted changes that eliminate real attack surface.

2. **Address architectural smells.** *Repeated Switches* in `task_list.py` (one property adds one edit point for four call sites), *Divergent Change* in `eventbus.py:publish()` (extract `_deliver_to_agent` helper) and `loop.py:125–139` (per-kind handler methods), and the large method `handle_prompt()` in `core.py` (~130 lines, six concerns). These are high-effort but highest-return changes because they directly reduce future editing cost.

3. **Clean up style violations.** Import ordering fixes in `config.py`, `loop.py`, and `context_compression.py`; dead code removal (`__main__.py:180` ternary, `session_utils.py:171` unused import); type annotation corrections (`eventbus.py:210` return type mismatch). These are low-effort, high-clarity improvements that make the codebase more consistent with AGENTS.md conventions.

4. **Resolve concurrency and error-handling risks.** Move `task_done()` into a `finally` block in `eventbus.py:419`; narrow exception catches in `loop.py:160–161` and `session.py:133`; add error handling to fire-and-forget `_emit()` in `task_list.py:98–106`. These are small changes that prevent subtle production failures.

5. **Improve testability.** Remove Middle Man wrappers (`core.py:353–367`, `session.py:165–171`), replace module-level mutable globals with scoped alternatives (`session_utils.py:226–237`), and add synchronous fallback paths for async code paths that are currently untestable in isolation. This reduces test complexity across the board.
