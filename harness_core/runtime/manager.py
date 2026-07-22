"""Runtime orchestration for the harness agent + TUI.

The :class:`Manager` is the single entry point that wires together the
:class:`~harness_core.agent.Agent` async loop and the Textual TUI app, and
listens on the event bus for a confirmed quit request so it can coordinate an
orderly shutdown of both.
"""

import asyncio
import logging

from harness_core.eventbus import EventListener, event_bus
from harness_core.event_types import (
    PROCESS_CONTROL_QUIT,
    PROCESS_CONTROL_QUIT_CONFIRM,
    AppControlPayload,
)
from harness_core.terminal_io.tui_app import TextualHarnessApp
from harness_core.agent import Agent
from harness_core.tools import AGENT_TOOLS
from harness_core.session.session_utils import create_run_folder

logger = logging.getLogger(__name__)


class Manager:
    """Coordinates the agent loop and the TUI for the harness process.

    Responsibilities:
      * Launch the Textual TUI (:class:`TextualHarnessApp`) and the agent's
        ``run_loop`` concurrently on the main event loop.
      * Listen on the event bus for ``PROCESS_CONTROL_QUIT_CONFIRM`` and, when
        received, signal the agent to exit and close the TUI.
    """

    def __init__(self, agent=None) -> None:
        """Store the agent to be managed.

        Args:
            agent: An optional pre-built :class:`~harness_core.agent.Agent`
                instance. If omitted, the agent must be created later via
                :meth:`launch_agent` before :meth:`run` is called.
        """
        self._agent = agent
        self._app: "TextualHarnessApp | None" = None
        self._listener: "_ShutdownListener | None" = None
        self._tui_task: "asyncio.Task | None" = None
        self._agent_task: "asyncio.Task | None" = None

    def launch_agent(
        self,
        agent_name: str,
        tool_schemas=None,
        extra_tools=None,
    ) -> "Agent":
        """Create and store a new agent (generic agent-launch helper).

        Starts a fresh run folder (so this launch and any subagents it spawns are
        organised under a single date-time directory) and builds the agent via
        :meth:`Agent.from_agent_name`. The created agent is stored on
        ``self._agent`` and returned.

        Args:
            agent_name: The discovery name of the agent (e.g. ``"main"``).
            tool_schemas: Optional list of tool schemas. Defaults to
                ``AGENT_TOOLS`` when ``None``.
            extra_tools: Optional extra tools passed through to the agent.

        Returns:
            The constructed :class:`~harness_core.agent.Agent` instance.
        """
        tool_schemas = AGENT_TOOLS if tool_schemas is None else tool_schemas
        # Start a fresh run folder for this launch.
        create_run_folder()
        self._agent = Agent.from_agent_name(
            agent_name, tool_schemas=tool_schemas, extra_tools=extra_tools
        )
        return self._agent

    async def run(self) -> None:
        """Run the agent loop and the TUI concurrently until shutdown."""
        if self._agent is None:
            raise RuntimeError("No agent launched; call launch_agent(...) first.")

        self._listener = _ShutdownListener(self)

        # Run listener on SEPARATE worker thread so we can use app.call_from_thread()
        import threading
        
        def _run_listener():
            """Run shutdown listener mailbox task on a worker thread."""
            # FIRST — create and set up event loop on this new thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # Store the worker loop so shutdown cleanup can signal it to stop.
            self._listener_loop = loop
            try:
                # THEN — run listener (which calls create_task using that loop)
                self._listener.run()
                loop.run_forever()
            except KeyboardInterrupt:
                pass
        
        self._listener_thread = threading.Thread(
            target=_run_listener, daemon=True, name="shutdown-listener"
        )
        self._listener_thread.start()

        # Wait for listener registration on worker thread
        import time
        time.sleep(0.1)

        try:
            self._listener.subscribe([PROCESS_CONTROL_QUIT, PROCESS_CONTROL_QUIT_CONFIRM])

            # TODO(headless): skip start_tui() when running headless

            # Subscribe the TUI listener to the event bus BEFORE the agent starts
            # emitting, so the initial "agent.status.ready" event is not missed.
            # The EventBus does not replay missed messages, so if the TUI
            # subscribed later (e.g. in on_mount) the startup banner + model name
            # would be dropped. The TUI controller buffers widget writes until the
            # app is actually running, so handlers firing before run_async starts
            # simply buffer and flush on bind() — no "App is not running" crash.
            from harness_core.terminal_io.event_listener import subscribe_event_listener
            self._tui_event_listener = subscribe_event_listener(self._agent._id, event_bus)

            self._tui_task = asyncio.create_task(self._launch_tui())
            self._agent_task = asyncio.create_task(self._agent.run_loop())

            await asyncio.gather(self._tui_task, self._agent_task)
        finally:
            if self._listener is not None:
                try:
                    self._listener.unsubscribe([PROCESS_CONTROL_QUIT, PROCESS_CONTROL_QUIT_CONFIRM])
                except Exception:  # pragma: no cover - defensive
                    logger.debug("Error stopping shutdown listener", exc_info=True)

            # Cancel + await the TUI event listener task (runs on main loop).
            if hasattr(self, '_tui_event_listener') and self._tui_event_listener is not None:
                tui_task = getattr(self._tui_event_listener, '_listener_task', None)
                if tui_task is not None and not tui_task.done():
                    tui_task.cancel()
                    try:
                        await tui_task
                    except (asyncio.CancelledError, RuntimeError):
                        pass
                # Deregister from bus so no further delivery attempts on closing loop
                event_bus.deregister_agent("tui")

            # Deregister the shutdown listener itself (loop is already dead by now)
            try:
                event_bus.deregister_agent(self._listener._id)
            except Exception:
                pass
            
            if hasattr(self, '_listener_thread') and self._listener_thread.is_alive():
                try:
                    # Stop the worker thread's own loop (it owns the listener
                    # task and any async generators). We stored a reference to it
                    # when the thread was started (_listener_loop).
                    wl = getattr(self, '_listener_loop', None)
                    if wl is not None and not wl.is_closed():
                        try:
                            wl.call_soon_threadsafe(wl.stop)
                        except Exception:
                            pass
                        self._listener_thread.join(timeout=2.0)
                        # shutdown_asyncgens() is a coroutine in modern Python
                        # (3.14). Await it on the (now idle) worker loop. If the
                        # loop can't run it (already stopped/closed), close the
                        # coroutine explicitly so it is never left un-awaited.
                        try:
                            coro = wl.shutdown_asyncgens()
                            wl.run_until_complete(coro)
                        except Exception:
                            # If run_until_complete failed, the coroutine must be
                            # explicitly closed to avoid the "never awaited"
                            # RuntimeWarning.
                            try:
                                coro.close()
                            except Exception:
                                pass
                        finally:
                            try:
                                wl.close()
                            except Exception:
                                pass
                except Exception:
                    logger.debug("Error stopping listener thread", exc_info=True)

    async def _launch_tui(self) -> None:
        """Construct and run the Textual TUI app, retaining the instance.

        Mirrors the behavior of ``harness_core.terminal_io.tui.launch`` but
        keeps a reference to the running ``TextualHarnessApp`` so the manager can
        close it during shutdown.
        """
        self._app = TextualHarnessApp(agent_id=self._agent._id)
        # Store manager ref on app so the ShowQuitDialog handler can route back
        self._app._manager = self
        await self._app.run_async()

    def _on_quit_confirmed(self) -> None:
        """Handle a confirmed quit: stop the agent and close the TUI.

        Called from the event loop thread (the listener runs on the main loop),
        so it is safe to mutate widgets / call ``app.exit()`` directly.
        """
        logger.debug("Shutdown triggered by PROCESS_CONTROL_QUIT_CONFIRM")

        # Signal the agent loop to stop (sets its loop exit event).
        try:
            self._agent.request_exit()
        except Exception:  # pragma: no cover - defensive
            logger.debug("Error requesting agent exit", exc_info=True)

        # Close the TUI if it is running.
        if self._app is not None:
            try:
                self._app.exit()
            except Exception:  # pragma: no cover - defensive
                logger.debug("Error exiting TUI app", exc_info=True)

    async def shutdown(self) -> None:
        """Cancel the managed tasks (best-effort orderly shutdown helper)."""
        for task in (self._tui_task, self._agent_task):
            if task is not None and not task.done():
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):  # noqa: BLE001
                    pass


class _ShutdownListener(EventListener):
    """Event-bus listener that maps quit events to the manager.

    Subscribes to both ``PROCESS_CONTROL_QUIT`` (from /exit or /quit commands)
    and ``PROCESS_CONTROL_QUIT_CONFIRM`` (from TUI dialog or Ctrl+Q).
    For a request event, shows a confirmation dialog in the running app; for
    confirm events, triggers Manager shutdown.
    """

    def __init__(self, manager: "Manager") -> None:
        super().__init__(event_bus, "runtime.manager.shutdown")
        self._manager = manager

    async def handle_process_control_quit(self, event) -> None:
        """React to a quit request by showing confirmation dialog in the TUI."""
        logger.debug("handle_process_control_quit() CALLED")

        payload = getattr(event, "payload", None)
        if not isinstance(payload, AppControlPayload):
            return
        self._show_dialog()

    async def handle_process_control_quit_confirm(self, event) -> None:
        """React to a confirmed quit by triggering manager shutdown."""
        payload = getattr(event, "payload", None)
        if isinstance(payload, AppControlPayload) and payload.action == "quit_confirm":
            self._manager._on_quit_confirmed()
        else:
            logger.debug(
                "Ignoring process_control_quit_confirm with unexpected payload: %r",
                payload,
            )

    def _show_dialog(self) -> None:
        """Push dialog using Textual's call_from_thread (worker thread)."""
        from harness_core.terminal_io.tui_app import QuitConfirmDialog

        app = self._manager._app
        if app is None:
            return

        try:
            # call_from_thread requires different threads — now we're on worker thread
            async def _push():
                await app.push_screen(QuitConfirmDialog())

            # This wraps in _context() automatically, setting active_app ContextVar
            future = app.call_from_thread(_push)
            logger.debug("Scheduled dialog via call_from_thread")
        except Exception as e:
            logger.debug(f"Error scheduling dialog: {type(e).__name__}: {e}", exc_info=True)
