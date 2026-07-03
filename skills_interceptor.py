"""Chat-interceptor middleware for slash-command skill activation.

This module inspects raw user messages *before* they reach the LLM and can:

1. Match a leading ``/skill-name`` against skills in the ``skills/`` directory.
2. Enforce the ``user-invocable`` permission flag on matched skills.
3. Force-activate an invocable skill by injecting its SKILL.md body into the
   conversation context so the model gains immediate access to that skill's
   instructions for this turn only.

The interceptor is intended to be called from :func:`agent.loop.user_loop` (or
any other message-handling pipeline) right after the built-in slash commands
have been checked and before ``agent.handle_prompt`` is invoked.

Result envelope
---------------
All public functions in this module return a :class:`InterceptorOutcome` data
class with three fields:

* ``kind`` (:data:`InterceptorKind`) — what happened, e.g. ``ACTIVATED``,
  ``RESTRICTED``, ``UNKNOWN``, or ``SKIP``.
* ``payload`` (``str | None``) — contextual data associated with the outcome:
  for :data:`InterceptorKind.ACTIVATED` this is a string ready to be injected
  into message history; for :data:`InterceptorKind.RESTRICTED` it is an error
  message shown to the user.
* ``stripped_message`` (``str | None``) — if the slash prefix was consumed,
  the remainder of the user's input after stripping ``/skill-name ``. Useful
  for callers that want to forward the cleaned request text onward.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Outcome kinds returned by the interceptor
# ---------------------------------------------------------------------------


class InterceptorKind:
    """String constants describing what the interceptor decided to do."""

    #: The message matched a slash command, activated an invocable skill, and
    #: its context was injected.  Callers should NOT forward this turn to the
    #: LLM — the next ``handle_prompt`` call will pick up the injected context.
    ACTIVATED = "activated"

    #: A matching skill exists but has ``user-invocable: false``. The slash was
    #: dropped and the remainder of the input is forwarded as regular text to
    #: the LLM. An informational message may be shown in :attr:`payload`.
    RESTRICTED = "restricted"

    #: The leading ``/name`` did not match any skill directory. Treat as a
    #: regular text message (fallback). Callers SHOULD forward to the LLM.
    UNKNOWN = "unknown"

    #: The input is not a slash command at all (does not start with ``/`` or
    #: does not match the regex pattern). Callers should fall through to their
    #: normal handling path unchanged.
    SKIP = "skip"


# ---------------------------------------------------------------------------
# Outcome data class — consumers of this module work exclusively with these
# objects rather than raw tuples, which makes downstream code self-documenting.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InterceptorOutcome:
    """Immutable result from an interceptor invocation.

    Attributes:
        kind: One of the :class:`InterceptorKind` constants.
        payload: Extra data relevant to the outcome — either the context blob
            to inject (ACTIVATED), or an error string for display (RESTRICTED).
            ``None`` for SKIP and UNKNOWN outcomes.
        stripped_message: The user's raw input with the ``/skill-name `` prefix
            removed, if the interceptor consumed it (ACTIVATED only). Otherwise
            ``None``.
    """

    kind: str
    payload: Optional[str] = None
    stripped_message: Optional[str] = None


# ---------------------------------------------------------------------------
# Regex for matching slash commands at the start of a user message.
#
# Pattern breakdown::
#
#     ^\/([a-zA-Z0-9\-]+)
#       ^  ^^^^^^^^^^^^^^^^
#       |    Captures one or more alphanumerics or hyphens immediately after
#       |    the leading slash — i.e. a valid skill-name slug.
#       |
#       Matches the literal leading "/" character.
#
# The captured group is treated as a candidate skill name and looked up in the
# skills directory.  Anything after the matched command (whitespace + request
# text) is preserved so the user's actual instruction can be forwarded.
# ---------------------------------------------------------------------------

SLASH_COMMAND_RE = re.compile(r"^/([a-zA-Z0-9\-]+)")


def intercept_message(
    raw_user_input: str,
    skills_dir: Optional[Path] = None,
) -> InterceptorOutcome:
    """Inspect a raw user message and apply the slash-command routing rules.

    This is the main entry point for the interceptor middleware. It performs
    all three phases — regex match, permission check, context injection — in
    sequence and returns an :class:`InterceptorOutcome` describing what should
    happen next.

    Args:
        raw_user_input: The user's verbatim input as received from the prompt.
        skills_dir: Override path to the skills directory (defaults to ``cwd / "skills"``).

    Returns:
        An :class:`InterceptorOutcome` summarising what happened. Callers should
        inspect :attr:`InterceptorOutcome.kind` and act accordingly.
    """
    from skills_discovery import get_skill_by_name  # lazy import — avoids cycle at startup

    if not raw_user_input or not raw_user_input.startswith("/"):
        return InterceptorOutcome(kind=InterceptorKind.SKIP)

    match = SLASH_COMMAND_RE.match(raw_user_input)
    if not match:
        # Starts with "/" but is not a valid slash command (e.g. "/???").
        # Treat as unknown — the LLM will see it as free text and can respond.
        return InterceptorOutcome(kind=InterceptorKind.UNKNOWN)

    candidate_name = match.group(1).lower()
    rest_after_command = raw_user_input[match.end():].lstrip(" ")

    # ------------------------------------------------------------------
    # Phase 2: permission check — does a matching skill exist, and is it
    # user-invocable?
    # ------------------------------------------------------------------
    if skills_dir is None:
        skills_dir = Path.cwd() / "skills"

    metadata, lookup_error = get_skill_by_name(candidate_name, skills_dir)

    if lookup_error or not metadata.get("name"):
        # No matching skill directory — fall through to regular LLM handling.
        return InterceptorOutcome(kind=InterceptorKind.UNKNOWN)

    # Permission gate: user-invocable defaults to True per spec.
    if not metadata.get("user-invocable", True):
        return InterceptorOutcome(
            kind=InterceptorKind.RESTRICTED,
            payload=(
                f"Command ``/{candidate_name}`` is restricted to internal use "
                f"(the skill has `user-invocable: false`). It cannot be triggered "
                f"manually."
            ),
            stripped_message=rest_after_command,
        )

    # ------------------------------------------------------------------
    # Phase 3: force-activate — build the context-injection block and return it.
    # ------------------------------------------------------------------
    body = metadata.get("body", "")
    if not body:
        return InterceptorOutcome(
            kind=InterceptorKind.RESTRICTED,
            payload=(
                f"Skill ``{candidate_name}`` exists but contains no instructions "
                f"in its SKILL.md body. Cannot activate."
            ),
        )

    skill_root = (skills_dir / candidate_name).resolve()
    abs_path_marker = str(skill_root)

    context_block = (
        "<user_activated_skill_context>\n"
        f"**Skill:** {candidate_name}\n"
        f"**Root directory:** `{abs_path_marker}`\n\n"
        "**Instructions:**\n"
        f"{body}\n"
        "</user_activated_skill_context>"
    )

    return InterceptorOutcome(
        kind=InterceptorKind.ACTIVATED,
        payload=context_block,
        stripped_message=rest_after_command,
    )


# ---------------------------------------------------------------------------
# Convenience helpers — small one-liners that callers sometimes need. Kept at
# module level so they do not have to reach into internals themselves.
# ---------------------------------------------------------------------------


def matches_slash_pattern(text: str) -> bool:
    """Return ``True`` if *text* starts with a slash command matching the pattern."""
    return bool(SLASH_COMMAND_RE.match(text))


def extract_command_name(text: str) -> Optional[str]:
    """If *text* is a slash command, return its captured name (lowercase), else ``None``."""
    match = SLASH_COMMAND_RE.match(text)
    if not match:
        return None
    return match.group(1).lower()
