---
name: "harness_core.model.utils.tokenize_prompt"
description: "Ask OpenAI-compatible API to tokenize the accumulated *messages* and return the count."
source: "harness_core/model/utils.py"
---

Ask OpenAI-compatible API to tokenize the accumulated *messages* and return the count.

Used as a client-side source of truth for prompt token count — useful when
caching causes ``prompt_eval_count`` to be zero in chat responses.

Returns ``None`` on any failure (network, model load, etc.) so callers can
fall back gracefully.

## Signature
```python
tokenize_prompt(openai_client, messages: list[dict], model_name: str) -> int | None
```

## References
- [Module: harness_core.model.utils](harness_core_model_utils) - Parent module
