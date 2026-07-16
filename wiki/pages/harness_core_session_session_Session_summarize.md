---
name: "harness_core.session.session.summarize"
description: "Ask the LLM to summarise the conversation accumulated so far."
source: "harness_core/session/session.py"
---

Ask the LLM to summarise the conversation accumulated so far.

Builds a temporary message list from recent history and appends a
summary prompt. The resulting turn is *not* persisted in ``self.messages``
— the session's own history remains untouched.

Args:
    summary_prompt: Optional override for how to summarise. If provided,
        this replaces the default "expert summarizer" system message and
        user instruction, letting the caller specify any custom guidance.

Returns:
    A string containing the generated summary, or an empty string on
    failure.

Raises:
    RuntimeError: If no provider is configured (call Agent to use summarize).

## Signature
```python
summarize(self, summary_prompt: str | None) -> str
```

## References
- [Module: harness_core.session.session](harness_core_session_session) - Parent module
- [Class: Session](harness_core_session_session_Session) - Parent class
