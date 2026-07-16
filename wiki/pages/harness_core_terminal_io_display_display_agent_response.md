---
name: "harness_core.terminal_io.display.display_agent_response"
description: "Display the agent's response safely."
source: "harness_core/terminal_io/display.py"
---

Display the agent's response safely.

Parameters
----------
content: str | None
    The raw text response from the agent. If ``None`` is received, it is
    treated as an empty string to avoid ``TypeError`` when constructing a
    ``Markdown`` object.
response: dict, optional
    Additional metadata (e.g., token usage) used for speed reporting.
context_length: int, optional
    Length of the context window used for the request.
prompt_token_count: int | None, optional
    Number of tokens in the original prompt.

## Signature
```python
display_agent_response(content: str | None, response: dict | None, context_length: int, prompt_token_count: int | None, reasoning: str | None) -> None
```

## References
- [Module: harness_core.terminal_io.display](harness_core_terminal_io_display) - Parent module
