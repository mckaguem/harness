"""Tests for the textual TUI in terminal_io/tui.py.

These run headless via textual's ``run_test``/``Pilot`` so they need no real
terminal and are safe in CI.  We exercise idiomatic textual patterns: widget
composition, the multi-line input submit binding, and the TUI routing that lets
the classic ``display_*`` helpers render into the ``RichLog`` pane while a TUI
is active.

The project's pytest has no async plugin, so each async scenario is driven from
a plain ``def test_*`` via ``asyncio.run``.  Note: assertions about a pending
prompt are made *after* ``pilot.press`` returns (the key handler runs on the
app thread synchronously), so we never block the single app thread.
"""

import asyncio

import pytest

from textual.widgets import Footer, Header, RichLog, TextArea

from terminal_io.tui import TextualHarnessApp, HarnessTUI, get_tui
from terminal_io import display


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

    def test_footer_present(self, tui_app):
        async def _body():
            async with tui_app.run_test():
                assert tui_app.query_one(Footer) is not None

        _drive(_body())

    def test_output_is_richlog(self, tui_app):
        async def _body():
            async with tui_app.run_test():
                assert isinstance(tui_app.query_one("#output", RichLog), RichLog)

        _drive(_body())

    def test_input_is_textarea(self, tui_app):
        async def _body():
            async with tui_app.run_test():
                assert isinstance(tui_app.query_one("#input", TextArea), TextArea)

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
                await pilot.press("ctrl+enter")

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
            result["value"] = get_tui().prompt("You> ")

        async def _body():
            async with tui_app.run_test() as pilot:
                t = threading.Thread(target=worker, daemon=True)
                t.start()
                await pilot.pause()  # let prompt() arm + focus the input
                assert tui_app.focused == tui_app.query_one("#input", TextArea)
                tui_app.query_one("#input", TextArea).text = "worker typed this"
                get_tui().submit()
                t.join(timeout=2.0)
                assert result.get("value") == "worker typed this"

        _drive(_body())


class TestRouting:
    """When the TUI is active, display_* writes route into the RichLog."""

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
        RichLog, so messages were invisible in the TUI alongside the agent's
        responses.
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
            controller.prompt("You> ")


class TestStatusSpinner:
    """The busy spinner sits at the bottom of the message panel and toggles."""

    def test_spinner_widget_present_and_hidden_by_default(self, tui_app):
        from terminal_io.tui import StatusSpinner

        async def _body():
            async with tui_app.run_test():
                spinner = tui_app.query_one("#spinner", StatusSpinner)
                assert spinner is not None
                # The controller hides the spinner until the agent is running.
                assert spinner.display is False

        _drive(_body())

    def test_spinner_render_animates(self, tui_app):
        from terminal_io.tui import StatusSpinner

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

