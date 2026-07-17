"""SubagentManager — registry/orchestrator for background sub-agent jobs.

This module owns the "in-flight background sub-agent" lifecycle:

* ``launch`` submits a sub-agent job to a worker thread (so each sub-agent gets
  its own ``CURRENT_AGENT`` context), returns a short identifier such as
  ``"subagent-1"``, and enforces a maximum concurrency limit.
* ``await_one`` blocks until a specific (or the first completed) background job
  finishes and returns its :class:`~harness_core.tools.tool_result.ToolResult`.

It is intentionally decoupled from the synchronous ``run_subagent`` path so that
the existing behaviour (``block=True``) is untouched. A module-level singleton
``manager`` is shared by the ``run_subagent(block=False)`` tool path and the
``await_subagent`` tool.
"""

from __future__ import annotations

import itertools
import threading
import concurrent.futures
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait

from harness_core.tools.tool_result import ToolResult

# Imported here (not lazily) so tests can patch
# ``harness_core.tools.subagent_manager._run_one`` directly. run_subagent only
# imports this module lazily (inside functions), so there is no circular import
# at module load time.
from harness_core.tools.run_subagent import _run_one


# Default max number of concurrent background sub-agents. Overridable per
# instance (e.g. ``manager.MAX_CONCURRENT = 1``) for tests.
DEFAULT_MAX_CONCURRENT = 4


class SubagentManager:
    """Track and orchestrate background sub-agent jobs."""

    def __init__(self, max_concurrent: int = DEFAULT_MAX_CONCURRENT) -> None:
        self.MAX_CONCURRENT = max_concurrent
        self._counter = itertools.count(1)
        self._futures: dict[str, Future[ToolResult]] = {}
        self._lock = threading.Lock()
        # One shared executor; sized generously so jobs aren't queued behind
        # unrelated work. The MAX_CONCURRENT guard is enforced by ``launch``.
        self._executor = ThreadPoolExecutor(
            max_workers=max(8, max_concurrent * 2),
            thread_name_prefix="subagent",
        )

    # -- public API ---------------------------------------------------------

    def launch(self, sub_agent: str, task: str) -> str:
        """Start *sub_agent*/*task* in the background and return an identifier.

        Raises:
            RuntimeError: if the number of active background jobs has already
                reached ``MAX_CONCURRENT``.
        """
        with self._lock:
            active = len(self._futures)
            if active >= self.MAX_CONCURRENT:
                raise RuntimeError(
                    f"Maximum number of concurrent subagents "
                    f"({self.MAX_CONCURRENT}) reached; await a running "
                    f"subagent before launching more."
                )
            identifier = f"subagent-{next(self._counter)}"
            future = self._executor.submit(_run_one, None, sub_agent, task)
            self._futures[identifier] = future
        return identifier

    def await_one(self, identifier: str | None = None, timeout: float | None = None) -> ToolResult:
        """Block until a background job finishes and return its ToolResult.

        Args:
            identifier: If given, wait specifically on that job's future. If
                ``None``, block until the *first* currently-running job
                completes and return its result.
            timeout: Optional per-future timeout (seconds). ``None`` = no limit.

        Raises:
            RuntimeError: if there are no running subagents to await.
            Exception: re-raises whatever the background job raised (e.g. on a
                timeout) so callers observe the real failure.
        """
        with self._lock:
            if identifier is not None:
                future = self._futures.get(identifier)
                if future is None:
                    raise RuntimeError(
                        f"No running subagent with identifier '{identifier}'."
                    )
                assert future is not None
                pending = {identifier: future}
            else:
                if not self._futures:
                    raise RuntimeError("No running subagents to await.")
                pending = dict(self._futures)

        if identifier is None:
            # Block until at least one job completes, then resolve that one.
            done, _ = wait(list(pending.values()), return_when=FIRST_COMPLETED)
            with self._lock:
                # Map the completed future back to its identifier.
                for ident, fut in list(self._futures.items()):
                    if fut in done:
                        identifier = ident
                        future = fut
                        break

        assert future is not None
        result = future.result(timeout=timeout)
        with self._lock:
            assert identifier is not None
            self._futures.pop(identifier, None)
        return result

    def active_count(self) -> int:
        """Return the number of currently in-flight background jobs."""
        with self._lock:
            return len(self._futures)

    def is_running(self, identifier: str) -> bool:
        """Return True if *identifier* refers to a still-active background job."""
        with self._lock:
            future = self._futures.get(identifier)
        return future is not None and not future.done()


# Shared singleton used by the run_subagent(block=False) path and the
# await_subagent tool.
manager = SubagentManager()
