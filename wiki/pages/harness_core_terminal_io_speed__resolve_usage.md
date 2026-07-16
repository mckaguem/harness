---
name: "harness_core.terminal_io.speed._resolve_usage"
description: "Extract (completion_tokens, prompt_tokens) from a response."
source: "harness_core/terminal_io/speed.py"
---

Extract (completion_tokens, prompt_tokens) from a response.

Supports both OpenAI-style and Ollama-native formats:
  - OpenAI:  {"usage": {"completion_tokens": N, "prompt_tokens": M}}
  - Ollama:  {"eval_count": N, "prompt_eval_count": M}
Returns (0, 0) if neither format is present.

## Signature
```python
_resolve_usage(response: dict) -> tuple[int, int]
```

## References
- [Module: harness_core.terminal_io.speed](harness_core_terminal_io_speed) - Parent module
