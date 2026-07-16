---
name: "harness_core.terminal_io.speed._resolve_duration_ms"
description: "Extract wall-clock duration in milliseconds from a response."
source: "harness_core/terminal_io/speed.py"
---

Extract wall-clock duration in milliseconds from a response.

Supports:
  - OpenAI-style: {"duration_ms": N} (already in ms)
  - Ollama eval:   {"eval_duration": N} (nanoseconds → ms)
  - Ollama prompt: {"prompt_eval_duration": N} (nanoseconds → ms)

Returns None when no duration information is available.

## Signature
```python
_resolve_duration_ms(response: dict) -> float | None
```

## References
- [Module: harness_core.terminal_io.speed](harness_core_terminal_io_speed) - Parent module
