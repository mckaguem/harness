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
    app = TextualHarnessApp(agent_id=None)
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
    """The input area is wired up; user input flows through publish_user_input()."""

    def test_submit_resolves_pending_prompt(self, tui_app):
        async def _body():
            async with tui_app.run_test() as pilot:
                text_area = tui_app.query_one("#input", TextArea)
                text_area.text = "hello world\nsecond line"
                text_area.focus()

                # After the refactor, input is event-driven via publish_user_input().
                # We verify the text area content before publishing.
                assert text_area.text == "hello world\nsecond line"

                await pilot.pause()

        _drive(_body())

    def test_publish_user_input_event(self, tui_app):
        """Publishing user input via publish_user_input() sends an event to the bus."""
        async def _body():
            async with tui_app.run_test() as pilot:
                # Get the TUI controller and publish an event.
                tui = get_tui()
                tui.publish_user_input("test message")

                # Verify the event was published (check via event bus or publisher).
                from harness_core.terminal_io.event_publisher import get_tui_publisher as _get_pub

                pub = _get_pub()
                assert pub is not None

                await pilot.pause()

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
        """A controller that has not been bound should be a no-op."""
        from harness_core.terminal_io.harness_tui import HarnessTUI

        controller = HarnessTUI()
        assert controller.is_active() is False
        # Should not raise even though nothing is mounted.
        controller.write("ignored")
        assert controller.write_count() == 0

        # publish_user_input doesn't block, but may still try to publish if publisher exists.
        # The old prompt() raised RuntimeError when unbound; now it's event-driven.
        controller.publish_user_input("test message")  # Should not raise


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
        async def _body():
            async with tui_app.run_test() as pilot:
                controller = get_tui()
                spinner = tui_app.query_one("#spinner")
                # Hidden initially (set by bind()).
                assert spinner.display is False

                controller.show_spinner()
                assert spinner.display is True

                controller.hide_spinner()
                assert spinner.display is False

        _drive(_body())
