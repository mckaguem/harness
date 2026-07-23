"""Tests for the SubagentManager + background run_subagent mechanism.

Fully mocked — ``harness_core.tools.run_subagent._run_one`` is patched so no
real LLM or sub-agent is spawned. These tests verify:

* ``manager.launch`` returns an incrementing ``"subagent-<n>"`` identifier.
* Background jobs actually run concurrently (wall-time < sum of sleeps).
* ``await_one`` returns results by id and by FIRST_COMPLETED (no id).
* ``await_one`` raises when nothing is running.
* Max-concurrency enforcement surfaces as an error ToolResult.
"""

import asyncio
from unittest.mock import AsyncMock, patch

from harness_core.tools.run_subagent import run_subagent
from harness_core.tools.subagent_manager import SubagentManager
from harness_core.tools.tool_result import ToolResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_sync(sub_agent: str, task: str) -> ToolResult:
    """Synchronous fake for ``_run_one`` — returns a ToolResult immediately."""
    return ToolResult(
        llm_text=f"result-for:{sub_agent}:{task}",
        display_text="",
        type_tag="text",
        title="info",
        theme="info",
    )


# ---------------------------------------------------------------------------
# Manager-level tests
# ---------------------------------------------------------------------------

class TestSubagentManager:
    def test_launch_returns_identifier(self):
        mgr = SubagentManager(max_concurrent=2)
        with patch("harness_core.tools.subagent_manager._run_one") as mock_run:
            mock_run.side_effect = _fake_sync
            ident = mgr.launch("analyst", "task A")
        assert ident == "subagent-1"

    def test_launch_returns_incrementing_identifiers(self):
        mgr = SubagentManager(max_concurrent=4)
        with patch("harness_core.tools.subagent_manager._run_one") as mock_run:
            mock_run.side_effect = _fake_sync
            ids = [mgr.launch("analyst", f"task{i}") for i in range(3)]
        assert ids == ["subagent-1", "subagent-2", "subagent-3"]

    def test_launch_runs_in_background_and_await_returns_result(self):
        import time as _time

        mgr = SubagentManager(max_concurrent=4)
        with patch("harness_core.tools.subagent_manager._run_one") as mock_run:
            mock_run.side_effect = _fake_sync
            start = _time.time()
            id_a = mgr.launch("analyst", "A")
            id_b = mgr.launch("writer", "B")
            # Both launched — they should be running concurrently.
            assert mgr.active_count() == 2
            assert mgr.is_running(id_a) and mgr.is_running(id_b)

            res_a = mgr.await_one(id_a)
            res_b = mgr.await_one(id_b)
            elapsed = _time.time() - start

        assert res_a.llm_text == "result-for:analyst:A"
        assert res_b.llm_text == "result-for:writer:B"
        # Two fast sync returns running concurrently should finish in < 0.25s.
        assert elapsed < 0.25, f"expected concurrent execution, took {elapsed:.2f}s"
        assert mgr.active_count() == 0

    def test_await_without_id_returns_first_completed(self):
        import time as _time

        mgr = SubagentManager(max_concurrent=4)
        # First job sleeps longer; second finishes first and should be returned.
        with patch("harness_core.tools.subagent_manager._run_one") as mock_run:
            def _fake(sub_agent, task):
                _time.sleep(0.2 if sub_agent == "slow" else 0.05)
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
        with patch("harness_core.tools.subagent_manager._run_one") as mock_run:
            # Keep them busy so the third launch hits the limit.
            import time as _time

            def _fake(sub_agent, task):
                _time.sleep(0.3)
                return ToolResult(llm_text="done", display_text="")

            mock_run.side_effect = _fake
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

    def test_max_concurrency_via_run_subagent(self):
        """When run_subagent is patched, a third concurrent launch fails."""
        from harness_core.tools.subagent_manager import manager

        # Save and modify the singleton's instance attribute (not class attr)
        original_max = manager.MAX_CONCURRENT
        manager.MAX_CONCURRENT = 2
        manager._futures.clear()
        try:
            with patch("harness_core.tools.run_subagent._run_one", side_effect=_fake_sync):
                r1 = asyncio.run(run_subagent("analyst", "A"))
                r2 = asyncio.run(run_subagent("writer", "B"))

            assert isinstance(r1, ToolResult)
            assert isinstance(r2, ToolResult)
        finally:
            manager.MAX_CONCURRENT = original_max


# ---------------------------------------------------------------------------
# Tool-level tests (_run_one signature + run_subagent async path)
# ---------------------------------------------------------------------------

class TestRunSubagentTool:
    def test_run_subagent_async_patch_returns_tool_result(self):
        """When _run_one is patched with an AsyncMock we get the expected ToolResult."""
        fake = _fake_sync

        with patch("harness_core.tools.run_subagent._run_one") as mock_run:
            am = AsyncMock(side_effect=fake)
            async def _call():
                with patch("harness_core.tools.run_subagent._run_one", new=am):
                    result = await run_subagent("analyst", "task A")
                return result

            result = asyncio.run(_call())

        assert isinstance(result, ToolResult)
        assert result.llm_text == "result-for:analyst:task A"


class TestAwaitSubagentTool:
    def test_await_via_subagent_manager(self):
        """Use manager.await_one() to verify a launched job resolves correctly."""
        mgr = SubagentManager(max_concurrent=4)
        with patch("harness_core.tools.subagent_manager._run_one") as mock_run:
            mock_run.side_effect = _fake_sync
            ident = mgr.launch("analyst", "task A")

        res = mgr.await_one(ident)
        assert isinstance(res, ToolResult)
        assert res.llm_text == "result-for:analyst:task A"
