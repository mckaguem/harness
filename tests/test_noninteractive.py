"""Tests for harness.py non-interactive (``--message``) mode.

These tests verify that ``harness.run_non_interactive`` drives
``Agent.handle_prompt`` to completion and that ``harness.parse_args`` extracts
the ``--message`` flag.  The model provider is replaced with an in-memory fake
so no network/LLM calls are made.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure the project root is importable.
sys.path.insert(0, str(Path(__file__).parent.parent))


from harness_core.agent import Agent, AgentType, RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
from harness_core.model.provider import Provider
from harness_core.__main__ import parse_args, run_non_interactive


class _FakeProvider(Provider):
    """In-memory Provider used to avoid real network calls in tests."""

    def __init__(self, responses):
        # ``responses`` is a list of dicts (OpenAI-style) consumed in order.
        self._responses = list(responses)
        self.base_url = "http://localhost.test"

    def chat_completion(self, messages, model, **kwargs):
        if self._responses:
            return self._responses.pop(0)
        # Default: a plain assistant text response with no tool calls.
        return {
            "choices": [{"message": {"role": "assistant", "content": ""}}],
            "model": model,
            "usage": {},
        }

    def tokenize(self, text, model):
        return None

    def get_base_url(self):
        return self.base_url


def _make_agent(provider, content="Hello!", tool_calls=None, model="test"):
    """Build an Agent wired to a fake provider returning one assistant turn."""
    agent_type = AgentType(
        model_name=model,
        system_prompt="You are a helpful test agent.",
        agent_tools=[],
    )
    agent = Agent(agent_type, 4096, provider=provider)
    return agent


def _simple_response(content):
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "model": "test",
        "usage": {},
    }


# ── parse_args() ───────────────────────────────────────────────────────────


class TestParseArgs:
    def test_short_flag_returns_message(self):
        assert parse_args(["-m", "hello"]) == {"message": "hello", "help": False}

    def test_long_flag_returns_message(self):
        assert parse_args(["--message", "hello world"]) == {
            "message": "hello world",
            "help": False,
        }

    def test_absent_flag_returns_none(self):
        assert parse_args([]) == {"message": None, "help": False}

    def test_help_short_sets_flag(self):
        assert parse_args(["-h"]) == {"message": None, "help": True}

    def test_help_long_sets_flag(self):
        assert parse_args(["--help"]) == {"message": None, "help": True}

    def test_unknown_option_exits_nonzero(self):
        with pytest.raises(SystemExit) as exc:
            parse_args(["--bogus"])
        assert exc.value.code == 2

    def test_missing_argument_to_flag_exits_nonzero(self):
        with pytest.raises(SystemExit) as exc:
            parse_args(["-m"])  # -m requires an argument
        assert exc.value.code == 2

    def test_help_does_not_require_message(self):
        # --help alongside --message should still flag help and not error.
        assert parse_args(["--help", "--message", "x"])["help"] is True


# ── run_non_interactive() ───────────────────────────────────────────────────


class TestRunNonInteractive:
    def test_simple_message_drives_handle_prompt(self):
        """A plain message should run to completion and produce a RESPONSE."""
        provider = _FakeProvider([_simple_response("Hello there!")])
        agent = _make_agent(provider)

        captured = {}
        with patch("harness_core.terminal_io.display_agent_response",
                   side_effect=lambda c, r, cl: captured.setdefault("content", c)), patch(
            "harness_core.terminal_io.display_user_message"), patch(
            "harness_core.terminal_io.display_tool_call"), patch(
            "harness_core.terminal_io.display_tool_result"), patch(
            "harness_core.terminal_io.display_error"):
            rc = run_non_interactive(agent, "hello")

        assert rc == 0
        assert captured["content"] == "Hello there!"
        # The provider must have been consulted exactly once (single turn).
        assert len(provider._responses) == 0

    def test_sets_current_agent_contextvar(self):
        """CURRENT_AGENT must be bound so agent-aware tools work."""
        from harness_core.agent.context import CURRENT_AGENT

        provider = _FakeProvider([_simple_response("Hi")])
        agent = _make_agent(provider)

        with patch("harness_core.terminal_io.display_agent_response"), patch(
            "harness_core.terminal_io.display_user_message"), patch(
            "harness_core.terminal_io.display_tool_call"), patch(
            "harness_core.terminal_io.display_tool_result"), patch(
            "harness_core.terminal_io.display_error"):
            run_non_interactive(agent, "hello")

        # After the run, the ContextVar should resolve to our agent on this
        # thread (set on entry and never cleared).
        assert CURRENT_AGENT.get() is agent

    def test_tool_call_and_result_are_displayed(self):
        """TOOL_CALL / TOOL_RESULT events are rendered, not swallowed."""
        # First turn requests a tool call, second turn returns a final answer.
        tool_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "execute_bash",
                            "arguments": '{"command": "ls"}',
                        },
                    }],
                }
            }],
            "model": "test",
            "usage": {},
        }
        provider = _FakeProvider([tool_response, _simple_response("Done!")])
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=["execute_bash"],
        )
        agent = Agent(agent_type, 4096, provider=provider)

        calls = []
        results = []
        with patch("harness_core.terminal_io.display_agent_response"), patch(
            "harness_core.terminal_io.display_user_message"), patch(
            "harness_core.terminal_io.display_tool_call",
            side_effect=lambda fn, a: calls.append(fn)), patch(
            "harness_core.terminal_io.display_tool_result",
            side_effect=lambda fn, r: results.append(fn)), patch(
            "harness_core.terminal_io.display_error"):
            rc = run_non_interactive(agent, "list files")

        assert rc == 0
        assert "execute_bash" in calls
        assert "execute_bash" in results

    def test_error_event_is_displayed(self):
        """An ERROR tuple is surfaced via display_error."""
        # Request an unknown tool; the agent yields ERROR then a final RESPONSE.
        bad_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "unknown_tool", "arguments": "{}"},
                    }],
                }
            }],
            "model": "test",
            "usage": {},
        }
        provider = _FakeProvider([bad_response, _simple_response("Sorry")])
        agent_type = AgentType(
            model_name="test",
            system_prompt="Test",
            agent_tools=[],
        )
        agent = Agent(agent_type, 4096, provider=provider)

        errors = []
        with patch("harness_core.terminal_io.display_agent_response"), patch(
            "harness_core.terminal_io.display_user_message"), patch(
            "harness_core.terminal_io.display_tool_call"), patch(
            "harness_core.terminal_io.display_tool_result"), patch(
            "harness_core.terminal_io.display_error",
            side_effect=lambda d: errors.append(d)):
            rc = run_non_interactive(agent, "do something")

        assert rc == 0
        assert any("unknown_tool" in str(e).lower() for e in errors)

    def test_empty_message_is_safe(self):
        """An empty message still runs without crashing."""
        provider = _FakeProvider([_simple_response("")])
        agent = _make_agent(provider)

        with patch("harness_core.terminal_io.display_agent_response"), patch(
            "harness_core.terminal_io.display_user_message"), patch(
            "harness_core.terminal_io.display_tool_call"), patch(
            "harness_core.terminal_io.display_tool_result"), patch(
            "harness_core.terminal_io.display_error"):
            rc = run_non_interactive(agent, "")

        assert rc == 0

    def test_main_help_path_exits_zero(self, capsys):
        """main(['--help']) prints usage and exits 0 without building an agent."""
        with patch("harness_core.__main__.build_agent") as mock_build:
            with pytest.raises(SystemExit) as exc:
                # Imported lazily to avoid side effects at module load.
                from harness_core.__main__ import main
                main(["--help"])
        assert exc.value.code == 0
        # build_agent must NOT be invoked in help mode.
        mock_build.assert_not_called()
        out = capsys.readouterr().out
        assert "Usage:" in out
