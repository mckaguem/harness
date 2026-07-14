"""Tests for harness.py — user_loop interactive REPL (event-driven).

user_loop no longer calls display_* helpers directly; it emits typed events
on the harness event bus. These tests subscribe a no-filter _EventSpy listener
and assert the expected events are published for each kind of turn output.
"""

from unittest.mock import MagicMock, patch

import pytest

from harness_core.agent.loop import user_loop
from harness_core.eventbus import EventListener, event_bus


class _EventSpy(EventListener):
    """Collect every published event on the harness topics (no sender filter).

    Unlike the real TUI HarnessEventListener this spy does not apply a
    filter_by_sender regex, so it captures events regardless of the agent id
    (the test agent is a MagicMock whose .id is not a real string).
    """

    TOPICS = (
        "agent.turn.start",
        "agent.turn.response",
        "agent.turn.stop",
        "agent.tool.call",
        "agent.tool.result",
        "agent.tool.error",
        "agent.status.usage",
        "agent.status.ready",
    )

    def __init__(self) -> None:
        self.events: list = []
        for topic in self.TOPICS:
            event_bus.subscribe(topic, self)

    async def handle(self, event) -> None:
        self.events.append(event)

    def count(self, topic: str) -> int:
        return sum(1 for e in self.events if e.topic == topic)


@pytest.fixture(autouse=True)
def _reset_event_bus():
    """Ensure no listener subscriptions leak between tests."""
    yield
    event_bus._subscribers.clear()


def _drive(agent, client, inputs):
    """Run user_loop feeding the given prompt inputs; return the spy."""
    spy = _EventSpy()
    calls = {"n": 0}

    def side_effect(*args):
        calls["n"] += 1
        if calls["n"] <= len(inputs):
            return inputs[calls["n"] - 1]
        raise AssertionError(f"prompt_user called too many times ({calls['n']})")

    with patch("harness_core.agent.loop.prompt_user", side_effect=side_effect):
        with patch("harness_core.agent.loop.print_system"):
            user_loop(agent, client)
    return spy


class TestRunLoop:
    """Tests for run_loop() function (now event-driven)."""

    def test_run_loop_calls_print_system_on_start(self):
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()

        spy = _drive(mock_agent, mock_client, ["/exit"])
        # /exit short-circuits before any LLM turn: no handle_prompt, no events.
        assert mock_agent.handle_prompt.call_count == 0
        assert spy.count("agent.turn.response") == 0
        assert spy.count("agent.turn.start") == 0

    def test_run_loop_handles_exit_command(self):
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()

        spy = _drive(mock_agent, mock_client, ["/exit"])
        assert mock_agent.handle_prompt.call_count == 0
        assert spy.count("agent.turn.response") == 0

    def test_run_loop_handles_quit_command(self):
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()

        spy = _drive(mock_agent, mock_client, ["/quit"])
        assert mock_agent.handle_prompt.call_count == 0
        assert spy.count("agent.turn.response") == 0

    def test_run_loop_displays_agent_response(self):
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        mock_agent.handle_prompt.return_value = [
            ("response", "Hello world!", {"eval_count": 10}, None)
        ]

        spy = _drive(mock_agent, mock_client, ["test message", "/exit"])
        assert spy.count("agent.turn.response") == 1
        assert spy.count("agent.status.usage") == 1
        assert spy.count("agent.turn.start") == 1
        assert spy.count("agent.turn.stop") == 1

    def test_run_loop_displays_tool_calls(self):
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        mock_agent.handle_prompt.return_value = [
            ("tool_call", "execute_bash", '{"command": "ls"}', None),
        ]

        spy = _drive(mock_agent, mock_client, ["test message", "/exit"])
        assert spy.count("agent.tool.call") == 1
        assert spy.count("agent.turn.start") == 1
        assert spy.count("agent.turn.stop") == 1

    def test_run_loop_displays_tool_results(self):
        from harness_core.tools.tool_result import ToolResult

        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        result_obj = ToolResult(
            llm_text="file1.txt\nfile2.txt",
            display_text="file1.txt\nfile2.txt",
            type_tag="text",
            title="execute_bash",
            theme="status",
        )
        mock_agent.handle_prompt.return_value = [
            ("tool_result", "execute_bash", result_obj, None),
        ]

        spy = _drive(mock_agent, mock_client, ["test message", "/exit"])
        assert spy.count("agent.tool.result") == 1
        assert spy.count("agent.turn.start") == 1
        assert spy.count("agent.turn.stop") == 1

    def test_run_loop_displays_errors(self):
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        mock_agent.handle_prompt.return_value = [
            ("error", "Connection timeout", None, None)
        ]

        spy = _drive(mock_agent, mock_client, ["test message", "/exit"])
        assert spy.count("agent.tool.error") == 1
        assert spy.count("agent.turn.start") == 1
        assert spy.count("agent.turn.stop") == 1

    def test_run_loop_handles_multiple_outputs(self):
        from harness_core.tools.tool_result import ToolResult

        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        result_obj = ToolResult(
            llm_text="file1.txt",
            display_text="file1.txt",
            type_tag="text",
            title="execute_bash",
            theme="status",
        )
        mock_agent.handle_prompt.return_value = [
            ("response", "Thinking...", {"eval_count": 5}, None),
            ("tool_call", "execute_bash", '{"command": "ls"}', None),
            ("tool_result", "execute_bash", result_obj, None),
        ]

        spy = _drive(mock_agent, mock_client, ["test message", "/exit"])
        assert spy.count("agent.turn.response") == 1
        assert spy.count("agent.tool.call") == 1
        assert spy.count("agent.tool.result") == 1
        assert spy.count("agent.status.usage") == 1

    def test_run_loop_ignores_unknown_command(self):
        mock_agent = MagicMock()
        mock_agent._agent_type.model_name = "test-model"
        mock_client = MagicMock()
        mock_agent.handle_prompt.return_value = [
            ("response", "Test response", {"eval_count": 10}, None)
        ]

        spy = _drive(mock_agent, mock_client, ["/unknown", "/exit"])
        # Unknown slash command falls through to the LLM: one handle_prompt call
        # and at least one agent response event.
        assert mock_agent.handle_prompt.call_count == 1
        assert spy.count("agent.turn.response") >= 1
