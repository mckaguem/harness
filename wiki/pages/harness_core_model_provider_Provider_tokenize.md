---
name: "harness_core.model.provider.tokenize"
description: "Tokenize text using the provider's tokenizer."
source: "harness_core/model/provider.py"
---

Tokenize text using the provider's tokenizer.

Args:
    text: Text to tokenize
    model: Model name (for model-specific tokenization)

Returns:
    List of token IDs, or None if tokenization fails

## Signature
```python
tokenize(self, text: str, model: str) -> list[int] | None
```

## References
- [Module: harness_core.model.provider](harness_core_model_provider) - Parent module
- [Class: Provider](harness_core_model_provider_Provider) - Parent class
