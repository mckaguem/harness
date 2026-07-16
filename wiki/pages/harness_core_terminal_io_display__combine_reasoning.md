---
name: "harness_core.terminal_io.display._combine_reasoning"
description: "Prepend reasoning/thinking above a horizontal separator, then the body."
source: "harness_core/terminal_io/display.py"
---

Prepend reasoning/thinking above a horizontal separator, then the body.

Used by both the agent-response panel and the pre-tool-call "Agent" panel so
the user sees the model's thinking followed by a clear ``---`` separator and
then the actual response / pre-tool-call text.

The separator is only drawn when there is real body text to separate: if the
model returned reasoning but no separate answer content, the reasoning is
shown on its own (no dangling ``---`` with a blank panel beneath it).

## Signature
```python
_combine_reasoning(reasoning: str | None, body: str) -> str
```

## References
- [Module: harness_core.terminal_io.display](harness_core_terminal_io_display) - Parent module
