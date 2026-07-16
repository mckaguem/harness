---
name: "harness_core.skills.interceptor.intercept_message"
description: "Inspect a raw user message and apply the slash-command routing rules."
source: "harness_core/skills/interceptor.py"
---

Inspect a raw user message and apply the slash-command routing rules.

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

## Signature
```python
intercept_message(raw_user_input: str, skills_dir: Path | None) -> InterceptorOutcome
```

## References
- [Module: harness_core.skills.interceptor](harness_core_skills_interceptor) - Parent module
