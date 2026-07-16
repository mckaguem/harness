"""Tests for the textual TUI in terminal_io/tui.py.

These run headless via textual's ``run_test``/``Pilot`` so they need no real
terminal and are safe in CI.  We exercise idiomatic textual patterns: widget
composition, the multi-line input submit binding, and the TUI routing that lets
the classic ``display_*`` helpers render into the output pane while a TUI is
active.

Key TUI behaviour under test:
* The output pane is a :class:`~textual.containers.VerticalScroll` of
  :class:`~textual.widgets.Static` widgets (one per renderable).
* A tool call is rendered inside a :class:`~textual.widgets.Collapsible`
  whose title matches the panel title (``"Tool: <name>"``); the matching tool
  result is appended *inline* inside that same collapsible (after a separator)
  rather than as a separate panel.

The project's pytest has no async plugin, so each async scenario is driven from
a plain ``def test_*`` via ``asyncio.run``.  Note: assertions about a pending
prompt are made *after* ``pilot.press`` returns (the key handler runs on the
app thread synchronously), so we never block the single app thread.
"""

import asyncio

import pytest

from textual.widgets import Footer, Header, TextArea, Collapsible, Static
from textual.containers import VerticalScroll

from harness_core.terminal_io.tui import TextualHarnessApp, HarnessTUI, get_tui
from harness_core.terminal_io import display
from harness_core.eventbus import Event, EventBus, event_bus
from harness_core.terminal_io.event_listener import make_event_listener, subscribe_event_listener


@pytest.fixture
def tui_app():
    """Provide a fresh app + reset controller around each test."""
    get_tui().reset()
    app = TextualHarnessApp(agent=None)
    yield app
    get_tui().reset()


def _drive(coro):
    """Run an async scenario to completion on a fresh event loop."""
    asyncio.run(coro)


class TestComposition:
    """The app composes the expected idiomatic widget tree."""

    def test_header_present(self, tui_app):
        async def _body():
            async with tui_app.run_test():
                assert tui_app.query_one(Header) is not None

        _drive(_body())


class TestEventBusIntegration:
    """Integration test for spinner visibility via the event bus.

    This test verifies the full event flow:
    1. Creates a real EventListener (HarnessEventListener)
    2. Subscribes it to agent.turn.start/stop events
    3. Emits events via the event bus
    4. Verifies the spinner visibility toggles
    """

    def test_spinner_toggles_via_event_bus(self, tui_app):
        import threading

        async def _body():
            async with tui_app.run_test() as pilot:
                controller = get_tui()
                spinner = tui_app.query_one("#spinner")
                # Hidden initially (set by bind()).
                assert spinner.display is False

                # Create a test event bus and listener for the test agent
                test_bus = EventBus()
                test_agent_id = "Agent.test"
                listener = subscribe_event_listener(test_agent_id, test_bus)

                # Allow time for subscriptions to register and background task to start
                await pilot.pause()
                await pilot.pause()

                # Emit agent.turn.start event via the event bus
                test_bus.publish_to_topic(sender=test_agent_id, topic="agent.turn.start", payload=None)

                # Allow time for event to be processed by the listener's mailbox
                await pilot.pause()
                await pilot.pause()
                await pilot.pause()

                # Spinner should now be visible
                assert spinner.display is True, "Spinner should be visible after agent.turn.start event"

                # Emit agent.turn.stop event via the event bus
                test_bus.publish_to_topic(sender=test_agent_id, topic="agent.turn.stop", payload=None)

                # Allow time for event to be processed
                await pilot.pause()
                await pilot.pause()
                await pilot.pause()

                # Spinner should now be hidden
                assert spinner.display is False, "Spinner should be hidden after agent.turn.stop event"

        _drive(_body())


class TestPromptFlow:
    """Ctrl+Enter submits the TextArea and resolves a pending prompt."""

    def test_submit_resolves_pending_prompt(self, tui_app):
        async def _body():
            async with tui_app.run_test() as pilot:
                controller = get_tui()
                # Arm a pending prompt (mirrors controller.prompt on the loop
                # thread, which blocks on an Event).  This is set from the app
                # thread, so no cross-thread blocking is needed here.
                controller._pending = __import__("threading").Event()
                controller._pending_value = ""

                text_area = tui_app.query_one("#input", TextArea)
                text_area.text = "hello world\nsecond line"
                text_area.focus()
                await pilot.press("ctrl+g")

                # The submit handler ran synchronously during pilot.press.
                assert controller._pending_value == "hello world\nsecond line"
                # Regression: the prompt box must clear on submit so it is
                # empty and ready for the next message.
                assert text_area.text == ""

        _drive(_body())

    def test_prompt_blocks_until_submit(self, tui_app):
        """A worker thread calling prompt() blocks until the app submits."""
        import threading

        result: dict = {}

        def worker() -> None:
            # This runs on a *different* thread than the app, exactly like the
            # real user_loop worker; call_from_thread is then legal.
            result["value"] = get_tui().prompt("")

        async def _body():
            async with tui_app.run_test() as pilot:
                t = threading.Thread(target=worker, daemon=True)
                t.start()
                await pilot.pause()  # let prompt() arm + focus the input
                assert tui_app.focused == tui_app.query_one("#input", TextArea)
                tui_app.query_one("#input", TextArea).text = "worker typed this"
                get_tui().submit()
                await pilot.pause()  # yield so the worker thread can finish
                t.join(timeout=2.0)
                assert result.get("value") == "worker typed this"

        _drive(_body())


class TestRouting:
    """When the TUI is active, display_* writes route into the output pane."""

    def test_is_active_true_while_running(self, tui_app):
        async def _body():
            async with tui_app.run_test():
                assert get_tui().is_active() is True

        _drive(_body())

    def test_print_system_increments_write_count(self, tui_app):
        import threading

        async def _body():
            async with tui_app.run_test() as pilot:
                controller = get_tui()
                before = controller.write_count()
                # Call the display helper from a *different* thread (as the
                # loop worker would), so call_from_thread is legal.
                t = threading.Thread(
                    target=lambda: display.print_system("Title", "body message"),
                    daemon=True,
                )
                t.start()
                t.join(timeout=2.0)
                await pilot.pause()  # flush the scheduled write on the app thread
                assert controller.write_count() == before + 1

        _drive(_body())

    def test_display_message_panel_routes_to_tui(self, tui_app):
        import threading

        async def _body():
            async with tui_app.run_test() as pilot:
                controller = get_tui()
                before = controller.write_count()
                t = threading.Thread(
                    target=lambda: display.display_message_panel(
                        "plain output", theme="info", result_type="text"
                    ),
                    daemon=True,
                )
                t.start()
                t.join(timeout=2.0)
                await pilot.pause()
                assert controller.write_count() == before + 1

        _drive(_body())

    def test_display_error_routes_to_tui(self, tui_app):
        import threading

        async def _body():
            async with tui_app.run_test() as pilot:
                controller = get_tui()
                before = controller.write_count()
                t = threading.Thread(
                    target=lambda: display.display_error("something broke"),
                    daemon=True,
                )
                t.start()
                t.join(timeout=2.0)
                await pilot.pause()
                assert controller.write_count() == before + 1

        _drive(_body())

    def test_display_user_message_routes_to_tui(self, tui_app):
        """The user's own typed message must appear in the output pane.

        Regression test: previously nothing echoed the user's input into the
        output pane, so messages were invisible in the TUI alongside the
        agent's responses.
        """
        import threading

        async def _body():
            async with tui_app.run_test() as pilot:
                controller = get_tui()
                before = controller.write_count()
                t = threading.Thread(
                    target=lambda: display.display_user_message(
                        "hello from the user"
                    ),
                    daemon=True,
                )
                t.start()
                t.join(timeout=2.0)
                await pilot.pause()
                assert controller.write_count() == before + 1

        _drive(_body())


class TestToolPanel:
    """Tool calls render in a Collapsible; results are inline within it."""

    def test_tool_call_creates_collapsible_with_matching_title(self, tui_app):
        import threading

        async def _body():
            async with tui_app.run_test() as pilot:
                controller = get_tui()
                t = threading.Thread(
                    target=lambda: display.display_tool_call("execute_bash", '{"command": "ls"}'),
                    daemon=True,
                )
                t.start()
                t.join(timeout=2.0)
                await pilot.pause()

                out = tui_app.query_one("#output", VerticalScroll)
                collapsibles = list(out.query(Collapsible))
                assert len(collapsibles) == 1
                assert collapsibles[0].title == "Tool: execute_bash"
                # The collapsible must contain the call content as a child.
                assert len(list(collapsibles[0].query(Static))) >= 1

        _drive(_body())

    def test_tool_result_renders_inline_inside_call_collapsible(self, tui_app):
        import threading

        from harness_core.tools.tool_result import ToolResult

        def _run():
            display.display_tool_call("execute_bash", '{"command": "ls"}')
            # In the real loop the result always follows its call immediately.
            display.display_tool_result(
                "execute_bash",
                ToolResult(llm_text="file_a\nfile_b", display_text="file_a\nfile_b",
                           type_tag="text", title="", theme="info"),
            )

        async def _body():
            async with tui_app.run_test() as pilot:
                t = threading.Thread(target=_run, daemon=True)
                t.start()
                t.join(timeout=2.0)
                await pilot.pause()

                out = tui_app.query_one("#output", VerticalScroll)
                collapsibles = list(out.query(Collapsible))
                assert len(collapsibles) == 1
                # Exactly one collapsible (the call); the result is merged
                # inline INSIDE it, not as a second collapsible.
                assert collapsibles[0].title == "Tool: execute_bash"
                # The collapsible holds a single inner Static (one Panel that
                # contains call + separator + result), not 3 separate widgets.
                # (query(Static) also matches the CollapsibleTitle, so exclude it.)
                inner_statics = [
                    w for w in collapsibles[0].query(Static)
                    if not w.__class__.__name__.endswith("Title")
                ]
                assert len(inner_statics) == 1

        _drive(_body())


class TestControllerLifecycle:
    """The controller is inert when no app is running."""

    def test_inactive_controller_is_noop(self):
        controller = HarnessTUI()
        assert controller.is_active() is False
        # Should not raise even though nothing is mounted.
        controller.write("ignored")
        assert controller.write_count() == 0
        import pytest as _pytest

        with _pytest.raises(RuntimeError):
            controller.prompt("")


class TestStatusSpinner:
    """The busy spinner sits at the bottom of the message panel and toggles."""

    def test_spinner_widget_present_and_hidden_by_default(self, tui_app):
        from harness_core.terminal_io.tui import StatusSpinner

        async def _body():
            async with tui_app.run_test():
                spinner = tui_app.query_one("#spinner", StatusSpinner)
                assert spinner is not None
                # The controller hides the spinner until the agent is running.
                assert spinner.display is False

        _drive(_body())

    def test_spinner_render_animates(self, tui_app):
        from harness_core.terminal_io.tui import StatusSpinner

        async def _body():
            async with tui_app.run_test():
                spinner = tui_app.query_one("#spinner", StatusSpinner)
                first = spinner.render()
                second = spinner.render()
                # Each frame advances the glyph index, so two renders differ.
                assert first != second
                assert "thinking" in first.plain

        _drive(_body())

    def test_show_hide_spinner_toggles_display(self, tui_app):
        import threading

        async def _body():
            async with tui_app.run_test() as pilot:
                controller = get_tui()
                spinner = tui_app.query_one("#spinner")
                # Hidden initially (set by bind()).
                assert spinner.display is False

                # show_spinner is called from the worker/loop thread.
                t = threading.Thread(target=controller.show_spinner, daemon=True)
                t.start()
                t.join(timeout=2.0)
                await pilot.pause()
                assert spinner.display is True

                # hide_spinner clears it again.
                t2 = threading.Thread(target=controller.hide_spinner, daemon=True)
                t2.start()
                t2.join(timeout=2.0)
                await pilot.pause()
                assert spinner.display is False

        _drive(_body())
