---
name: "harness_core.model.provider.Provider"
description: "Abstract base class for AI providers with singleton registry by name."
source: "harness_core/model/provider.py"
---

Abstract base class for AI providers with singleton registry by name.

Only one Provider instance is created per unique configuration name. The
registry is keyed on ``ProviderConfig.name`` so that agents sharing the same
provider name will transparently share the same underlying connection pool.

## Methods
- **get_or_create(cls, config: 'ProviderConfig') -> 'Provider'** - Get or create a singleton Provider for the given configuration
- **get(cls, name: str) -> 'Provider' | None** - Return the registered Provider for *name*, or ``None`` if not yet created
- **chat_completion(self, messages: list[Dict], model: str, **kwargs) -> Dict** - Get chat completion from the provider
- **chat_completion_async(self, messages, model, **kwargs)** - Async chat completion; optional for providers
- **tokenize(self, text: str, model: str) -> list[int] | None** - Tokenize text using the provider's tokenizer
- **get_base_url(self) -> str** - Get the base URL for the provider's API
- **from_config(cls, config: 'ProviderConfig') -> 'Provider'** - Create a Provider instance from a configuration object

## Class Variables
- `_registry`: dict[str, 'Provider']

## References
- [Module: harness_core.model.provider](harness_core_model_provider) - Parent module
- Base class: `ABC`
- [get_or_create](harness_core_model_provider_Provider_get_or_create) - Get or create a singleton Provider for the given configuration
- [get](harness_core_model_provider_Provider_get) - Return the registered Provider for *name*, or ``None`` if not yet created
- [chat_completion](harness_core_model_provider_Provider_chat_completion) - Get chat completion from the provider
- [chat_completion_async](harness_core_model_provider_Provider_chat_completion_async) - Async chat completion; optional for providers
- [tokenize](harness_core_model_provider_Provider_tokenize) - Tokenize text using the provider's tokenizer
- [get_base_url](harness_core_model_provider_Provider_get_base_url) - Get the base URL for the provider's API
- [from_config](harness_core_model_provider_Provider_from_config) - Create a Provider instance from a configuration object
- `_registry`: dict[str, 'Provider']
