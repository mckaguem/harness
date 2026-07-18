"""Interactive user loop mixin for the agent harness.

Consolidates all interactive-loop logic previously split between
``harness_core.agent.loop`` and the thin ``Agent.user_loop()`` delegator in
``harness_core.agent.core``. The :class:`InteractiveLoopMixin` is intended to be
mixed into :class:`~harness_core.agent.core.Agent` (or a subclass) so callers
(e.g. the TUI) can use :meth:`loop` as a uniform interface without reaching
into agent internals.
"""

import json
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
)
from harness_core.skills.interceptor import InterceptorKind, intercept_message
from harness_core.session.context_compression import check_and_compress_if_needed


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
    except Exception:
        pass


class InteractiveLoopMixin:
    """Mix-in that provides the interactive user-loop driver.

    Subclasses (e.g. :class:`~harness_core.agent.core.Agent`) must provide
    ``self.publish``, ``self.handle_prompt``, ``self.inject_text``, and
    ``self.context_length``/``self._agent_type``.
    """

    def loop(self, on_exit=None) -> None:  # noqa: D401
        """Run the interactive command loop for this agent.

        Args:
            on_exit: Optional callback invoked just before the loop exits due
                to ``/exit`` or ``/quit``. Receives ``(agent, messages)``.
        """
        from harness_core.terminal_io import prompt_user  # local: only used here

        self._publish_ready_status()

        while True:
            user_input = prompt_user()
            turn_start = _time.time()

            effective_input, should_break = self._process_user_input(user_input, on_exit)
            if should_break:
                break

            self._run_turn(effective_input, turn_start)

            if not (user_input.startswith('/') and effective_input == user_input):
                try:
                    self._check_and_publish_compression(self)
                except Exception as e:
                    self.publish(
                        "agent.session.error",
                        SessionErrorPayload(message=f"Auto-compression check failed: {e}"),
                    )

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
            is the text to feed into ``handle_prompt``, and ``should_break``
            indicates whether the outer loop should exit.
        """
        if not user_input.startswith('/'):
            return user_input, False

        parts = user_input[1:].split(' ', 1)
        command_name = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ''

        handler = COMMANDS.get(command_name)
        if handler is not None:
            result = handler(rest, agent=self)
            if result is True and on_exit is not None:
                on_exit(self, self._session.messages)
                return user_input, True
            elif result is True:
                return user_input, True
            return user_input, False

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

    def _run_turn(self, effective_input: str, turn_start: float) -> None:  # noqa: D401
        """Wrap ``handle_prompt`` + dispatch with start/stop events.

        Publishes ``agent.turn.start`` before and ``agent.turn.stop`` after the
        agent's response to a user message. Delegates the actual prompt handling
        and per-kind dispatch to :meth:`_handle_turn`. The outer try/finally
        guarantees that ``agent.turn.stop`` is always published, even if an
        unexpected exception escapes from ``_handle_turn``.
        """
        self.publish("agent.turn.start", ControlPayload(action={}))
        try:
            self._handle_turn(effective_input, turn_start)
        finally:
            self.publish("agent.turn.stop", ControlPayload(action={}))

    def _handle_turn(self, effective_input: str, turn_start: float) -> None:  # noqa: D401
        """Run ``handle_prompt`` and dispatch each output to the appropriate helper.

        Iterates defensively so that any exception raised while pulling items
        from the generator (or during dispatch) is surfaced as a
        ``agent.tool.error`` event, keeping the outer loop alive for the user
        to retry.
        """
        try:
            outputs = self.handle_prompt(effective_input)
            for output in outputs:
                kind = output[0]
                if kind == RESPONSE:
                    _, content, ollama_response, _ = output
                    self._publish_response(kind, content, ollama_response, turn_start)
                elif kind == TOOL_CALL:
                    _, func_name, args_str, response_data = output
                    self._publish_tool_call(func_name, args_str, response_data)
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

    def _publish_response(self, kind, content, ollama_response, turn_start) -> None:  # noqa: D401
        """Publish ``agent.turn.response`` and ``agent.turn.stats`` for a RESPONSE."""
        elapsed = _time.time() - turn_start
        reasoning = (
            (ollama_response or {}).get("reasoning")
            if isinstance(ollama_response, dict) else None
        )
        self.publish(
            "agent.turn.response",
            AgentResponsePayload(
                content=content or "",
                response=ollama_response,
                context_length=self.context_length,
                reasoning=reasoning,
            ),
        )
        self.publish(
            "agent.turn.stats",
            TurnStatsPayload(response=ollama_response, context_length=self.context_length, elapsed_seconds=elapsed),
        )

    def _publish_tool_call(self, func_name: str, args_str: str, response_data) -> None:  # noqa: D401
        """Publish ``agent.tool.call`` for a TOOL_CALL output."""
        args_dict = json.loads(args_str)
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
