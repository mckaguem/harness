"""Regression test: user_loop must survive a failing agent turn.

user_loop now emits events (instead of calling display_* directly). We
subscribe a no-filter spy and assert the expected events are published,
including that an agent-turn failure is surfaced as an agent.tool.error event
and the loop keeps going (prompt is called again).
"""

import sys
from types import SimpleNamespace

import pytest

from harness_core.agent import loop as loop_mod
from harness_core.agent.constants import RESPONSE, ERROR
from harness_core.eventbus import EventListener, event_bus


class _EventSpy(EventListener):
    """Collect every published event on the harness topics (no sender filter)."""

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


@pytest.fixture(autouse=True)
def _reset_event_bus():
    yield
    event_bus._subscribers.clear()


class _FakeConsole:
    """Minimal stand-in for rich.console.Console."""

    is_terminal = False

    def print(self, *a, **k):
        pass


def _make_fakes(monkeypatch, agent):
    """Patch loop + downstream deps so we can call user_loop without a real TUI."""
    captured = {"events": [], "exited": False, "prompt_calls": 0}

    def fake_prompt_user(prompt=None):
        captured["prompt_calls"] += 1
        # First call: a real user message. Second call: end the loop.
        if captured["prompt_calls"] >= 2:
            return "/quit"
        return "hello"

    def fake_display_user_message(text):
        pass

    def fake_print_system(*a, **k):
        pass

    class _FakeTui:
        def show_spinner(self):
            pass

        def hide_spinner(self):
            pass

    monkeypatch.setattr(loop_mod, "prompt_user", fake_prompt_user)
    monkeypatch.setattr(loop_mod, "display_user_message", fake_display_user_message)
    monkeypatch.setattr(loop_mod, "print_system", fake_print_system)
    # Avoid any real rich.Console construction in the exception handler.
    monkeypatch.setattr(loop_mod, "Console", lambda: _FakeConsole())
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

    # Spy on the event bus so we can assert what user_loop emits.
    spy = _EventSpy()
    captured["events"] = spy.events
    return captured


class TestUserLoopResilience:
    """user_loop must stay alive across agent-turn and normal-turn scenarios."""

    def test_user_loop_survives_provider_error(self, monkeypatch):
        """An exception from handle_prompt must NOT propagate out of user_loop."""

        class BoomAgent:
            id = "test-agent"
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

        # The error should have been surfaced as an event, and the loop should
        # have tried to prompt again (i.e. it did NOT crash after the first turn).
        assert any(e.topic == "agent.tool.error" for e in captured["events"])
        assert captured["prompt_calls"] >= 2

    def test_user_loop_normal_turn_still_works(self, monkeypatch):
        """Sanity: a normal successful turn still drives handle_prompt end-to-end."""

        class OkAgent:
            id = "test-agent"
            _context_length = 4096
            _agent_type = SimpleNamespace(name="test", model_name="test")

            def handle_prompt(self, user_input):
                yield (RESPONSE, "I am the agent.", {}, None)

        agent = OkAgent()
        captured = _make_fakes(monkeypatch, agent)

        loop_mod.user_loop(agent)

        assert any(
            e.topic == "agent.turn.response"
            and getattr(e.payload, "content", None) == "I am the agent."
            for e in captured["events"]
        )
        assert captured["prompt_calls"] >= 2
