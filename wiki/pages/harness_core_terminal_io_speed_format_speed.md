---
name: "harness_core.terminal_io.speed.format_speed"
description: "Extract and format token usage from an OpenAI-style or Ollama-native response."
source: "harness_core/terminal_io/speed.py"
---

Extract and format token usage from an OpenAI-style or Ollama-native response.

Reads ``response['usage']`` (OpenAI) or top-level ``eval_count`` /
``prompt_eval_count`` keys (Ollama).  If a wall-clock duration is present
in the response, calculates tokens/sec speed.

Produces a stats string joined by `` | ``::

    ⏱ 50 tok (33.3 tok/s) | 1024 in (25.0% ctx)

## Signature
```python
format_speed(response: dict, context_length: int) -> str
```

## References
- [Module: harness_core.terminal_io.speed](harness_core_terminal_io_speed) - Parent module
