"""Tests for parallel sub-agent execution and the additive async provider call.

These tests are fully mocked — no real LLM or provider network calls. They verify:

* ``run_subagents_parallel`` dispatches multiple ``(sub_agent, task)`` pairs
  concurrently (wall-time < sequential sum) and returns results in order.
* ``run_subagent`` remains a thin synchronous wrapper (backward compatible).
* ``Agent.handle_prompt`` collects both ``run_subagent`` tool results back into
  the conversation in a single turn when the model emits >1 sub-agent call.
* ``OpenAIProvider.chat_completion_async`` is a coroutine and keeps the
  normalized response shape; the sync ``chat_completion`` is unchanged.
"""

import asyncio
import inspect as _inspect
import time
from unittest.mock import MagicMock, patch, AsyncMock

from harness_core.agent import Agent, AgentType, RESPONSE, TOOL_CALL, TOOL_RESULT


# ---------------------------------------------------------------------------
# Async helper — converts an async-generator handle_prompt into a list.
# ---------------------------------------------------------------------------
def _collect_events(agent, prompt):  # type: (object, str) -> list[tuple]
    """Run ``agent.handle_prompt(prompt)`` to completion and return a flat list."""
    events = []

    async def _gather():
        async for event in agent.handle_prompt(prompt):
            events.append(event)

    asyncio.run(_gather())
    return events

from harness_core.model.provider import OpenAIProvider, Provider
from harness_core.model.types import ProviderConfig
from harness_core.tools.run_subagent import (
    run_subagent,
    run_subagents_parallel,
    _run_one,
)
from harness_core.tools.tool_result import ToolResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent_with_tool_calls(tool_calls, final_content="All done."):
    """Build an Agent whose mock provider emits *tool_calls* then ``final_content``.

    *tool_calls* is a list of dicts with keys ``name`` and ``arguments`` (the
    latter given as a JSON *string*). The provider returns these on the first
    turn, then a plain response (no tool calls) on the second turn.
    """
    agent_type = AgentType(
        model_name="test",
        system_prompt="Test",
        agent_tools=[],
    )
    agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
    provider = MagicMock(spec=Provider)
    provider.model_name = "test"

    first_output = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": f"call_{i}",
                        "type": "function",
                        "function": {"name": tc["name"], "arguments": tc["arguments"]},
                    }
                    for i, tc in enumerate(tool_calls)
                ],
            }
        }],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    second_output = {
        "choices": [{
            "message": {"role": "assistant", "content": final_content}
        }],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    # _chat() now awaits chat_completion_async — mirror the cycle there.
    it = iter([first_output, second_output])
    provider.chat_completion_async.side_effect = lambda *a, **kw: next(it)
    with patch("harness_core.model.provider.Provider.get_or_create", return_value=provider):
        return Agent(agent_type, id="parallel-subagent")


async def _fake_subagent_yield(task, delay=0.0):
    """Simulate a sub-agent ``handle_prompt`` async generator that sleeps then responds."""
    if delay:
        time.sleep(delay)
    yield (RESPONSE, f"result-for:{task}")


# ---------------------------------------------------------------------------
# run_subagent / run_subagents_parallel unit tests
# ---------------------------------------------------------------------------

class TestRunSubagentParallel:
    def test_run_subagent_single_still_works(self):
        """The synchronous single-call path must keep working via _run_one."""
        with patch("harness_core.agent.Agent") as MockAgent:
            sub = MagicMock()
            sub._agent_type = MagicMock()
            sub._agent_type.inject_extra_system_prompt = MagicMock()
            sub.handle_prompt.return_value = _fake_subagent_yield("task A")
            MockAgent.from_agent_name.return_value = sub

            result = run_subagent(MagicMock(), "analyst", "task A")

        assert result.llm_text == "result-for:task A"
        MockAgent.from_agent_name.assert_called_once()

    def test_run_subagents_parallel_empty_returns_empty(self):
        assert run_subagents_parallel([]) == []

    def test_parallel_runs_concurrently_and_in_order(self):
        """Two sub-agent calls run concurrently, results returned in order."""
        order = []
        calls = []

        def _fake_run_one(_agent, *args):
            sub_agent = args[0] if args else None
            order.append(("start", sub_agent))
            time.sleep(0.15)  # simulate work
            order.append(("end", sub_agent))
            return ToolResult(llm_text=f"out:{sub_agent}", display_text="")

        # Patch the internal worker so we control timing + observe concurrency.
        with patch("harness_core.tools.run_subagent._run_one", side_effect=_fake_run_one):
            start = time.time()
            results = run_subagents_parallel([
                ("analyst", "A"),
                ("writer", "B"),
            ])
            elapsed = time.time() - start

        # Order is preserved.
        assert [r.llm_text for r in results] == ["out:analyst", "out:writer"]
        # Concurrency: two 0.15s sleeps should finish in well under 0.30s.
        assert elapsed < 0.27, f"expected concurrent execution, took {elapsed:.2f}s"


# ---------------------------------------------------------------------------
# Integration: handle_prompt collects multiple run_subagent tool results
# ---------------------------------------------------------------------------

class TestHandlePromptParallel:
    def test_multiple_run_subagent_calls_collected_in_one_turn(self):
        """When the model emits 2 run_subagent calls, both results return next turn."""
        tool_calls = [
            {"name": "run_subagent", "arguments": '{"sub_agent": "analyst", "task": "A"}'},
            {"name": "run_subagent", "arguments": '{"sub_agent": "writer", "task": "B"}'},
        ]
        agent = _make_agent_with_tool_calls(tool_calls)

        with patch("harness_core.tools.run_subagent._run_one") as mock_run_one:
            mock_run_one.side_effect = [
                ToolResult(llm_text="FINDINGS_A", display_text=""),  # result for first sub-agent
                ToolResult(llm_text="FINDINGS_B", display_text=""),  # result for second sub-agent
            ]
            events = _collect_events(agent, "do both")

        kinds = [e[0] for e in events]
        # Two TOOL_CALL yields (both run_subagent), then two TOOL_RESULT yields.
        assert kinds.count(TOOL_CALL) == 2
        assert kinds.count(TOOL_RESULT) == 2
        # Both results were dispatched to the worker (None is passed as agent).
        dispatched = [c.args for c in mock_run_one.call_args_list]
        assert dispatched == [(None, "analyst", "A"), (None, "writer", "B")]
        # The provider's second turn had the two tool results appended (so a
        # final RESPONSE was produced).
        assert RESPONSE in kinds

    def test_single_run_subagent_uses_sequential_path(self):
        """A single run_subagent call still yields TOOL_RESULT + final RESPONSE."""
        tool_calls = [
            {"name": "run_subagent", "arguments": '{"sub_agent": "analyst", "task": "A"}'},
        ]
        agent = _make_agent_with_tool_calls(tool_calls)

        # Patch dispatch directly to return a ToolResult for run_subagent calls.
        with patch("harness_core.tools.dispatcher.dispatch") as mock_dispatch:
            def fake_dispatch(func_name, args, agent):
                if func_name == "run_subagent":
                    return ToolResult(llm_text="FINDINGS_A", display_text="")
                # For other tools, call the original dispatcher (which will raise KeyError for unknown)
                import harness_core.tools as tools_module
                mod = tools_module.DISPATCH_REGISTRY[func_name]
                fn = getattr(mod, func_name)
                result = fn(**args)
                # If it's a coroutine (because run_subagent was asyncified), await it
                if inspect.iscoroutine(result):
                    import asyncio as _asyncio
                    return _asyncio.run_coroutine_threadsafe(result, _asyncio.get_running_loop()).result()
                return result
            mock_dispatch.side_effect = fake_dispatch
            events = _collect_events(agent, "do one")

        kinds = [e[0] for e in events]
        assert kinds.count(TOOL_RESULT) == 1
        assert RESPONSE in kinds

    def test_non_subagent_tool_calls_not_parallelized(self):
        """A run_subagent mixed with a normal tool stays sequential (single call)."""
        tool_calls = [
            {"name": "execute_bash", "arguments": '{"command": "echo hi"}'},
            {"name": "run_subagent", "arguments": '{"sub_agent": "analyst", "task": "A"}'},
        ]
        agent = _make_agent_with_tool_calls(tool_calls)

        with patch("harness_core.tools.run_subagent.run_subagents_parallel") as mock_parallel:
            with patch("harness_core.tools.run_subagent.run_subagent", return_value=ToolResult(llm_text="FINDINGS_A", display_text="")):
                with patch("harness_core.tools.dispatcher.dispatch", return_value=MagicMock(llm_text="ok", display_text="")):
                    events = _collect_events(agent, "mix")

        mock_parallel.assert_not_called()
        kinds = [e[0] for e in events]
        assert kinds.count(TOOL_RESULT) == 2
        assert RESPONSE in kinds


# ---------------------------------------------------------------------------
# Additive async provider method
# ---------------------------------------------------------------------------

class TestAsyncProvider:
    def test_chat_completion_async_is_coroutine(self):
        import inspect
        assert inspect.iscoroutinefunction(OpenAIProvider.chat_completion_async)
        # Sync method must remain synchronous (not a coroutine).
        assert not inspect.iscoroutinefunction(OpenAIProvider.chat_completion)

    def test_provider_base_default_raises(self):
        async def _go():
            with patch("harness_core.model.provider.OpenAIProvider", create=True):
                # Use the abstract base directly to check the default raise.
                from harness_core.model.provider import Provider
                # Build a minimal concrete provider that does NOT override async.
                class Plain(Provider):
                    def chat_completion(self, messages, model, **kwargs):
                        return {}
                    def tokenize(self, text, model):
                        return None
                    def get_base_url(self):
                        return "x"
                p = Plain()
                try:
                    await p.chat_completion_async([], "m")
                    assert False, "should raise NotImplementedError"
                except NotImplementedError:
                    pass
        asyncio.run(_go())

    def test_chat_completion_async_mirrors_sync_shape(self):
        """Async call returns the same normalized shape as sync (no real network)."""
        provider = OpenAIProvider(MagicMock())

        # Fake a Responses-API-style response object.
        item_msg = MagicMock()
        item_msg.type = "message"
        item_msg.content = [MagicMock(text="hello")]
        item_fc = MagicMock()
        item_fc.type = "function_call"
        item_fc.call_id = "c1"
        item_fc.name = "run_subagent"
        item_fc.arguments = '{"sub_agent": "analyst", "task": "x"}'
        resp = MagicMock()
        resp.output = [item_msg, item_fc]
        usage = MagicMock(input_tokens=1, output_tokens=2, total_tokens=3)
        resp.usage = usage

        provider.client.responses.create = AsyncMock(return_value=resp)

        async def _go():
            out = await provider.chat_completion_async([{"role": "user", "content": "hi"}], "m")
            return out

        out = asyncio.run(_go())

        assert out["choices"][0]["message"]["content"] == "hello"
        assert out["choices"][0]["message"]["tool_calls"][0]["function"]["name"] == "run_subagent"
        assert out["usage"] == {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3}
