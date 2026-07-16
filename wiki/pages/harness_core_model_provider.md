---
name: "harness_core.model.provider"
description: "Provider abstraction for AI model backends with singleton registry."
source: "harness_core/model/provider.py"
---

Provider abstraction for AI model backends with singleton registry.

This module defines a common interface for different AI model backends via the
OpenAI-compatible/Responses API so that the rest of the codebase can work with any
provider interchangeably. All Provider instances are registered by name and retrieved
via get_or_create() to ensure there is only one instance per unique configuration.

## References
- [Provider](harness_core_model_provider_Provider) - Abstract base class for AI providers with singleton registry by name
  - [get_or_create](harness_core_model_provider_Provider_get_or_create) - Get or create a singleton Provider for the given configuration
  - [get](harness_core_model_provider_Provider_get) - Return the registered Provider for *name*, or ``None`` if not yet created
  - [chat_completion](harness_core_model_provider_Provider_chat_completion) - Get chat completion from the provider
  - [chat_completion_async](harness_core_model_provider_Provider_chat_completion_async) - Async chat completion; optional for providers
  - [tokenize](harness_core_model_provider_Provider_tokenize) - Tokenize text using the provider's tokenizer
  - [get_base_url](harness_core_model_provider_Provider_get_base_url) - Get the base URL for the provider's API
  - [from_config](harness_core_model_provider_Provider_from_config) - Create a Provider instance from a configuration object
- [OpenAIProvider](harness_core_model_provider_OpenAIProvider) - OpenAI provider implementation
  - [__init__](harness_core_model_provider_OpenAIProvider___init__) - Initialize with an OpenAI client
  - [chat_completion](harness_core_model_provider_OpenAIProvider_chat_completion) - Get chat completion from OpenAI via the Responses API
  - [chat_completion_async](harness_core_model_provider_OpenAIProvider_chat_completion_async) - Get chat completion from OpenAI via the Responses API (async)
  - [tokenize](harness_core_model_provider_OpenAIProvider_tokenize) - Tokenize text using OpenAI tokenizer
  - [get_base_url](harness_core_model_provider_OpenAIProvider_get_base_url) - Get OpenAI base URL
- [_to_responses_input](harness_core_model_provider__to_responses_input) - Convert chat-style ``messages`` into a valid Responses API request
- [_to_responses_tools](harness_core_model_provider__to_responses_tools) - Convert Chat-Completions tool schemas to the Responses API `tools` shape
- [_normalize_response](harness_core_model_provider__normalize_response) - Convert an OpenAI Responses API response into the normalized
chat-completion dict shape (``choices`` + ``usage``) shared by both the
sync and async chat paths
- [create_provider](harness_core_model_provider_create_provider) - Create a provider instance
- [Module Index](../index/harness_core_model.md) - Parent module index
