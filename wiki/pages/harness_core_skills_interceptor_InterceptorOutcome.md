---
name: "harness_core.skills.interceptor.InterceptorOutcome"
description: "Immutable result from an interceptor invocation."
source: "harness_core/skills/interceptor.py"
---

Immutable result from an interceptor invocation.

Attributes:
    kind: One of the :class:`InterceptorKind` constants.
    payload: Extra data relevant to the outcome — either the context blob
        to inject (ACTIVATED), or an error string for display (RESTRICTED).
        ``None`` for SKIP and UNKNOWN outcomes.
    stripped_message: The user's raw input with the ``/skill-name `` prefix
        removed, if the interceptor consumed it (ACTIVATED only). Otherwise
        ``None``.

## Methods
None

## Class Variables
- `kind`: str
- `payload`: str | None
- `stripped_message`: str | None

## References
- [Module: harness_core.skills.interceptor](harness_core_skills_interceptor) - Parent module
- `kind`: str
- `payload`: str | None
- `stripped_message`: str | None
