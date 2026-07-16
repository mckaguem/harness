---
name: "harness_core.model.utils.get_base_url"
description: "Return the OpenAI base URL as a plain string, if we can find it."
source: "harness_core/model/utils.py"
---

Return the OpenAI base URL as a plain string, if we can find it.

The openai-python ``Client`` stores its `base_url` directly on the instance.
If that fails, fall back to environment variables or default endpoint.

## Signature
```python
get_base_url(openai_client) -> str
```

## References
- [Module: harness_core.model.utils](harness_core_model_utils) - Parent module
