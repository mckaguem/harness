"""Interactive user loop mixin for the agent harness.

Consolidates all interactive-loop logic previously split between
``harness_core.agent.loop`` and the thin ``Agent.user_loop()`` delegator in
``harness_core.agent.core``. The :class:`InteractiveLoopMixin` is intended to be
mixed into :class:`~harness_core.agent.core.Agent` (or a subclass) so callers
can use :meth:`loop` or :meth:`run_loop` as a uniform interface without reaching
into agent internals.

The loop is now event-driven: user input arrives via events from the TUI on
the ``tui.user_input`` topic, dispatched by :class:`EventListenerLoopMixin`.
"""

import asyncio
import json
import logging
import time as _time
import traceback

from harness_core.agent.constants import RESPONSE, TOOL_CALL, TOOL_RESULT, ERROR
from harness_core.commands import COMMANDS
from harness_core.event_types import (
    AgentResponsePayload,
    ControlPayload,
    SessionErrorPayload,
    SystemMessagePayload,
    ToolCallPayload,
    ToolErrorPayload,
    ToolResultPayload,
    TurnStatsPayload,
    UserInputPayload,
)
from harness_core.eventbus import Event, EventListener, EventPublisher, filter_by_sender
from harness_core.skills.interceptor import InterceptorKind, intercept_message
from harness_core.session.context_compression import check_and_compress_if_needed

logger = logging.getLogger(__name__)


def _check_and_compress_if_needed(agent) -> None:
    """Check context utilization and trigger compression if above threshold."""
    try:
        session = getattr(agent, 'session', None) or getattr(agent, '_session', None)
        context_length = getattr(agent, 'context_length', 1 << 17)

        if session is None or not context_length:
            return

        result = check_and_compress_if_needed(session, context_length, threshold=0.5, fraction=0.1)

        if result.get("compressed"):
            agent.publish(
                "agent.turn.stats",
                TurnStatsPayload(response=None, context_length=context_length, elapsed_seconds=0.0),
            )
            agent.publish(
                "agent.session.autocompress",
                SystemMessagePayload(
                    title="Auto-Compression",
                    message=(
                        f"Context utilization was {result['pre_util']:.1%} of "
                        f"{context_length} max tokens. Auto-compressed to {result['post_util']:.1%}."
                    ),
                ),
            )
        elif result.get("error"):
            agent.publish(
                "agent.session.error",
                SessionErrorPayload(message=f"Auto-compression failed: {result['error']}"),
            )
    except Exception as e:
        logger.exception("Auto-compression handler failed for agent %s", getattr(agent, '_id', 'unknown'))


class InteractiveLoopMixin:
    """Mix-in that provides the interactive user-loop driver.

    Subclasses (e.g. :class:`~harness_core.agent.core.Agent`) must provide
    ``self.publish``, ``self.handle_prompt``, ``self.inject_text``, and
    ``self.context_length``/``self._agent_type``.
    """

    def loop(self, on_exit=None) -> None:  # noqa: D401
        """DEPRECATED. Use :meth:`run_loop` instead.

        The old blocking prompt_user() model has been replaced by an event-driven
        architecture where user input arrives via events from the TUI. This method
        is kept for backward compatibility and simply delegates to run_loop().

        Args:
            on_exit: Optional callback invoked just before the loop exits due
                to ``/exit`` or ``/quit``. Receives ``(agent, messages)``.
        """
        self.run_loop(on_exit=on_exit)

    async def run_loop(self, on_exit=None) -> None:  # noqa: D401
        """Run the interactive loop using events for user input.

        Unlike :meth:`loop`, this does NOT call prompt_user(). Instead it relies
        on :class:`EventListenerLoopMixin` to receive user input as events from
        the TUI and dispatch them through _process_and_run_turn.

        This is an async method that MUST be called with ``await`` inside an
        asyncio event loop context (e.g., via ``asyncio.run()`` in __main__.py).

        The method:
        1. Lazily initializes :class:`EventListenerLoopMixin` (which requires a
           running event loop for its mailbox listener task)
        2. Publishes the "agent.status.ready" banner event
        3. Blocks until /exit or /quit is received via _wait_for_exit()

        Args:
            on_exit: Optional callback invoked just before the loop exits due
                to ``/exit`` or ``/quit``. Receives ``(agent, messages)``.
        """

        logger.debug("Starting agent.")
        self._on_exit_callback = on_exit

        # Run the event loop
        self.run()
        self.subscribe()


        self._publish_ready_status()

        # Block until exit signal (set by /exit or error in dispatch path).
        await self._wait_for_exit()

    async def _wait_for_exit(self):  # noqa: D401
        """Block the current coroutine until the loop exit event is set.

        Called from run_loop() — waits for /exit or /quit to be processed by
        EventListenerLoopMixin, which sets self._loop_exit_event.
        """
        if not hasattr(self, '_loop_exit_event') or self._loop_exit_event is None:
            self._loop_exit_event = asyncio.Event()
        await self._loop_exit_event.wait()

    # ------------------------------------------------------------------
    # Internal turn processing — shared by both legacy synchronous loop and
    # new event-driven dispatch.
    # ------------------------------------------------------------------

    async def _process_and_run_turn(self, user_input: str) -> bool:  # noqa: D401
        """Process user input and run one agent turn asynchronously.

        Returns True if the loop should exit (e.g., /exit or /quit received).
        This method is called both by :meth:`loop` (legacy path, via deprecated
        alias) and by :class:`EventListenerLoopMixin.handle_tui_user_input`
        (event-driven path).

        Args:
            user_input: The raw user input text. May be a slash command or
                regular message. Skill-interception may modify this into
                effective_input before it reaches handle_prompt.

        Returns:
            True if the loop should exit, False otherwise.
        """
        turn_start = _time.time()

        effective_input, should_break = self._process_user_input(
            user_input, on_exit=self._on_exit_callback
        )
        if should_break:
            return True

        if effective_input and effective_input.strip():
            await self._run_turn(effective_input, turn_start)

        if not (user_input.startswith('/') and effective_input == user_input):
            try:
                self._check_and_publish_compression(self)
            except Exception as e:
                self.publish(
                    "agent.session.error",
                    SessionErrorPayload(message=f"Auto-compression check failed: {e}"),
                )

        return False

    # ------------------------------------------------------------------
    # Public helpers (intentionally prefixed with ``_`` — part of the loop
    # contract but not meant to be called directly by end users).
    # ------------------------------------------------------------------

    def _publish_ready_status(self) -> None:
        """Emit the initial "Agent Ready" system-message event."""
        self.publish(
            "agent.status.ready",
            SystemMessagePayload(
                title=f"🚀 Agent Ready — {self._agent_type.name} ({self._agent_type.model_name})",
                message="Type a message to begin. Type /exit or /quit to stop.",
                model=self._agent_type.model_name,
            ),
        )

    def _process_user_input(self, user_input: str, on_exit=None):  # noqa: D401
        """Process slash commands and skill-interceptor routing.

        Returns:
            A tuple ``(effective_input, should_break)`` where ``effective_input``
            is the text to feed into ``handle_prompt`` and ``should_break``
            indicates whether the outer loop should exit.

            For a recognized ``COMMANDS`` entry the raw ``/command`` portion is
            consumed and never forwarded. By default the whole command (including
            any trailing text) is consumed and nothing reaches the model. A handler
            may OPT IN to forwarding by returning a ``(text, should_break)`` tuple,
            in which case ``text`` (stripped) is forwarded to the model. This keeps
            the path open for forwarding commands like
            ``/goal fix all failing tests``. A self-contained command with no
            trailing text (e.g. ``/new``) is fully handled and returns
            ``("", False)`` so nothing reaches the model. A command that exits the
            loop returns ``("", True)``.
        """
        if not user_input.startswith('/'):
            return user_input, False

        parts = user_input[1:].split(' ', 1)
        command_name = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ''

        handler = COMMANDS.get(command_name)
        if handler is not None:
            result = handler(rest, agent=self)
            # A handler may opt into forwarding trailing text to the model by
            # returning a (text, should_break) tuple. Anything else (None/True/False)
            # means the command is fully handled and its text is consumed. This keeps
            # the path open for forwarding commands like
            # "/goal fix all failing tests" or "/code-review review the code in /src"
            # without forcing every built-in command to leak its arguments to the model.
            if isinstance(result, tuple) and len(result) == 2:
                forward_text, should_break = result
                forward_text = (forward_text or "").strip()
                if should_break:
                    if on_exit is not None:
                        on_exit(self, self._session.messages)
                    return "", True
                return forward_text, False
            # Non-tuple result: command fully handled; consume its text.
            if result is True and on_exit is not None:
                on_exit(self, self._session.messages)
                return "", True
            elif result is True:
                return "", True
            return "", False

        outcome = intercept_message(user_input)
        if outcome.kind == InterceptorKind.ACTIVATED:
            self.inject_text(outcome.payload or "")
            effective_input = outcome.stripped_message if outcome.stripped_message else user_input
        elif outcome.kind == InterceptorKind.RESTRICTED:
            self.publish("agent.tool.error", ToolErrorPayload(message=outcome.payload or ""))
            effective_input = outcome.stripped_message if outcome.stripped_message else user_input
        else:
            effective_input = user_input

        return effective_input, False

    async def _run_turn(self, effective_input: str, turn_start: float) -> None:  # noqa: D401
        """Wrap ``handle_prompt`` + dispatch with start/stop events.

        Publishes ``agent.turn.start`` before and ``agent.turn.stop`` after the
        agent's response to a user message. Delegates the actual prompt handling
        and per-kind dispatch to :meth:`_handle_turn`. The outer try/finally
        guarantees that ``agent.turn.stop`` is always published, even if an
        unexpected exception escapes from ``_handle_turn``.
        """
        self.publish("agent.turn.start", ControlPayload(action={}))
        try:
            await self._handle_turn(effective_input, turn_start)
        finally:
            self.publish("agent.turn.stop", ControlPayload(action={}))

    async def _handle_turn(self, effective_input: str, turn_start: float) -> None:  # noqa: D401
        """Run ``handle_prompt`` and dispatch each output to the appropriate helper.

        Iterates defensively so that any exception raised while pulling items
        from the generator (or during dispatch) is surfaced as a
        ``agent.tool.error`` event, keeping the outer loop alive for the user
        to retry.
        """
        try:
            outputs = self.handle_prompt(effective_input)
            async for output in outputs:
                kind = output[0]
                if kind == RESPONSE:
                    _, content, ollama_response, _ = output
                    self._publish_response(kind, content, ollama_response, turn_start)
                elif kind == TOOL_CALL:
                    _, func_name, args_str, response_data = output
                    self._publish_tool_call(func_name, args_str, response_data, turn_start)
                elif kind == TOOL_RESULT:
                    _, func_name, result, response_data = output
                    self._handle_and_publish_tool_result(func_name, result, response_data)
                elif kind == ERROR:
                    _, description, _, _ = output
                    self._publish_error(description)
        except Exception as exc:
            self.publish(
                "agent.tool.error",
                ToolErrorPayload(message=f"Agent turn failed: {exc}\n" + traceback.format_exc()),
            )

    # -- Per-kind output dispatch --------------------------------------

    def _publish_response(self, kind, content, response_data, turn_start) -> None:  # noqa: D401
        """Publish ``agent.turn.response`` and ``agent.turn.stats`` for a RESPONSE."""
        elapsed = _time.time() - turn_start
        reasoning = (
            (response_data or {}).get("reasoning")
            if isinstance(response_data, dict) else None
        )
        self.publish(
            "agent.turn.response",
            AgentResponsePayload(
                content=content or "",
                response=response_data,
                context_length=self.context_length,
                reasoning=reasoning,
            ),
        )
        self.publish(
            "agent.turn.stats",
            TurnStatsPayload(response=response_data, context_length=self.context_length, elapsed_seconds=elapsed),
        )

    def _publish_tool_call(self, func_name: str, args_str: str, response_data, turn_start) -> None:  # noqa: D401
        """Publish ``agent.tool.call`` for a TOOL_CALL output."""
        args_dict = json.loads(args_str)
        elapsed = _time.time() - turn_start
        summary = self._summarize(func_name, args_dict)
        pre_content = (response_data or {}).get("pre_tool_content", "") or ""
        reasoning = (response_data or {}).get("reasoning", "") or ""
        self.publish(
            "agent.tool.call",
            ToolCallPayload(
                func_name=func_name,
                args_str=args_str,
                summary=summary,
                pre_content=pre_content or "",
                reasoning=reasoning,
            ),
        )
        self.publish(
            "agent.turn.stats",
            TurnStatsPayload(response=response_data, context_length=self.context_length, elapsed_seconds=0.0),
        )

    def _handle_and_publish_tool_result(self, func_name: str, result, response_data) -> None:  # noqa: D401
        """Execute a tool call and publish the related ``agent.tool.result`` event.

        Groups both the extraction of :class:`~harness_core.tools.dispatcher.ToolResult`
        fields and the publishing of the resulting payload so that callers can
        treat "run a tool + emit its result" as one atomic step.
        """
        result_title = getattr(result, "title", None)
        result_display_text = getattr(result, "display_text", "") or ""
        result_theme = getattr(result, "theme", "info") or "info"
        result_type_tag = getattr(result, "type_tag", "text") or "text"
        self.publish(
            "agent.tool.result",
            ToolResultPayload(
                func_name=func_name,
                result_title=result_title,
                result_display_text=result_display_text or "",
                result_theme=result_theme or "info",
                result_type_tag=result_type_tag or "text",
            ),
        )

    def _publish_error(self, description) -> None:  # noqa: D401
        """Publish ``agent.tool.error`` for an ERROR output."""
        self.publish("agent.tool.error", ToolErrorPayload(message=description or ""))

    # -- Auto-compression ----------------------------------------------

    def _check_and_publish_compression(self, agent) -> None:  # noqa: D401
        """Run the auto-compression check after a user message turn.

        Delegates to :func:`_check_and_compress_if_needed`. Any unexpected
        failure is re-raised so the caller can publish a ``SessionErrorPayload``.
        """
        _check_and_compress_if_needed(agent)

    # -- Module-level helper wrappers ----------------------------------

    @staticmethod
    def _summarize(func_name: str, args_dict: dict) -> str:  # noqa: D401
        """Local wrapper so :func:`~harness_core.tools.dispatcher.summarize` is imported lazily."""
        from harness_core.tools.dispatcher import summarize
        return summarize(func_name, args_dict)

    def request_exit(self) -> None:
        """Signal the agent loop to exit (called by Manager on shutdown)."""
        try:
            if hasattr(self, '_loop_exit_event') and self._loop_exit_event is not None:
                self._loop_exit_event.set()
        except Exception:
            logger.exception("Failed to signal agent exit event")


class EventListenerLoopMixin(EventListener):
    """Mix-in that listens for user input events from the TUI and dispatches them.

    This replaces the old blocking ``prompt_user()`` model with an event-driven one:

    - The TUI publishes :class:`~harness_core.event_types.UserInputPayload` events
      to the ``tui.user_input`` topic on the EventBus.
    - This mixin receives those events (filtered by sender id) and calls
      :meth:`InteractiveLoopMixin._process_and_run_turn`.
    - No thread-based prompting is needed; the agent processes input as events arrive.

    **IMPORTANT**: This mixin MUST be initialized from within an asyncio event loop
    context (e.g., inside :meth:`InteractiveLoopMixin.run_loop` which runs via
    ``asyncio.run()``). The :class:`~harness_core.eventbus.EventListener` base class
    calls ``asyncio.create_task()`` in ``__init__``, which requires a running event loop.

    Initialization is done lazily inside ``run_loop()`` so that Agent can be created
    in synchronous code without crashing.
    """

    TUI_SENDER_PATTERN = r"^Tui\\.main$"

    def __init__(self, eventBus: EventBus=None, id='', *args, **kwargs) -> None:  # noqa: D401
        """Initialize the event listener mixin.

        Accepts event_bus and id from Agent.__init__ via MRO chain as positional
        arguments (matching these named parameters). Calls EventPublisher.__init__
        explicitly to set self.eventBus and self._id (required by later
        EventListener initialization). Does NOT call EventListener.__init__ here —
        that's done lazily inside run_loop() which requires a running asyncio event loop.

        The MRO chain is: Agent → InteractiveLoopMixin (no __init__) → EventListenerLoopMixin.
        When Agent calls super().__init__(event_bus, self._id), the args are passed
        positionally and match these named parameters directly.
        """

        super().__init__(eventBus, id)
        #EventPublisher.__init__(self, eventBus, id)

    #@filter_by_sender(TUI_SENDER_PATTERN)
    async def handle_tui_user_input(self, event: Event) -> None:  # noqa: D401
        """Handle a user input event from the TUI.

        Extracts the message text and dispatches it through the InteractiveLoopMixin
        processing pipeline via _process_and_run_turn(). When /exit or /quit is
        received (should_break returns True), signals loop exit by setting
        self._loop_exit_event so run_loop() can return.

        Args:
            event: The Event containing a UserInputPayload from the TUI.
        """
        payload = event.payload
        if not isinstance(payload, UserInputPayload):
            return

        should_break = await self._process_and_run_turn(payload.message)
        if should_break:
            # Signal the run_loop to stop waiting
            try:
                self._loop_exit_event.set()
            except AttributeError:
                pass  # _loop_exit_event not set yet (shouldn't happen in normal flow)

    async def _dispatch_user_input(self, message: str) -> None:  # noqa: D401
        """Alternative dispatch entry point for user input.

        Currently handle_tui_user_input handles dispatch directly via
        _process_and_run_turn(), but this method is provided as a hook for
        future extensions (e.g., logging, filtering).

        Args:
            message: The user's submitted text content.
        """
        await self._process_and_run_turn(message)
