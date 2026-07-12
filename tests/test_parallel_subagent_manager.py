"""Tests for the SubagentManager + background run_subagent/await_subagent mechanism.

Fully mocked — ``harness_core.tools.run_subagent._run_one`` is patched so no
real LLM or sub-agent is spawned. These tests verify:

* ``manager.launch`` returns an incrementing ``"subagent-<n>"`` identifier.
* Background jobs actually run concurrently (wall-time < sum of sleeps).
* ``await_one`` returns results by id and by FIRST_COMPLETED (no id).
* ``await_one`` raises when nothing is running.
* Max-concurrency enforcement surfaces as an error ToolResult.
* The synchronous ``run_subagent(block=True)`` path is preserved.
* ``run_subagent(block=False)`` returns an identifier-bearing ToolResult.
* The new ``await_subagent`` tool is auto-discovered in DISPATCH_REGISTRY.
"""

import re
import time
from concurrent.futures import Future
from unittest.mock import MagicMock, patch

from harness_core.tools.run_subagent import run_subagent
from harness_core.tools.subagent_manager import SubagentManager
from harness_core.tools.tool_result import ToolResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_run_one_factory(sleep_for=0.0):
    """Return a fake ``_run_one`` that optionally sleeps then yields a result."""

    def _fake_run_one(sub_agent, task):
        if sleep_for:
            time.sleep(sleep_for)
        return ToolResult(
            llm_text=f"result-for:{sub_agent}:{task}",
            display_text="",
            type_tag="text",
            title="info",
            theme="info",
        )

    return _fake_run_one


# ---------------------------------------------------------------------------
# Manager-level tests
# ---------------------------------------------------------------------------

class TestSubagentManager:
    def test_launch_returns_identifier(self):
        mgr = SubagentManager(max_concurrent=2)
        with patch("harness_core.tools.subagent_manager._run_one") as mock_run:
            mock_run.side_effect = _fake_run_one_factory()
            ident = mgr.launch("analyst", "task A")
        assert ident == "subagent-1"

    def test_launch_returns_incrementing_identifiers(self):
        mgr = SubagentManager(max_concurrent=4)
        with patch("harness_core.tools.subagent_manager._run_one") as mock_run:
            mock_run.side_effect = _fake_run_one_factory()
            ids = [mgr.launch("analyst", f"task{i}") for i in range(3)]
        assert ids == ["subagent-1", "subagent-2", "subagent-3"]

    def test_launch_runs_in_background_and_await_returns_result(self):
        mgr = SubagentManager(max_concurrent=4)
        fake = _fake_run_one_factory(sleep_for=0.1)

        with patch("harness_core.tools.subagent_manager._run_one", side_effect=fake):
            start = time.time()
            id_a = mgr.launch("analyst", "A")
            id_b = mgr.launch("writer", "B")
            # Both launched — they should be running concurrently.
            assert mgr.active_count() == 2
            assert mgr.is_running(id_a) and mgr.is_running(id_b)

            res_a = mgr.await_one(id_a)
            res_b = mgr.await_one(id_b)
            elapsed = time.time() - start

        assert res_a.llm_text == "result-for:analyst:A"
        assert res_b.llm_text == "result-for:writer:B"
        # Two 0.1s sleeps running concurrently should finish in < 0.25s.
        assert elapsed < 0.25, f"expected concurrent execution, took {elapsed:.2f}s"
        assert mgr.active_count() == 0

    def test_await_without_id_returns_first_completed(self):
        mgr = SubagentManager(max_concurrent=4)
        # First job sleeps longer; second finishes first and should be returned.
        with patch("harness_core.tools.subagent_manager._run_one") as mock_run:
            def _fake(sub_agent, task):
                time.sleep(0.2 if sub_agent == "slow" else 0.05)
                return ToolResult(llm_text=f"result-for:{sub_agent}", display_text="")

            mock_run.side_effect = _fake
            id_slow = mgr.launch("slow", "A")
            id_fast = mgr.launch("fast", "B")
            res = mgr.await_one(None)

        assert res.llm_text == "result-for:fast"
        # "fast" should have been removed; "slow" still running.
        assert mgr.is_running(id_slow) is True
        assert mgr.is_running(id_fast) is False

    def test_await_none_running_raises(self):
        mgr = SubagentManager(max_concurrent=4)
        try:
            mgr.await_one()
            assert False, "expected RuntimeError"
        except RuntimeError as exc:
            assert "No running subagents to await" in str(exc)

    def test_await_unknown_identifier_raises(self):
        mgr = SubagentManager(max_concurrent=4)
        try:
            mgr.await_one("subagent-99")
            assert False, "expected RuntimeError"
        except RuntimeError as exc:
            assert "No running subagent with identifier" in str(exc)

    def test_max_concurrency_blocks_further_launches(self):
        mgr = SubagentManager(max_concurrent=2)
        fake = _fake_run_one_factory(sleep_for=0.3)  # keep them busy

        with patch("harness_core.tools.subagent_manager._run_one", side_effect=fake):
            id1 = mgr.launch("analyst", "A")
            id2 = mgr.launch("writer", "B")
            assert mgr.active_count() == 2
            try:
                mgr.launch("sysadmin", "C")
                assert False, "expected RuntimeError for max concurrency"
            except RuntimeError as exc:
                assert "Maximum number of concurrent subagents" in str(exc)
            finally:
                # Clean up the two in-flight jobs so we don't leak threads.
                mgr.await_one(id1)
                mgr.await_one(id2)

    def test_max_concurrency_via_tool_error_result(self):
        """Surfaced as an error ToolResult via run_subagent(block=False)."""
        from harness_core.tools.subagent_manager import manager

        manager.MAX_CONCURRENT = 2
        manager._futures.clear()
        fake = _fake_run_one_factory(sleep_for=0.3)

        with patch("harness_core.tools.subagent_manager._run_one", side_effect=fake):
            r1 = run_subagent("analyst", "A", block=False)
            r2 = run_subagent("writer", "B", block=False)
            assert "subagent-" in r1.llm_text
            assert "subagent-" in r2.llm_text
            r3 = run_subagent("sysadmin", "C", block=False)
            # Third launch beyond the limit -> error ToolResult.
            assert r3.theme == "error"
            assert "Maximum number of concurrent subagents" in r3.llm_text
            # Drain the running jobs.
            manager.await_one()
            manager.await_one()


# ---------------------------------------------------------------------------
# Tool-level tests (run_subagent block param + await_subagent discovery)
# ---------------------------------------------------------------------------

class TestRunSubagentTool:
    def test_run_subagent_block_true_still_synchronous(self):
        """Backward-compatible synchronous behaviour is preserved."""
        with patch("harness_core.tools.run_subagent._run_one") as mock_run:
            mock_run.side_effect = _fake_run_one_factory()
            result = run_subagent("analyst", "task A")
        # Returns a ToolResult directly (not an identifier string).
        assert isinstance(result, ToolResult)
        assert result.llm_text == "result-for:analyst:task A"
        mock_run.assert_called_once_with("analyst", "task A")

    def test_run_subagent_block_false_returns_identifier(self):
        with patch("harness_core.tools.subagent_manager._run_one", side_effect=_fake_run_one_factory()):
            result = run_subagent("analyst", "task A", block=False)

        assert isinstance(result, ToolResult)
        assert "subagent-" in result.llm_text
        # Extract the identifier and await it.
        ident = re.search(r"subagent-\d+", result.llm_text).group()
        from harness_core.tools.subagent_manager import manager

        res = manager.await_one(ident)
        assert res.llm_text == "result-for:analyst:task A"

    def test_await_subagent_tool_auto_discovered(self):
        from harness_core.tools import DISPATCH_REGISTRY

        assert "await_subagent" in DISPATCH_REGISTRY
        # It must be callable and resolve to the module's await_subagent fn.
        from harness_core.tools import await_subagent as await_mod

        assert hasattr(await_mod, "await_subagent")


class TestAwaitSubagentTool:
    def test_await_subagent_tool_roundtrip(self):
        from harness_core.tools.subagent_manager import manager

        with patch("harness_core.tools.subagent_manager._run_one", side_effect=_fake_run_one_factory()):
            launch_result = run_subagent("analyst", "task A", block=False)
            ident = re.search(r"subagent-\d+", launch_result.llm_text).group()

        from harness_core.tools import await_subagent as await_mod

        result = await_mod.await_subagent(ident)
        assert isinstance(result, ToolResult)
        assert result.llm_text == "result-for:analyst:task A"

    def test_await_subagent_none_running_returns_error(self):
        from harness_core.tools import await_subagent as await_mod
        from harness_core.tools.subagent_manager import manager

        # Ensure the shared singleton has no lingering jobs from other tests.
        manager._futures.clear()

        result = await_mod.await_subagent()
        assert result.theme == "error"
        assert "No running subagents to await" in result.llm_text
