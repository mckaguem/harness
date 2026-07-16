---
name: "harness_core.skills.interceptor"
description: "Chat-interceptor middleware for slash-command skill activation."
source: "harness_core/skills/interceptor.py"
---

Chat-interceptor middleware for slash-command skill activation.

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

## References
- [InterceptorKind](harness_core_skills_interceptor_InterceptorKind) - String constants describing what the interceptor decided to do
- [InterceptorOutcome](harness_core_skills_interceptor_InterceptorOutcome) - Immutable result from an interceptor invocation
- [intercept_message](harness_core_skills_interceptor_intercept_message) - Inspect a raw user message and apply the slash-command routing rules
- [matches_slash_pattern](harness_core_skills_interceptor_matches_slash_pattern) - Return ``True`` if *text* starts with a slash command matching the pattern
- [extract_command_name](harness_core_skills_interceptor_extract_command_name) - If *text* is a slash command, return its captured name (lowercase), else ``None``
- [SLASH_COMMAND_RE](harness_core_skills_interceptor_SLASH_COMMAND_RE) - Constant
- [Module Index](../index/harness_core_skills.md) - Parent module index
