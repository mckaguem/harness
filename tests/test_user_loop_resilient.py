"""Regression test: user_loop must survive a failing agent turn.

Previously, when the provider/LLM call raised inside handle_prompt, the
exception propagated out of user_loop. In the interactive (Textual) mode the
loop worker's finally-block calls app.exit(), so the *entire app closed
after a single message* ("type one thing then it exits").

This test drives the real user_loop directly with fake I/O helpers and a fake
agent whose handle_prompt raises, asserting the loop catches the error and
returns normally (so the app stays alive for the next input).
"""
import sys
from types import SimpleNamespace

import pytest

from harness_core.agent import loop as loop_mod
from harness_core.agent.constants import RESPONSE, ERROR


class _FakeConsole:
    """Minimal stand-in for rich.console.Console."""
    is_terminal = False

    def print(self, *a, **k):
        pass


def _make_fakes(monkeypatch, agent):
    """Patch loop + downstream deps so we can call user_loop without a real TUI."""
    captured = {"displayed": [], "exited": False, "prompt_calls": 0}

    def fake_prompt_user(prompt=None):
        captured["prompt_calls"] += 1
        # First call: a real user message. Second call: end the loop.
        if captured["prompt_calls"] >= 2:
            return "/quit"
        return "hello"

    def fake_display_error(text):
        captured["displayed"].append(("error", text))

    def fake_display_agent_response(content, resp, ctx):
        captured["displayed"].append(("response", content))

    def fake_display_user_message(text):
        captured["displayed"].append(("user", text))

    def fake_display_tool_call(name, args):
        captured["displayed"].append(("tool_call", name))

    def fake_display_tool_result(name, result):
        captured["displayed"].append(("tool_result", name))

    def fake_format_speed(*a, **k):
        return ""

    def fake_print_system(*a, **k):
        pass

    class _FakeTui:
        def show_spinner(self):
            pass

        def hide_spinner(self):
            pass

    monkeypatch.setattr(loop_mod, "prompt_user", fake_prompt_user)
    monkeypatch.setattr(loop_mod, "display_error", fake_display_error)
    monkeypatch.setattr(loop_mod, "display_agent_response", fake_display_agent_response)
    monkeypatch.setattr(loop_mod, "display_user_message", fake_display_user_message)
    monkeypatch.setattr(loop_mod, "display_tool_call", fake_display_tool_call)
    monkeypatch.setattr(loop_mod, "display_tool_result", fake_display_tool_result)
    monkeypatch.setattr(loop_mod, "format_speed", fake_format_speed)
    monkeypatch.setattr(loop_mod, "print_system", fake_print_system)
    monkeypatch.setattr(loop_mod, "_console", _FakeConsole())
    # Provide working /quit (and /exit) handlers so the loop can terminate
    # when our fake prompt_user returns '/quit'.
    monkeypatch.setattr(
        loop_mod, "COMMANDS",
        {"quit": lambda *a, **k: True, "exit": lambda *a, **k: True},
    )
    # intercept_message is only used for '/'-prefixed non-command input.
    monkeypatch.setattr(
        loop_mod, "intercept_message",
        lambda m: SimpleNamespace(kind="UNKNOWN", payload="", stripped_message=m),
    )
    monkeypatch.setattr(loop_mod, "_check_and_compress_if_needed", lambda *a, **k: None)

    # get_tui() must return our no-op spinner holder.
    import harness_core.terminal_io.tui as tui_mod

    monkeypatch.setattr(tui_mod, "get_tui", lambda: _FakeTui())

    return captured


def test_user_loop_survives_provider_error(monkeypatch):
    """An exception from handle_prompt must NOT propagate out of user_loop."""
    class BoomAgent:
        _context_length = 4096
        _agent_type = SimpleNamespace(name="test", model_name="test")

        def handle_prompt(self, user_input):
            # Simulate a provider/LLM failure (the real bug trigger).
            raise RuntimeError("Provider chat request failed: connection refused")
            yield  # pragma: no cover

    agent = BoomAgent()
    captured = _make_fakes(monkeypatch, agent)

    # Must return without raising.
    loop_mod.user_loop(agent)

    # The error should have been surfaced, and the loop should have tried to
    # prompt again (i.e. it did NOT crash after the first turn).
    assert any(k == "error" for k, _ in captured["displayed"]), captured
    assert captured["prompt_calls"] >= 2, captured


def test_user_loop_normal_turn_still_works(monkeypatch):
    """Sanity: a normal successful turn still drives handle_prompt end-to-end."""
    class OkAgent:
        _context_length = 4096
        _agent_type = SimpleNamespace(name="test", model_name="test")

        def handle_prompt(self, user_input):
            yield (RESPONSE, "I am the agent.", {})

    agent = OkAgent()
    captured = _make_fakes(monkeypatch, agent)

    loop_mod.user_loop(agent)

    assert any(k == "response" and v == "I am the agent." for k, v in captured["displayed"]), captured
    assert captured["prompt_calls"] >= 2, captured
