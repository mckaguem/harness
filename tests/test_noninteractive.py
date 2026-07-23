"""Tests for harness.py non-interactive (``--message``) mode.

These tests verify that ``Agent.handle_prompt`` drives a single prompt to completion
and that ``harness.parse_args`` extracts the ``--message`` flag.  The model provider
is replaced with an in-memory fake so no network/LLM calls are made. Tests consume
the async generator directly and inspect RESPONSE / TOOL_CALL / TOOL_RESULT / ERROR
events rather than relying on display patches (which no longer fire in non-interactive
mode).
"""

import asyncio
import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure the project root is importable.
sys.path.insert(0, str(Path(__file__).parent.parent))


from harness_core.agent import Agent, AgentType, RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
from harness_core.model.provider import Provider
from harness_core.model.types import ProviderConfig
from harness_core.__main__ import parse_args


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

    async def chat_completion_async(self, messages, model, **kwargs):
        """Async wrapper — consumes responses in order just like the sync version."""
        if self._responses:
            return self._responses.pop(0)
        raise RuntimeError("No more fake responses")

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
    agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
    with patch("harness_core.model.provider.Provider.get_or_create", return_value=provider):
        from harness_core.agent import Agent
        agent = Agent(agent_type, id="noninteractive-agent")
    return agent


def _simple_response(content):
    """Build a fake OpenAI-style response dict."""
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "model": "test",
        "usage": {},
    }


# ── parse_args() ───────────────────────────────────────────────────────────


class TestParseArgs:
    def test_short_flag_returns_message(self):
        assert parse_args(["-m", "hello"]) == {"message": "hello", "help": False, "log_level": logging.INFO}

    def test_long_flag_returns_message(self):
        assert parse_args(["--message", "hello world"]) == {
            "message": "hello world",
            "help": False,
            "log_level": logging.INFO,
        }

    def test_absent_flag_returns_none(self):
        assert parse_args([]) == {"message": None, "help": False, "log_level": logging.INFO}

    def test_help_short_sets_flag(self):
        assert parse_args(["-h"]) == {"message": None, "help": True, "log_level": logging.INFO}

    def test_help_long_sets_flag(self):
        assert parse_args(["--help"]) == {"message": None, "help": True, "log_level": logging.INFO}

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
    def _run_handle_prompt(self, agent, message):
        """Helper: run ``agent.handle_prompt`` to completion via asyncio.run."""
        events = []
        final_content = None

        async def collect():
            nonlocal final_content
            async for event in agent.handle_prompt(message):
                kind, *args = event
                events.append(event)
                if kind == RESPONSE:
                    final_content = args[0] if len(args) > 0 else ""

        asyncio.run(collect())
        return events, final_content

    def test_simple_message_drives_handle_prompt(self):
        """A plain message should run to completion and produce a RESPONSE."""
        provider = _FakeProvider([_simple_response("Hello there!")])
        agent = _make_agent(provider)

        events, content = self._run_handle_prompt(agent, "hello")

        kinds = [e[0] for e in events]
        assert RESPONSE in kinds
        assert content == "Hello there!"
        # The provider must have been consulted exactly once (single turn).
        assert len(provider._responses) == 0

    def test_tool_call_and_result_are_displayed(self):
        """TOOL_CALL / TOOL_RESULT events appear during handle_prompt."""
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
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=provider):
            agent = Agent(agent_type, id="noninteractive-agent")

        events, content = self._run_handle_prompt(agent, "list files")

        kinds = [e[0] for e in events]
        # Expect: TOOL_CALL -> TOOL_RESULT -> RESPONSE (tool call turn + final text).
        assert TOOL_CALL in kinds
        assert TOOL_RESULT in kinds
        assert RESPONSE in kinds
        # Extract the tool names from TOOL_CALL / TOOL_RESULT events.
        tc_funcs = [e[1] for e in events if e[0] == TOOL_CALL]
        tr_funcs = [e[1] for e in events if e[0] == TOOL_RESULT]
        assert "execute_bash" in tc_funcs
        assert "execute_bash" in tr_funcs

    def test_error_event_is_displayed(self):
        """An ERROR tuple is surfaced when the agent requests an unknown tool."""
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
        agent_type.provider_config = ProviderConfig(name="test", provider_type="openai", base_url="http://test.invalid/v1", api_key="test")
        with patch("harness_core.model.provider.Provider.get_or_create", return_value=provider):
            agent = Agent(agent_type, id="noninteractive-agent")

        events, content = self._run_handle_prompt(agent, "do something")

        kinds = [e[0] for e in events]
        assert ERROR in kinds
        # At least one error message should mention the unknown tool.
        err_msgs = [str(e[1]) for e in events if e[0] == ERROR]
        assert any("unknown_tool" in str(m).lower() for m in err_msgs)

    def test_empty_message_is_safe(self):
        """An empty message still runs without crashing."""
        provider = _FakeProvider([_simple_response("")])
        agent = _make_agent(provider)

        events, content = self._run_handle_prompt(agent, "")

        # Should still produce a RESPONSE event (even if the content is "").
        kinds = [e[0] for e in events]
        assert RESPONSE in kinds

    def test_main_help_path_exits_zero(self, capsys):
        """main(['--help']) prints usage and returns without building an agent."""
        # ``__main__.blarg`` is now async; main() returns on --help (no sys.exit).
        from harness_core.__main__ import main

        main(["--help"])
        out = capsys.readouterr().out
        assert "Usage:" in out
