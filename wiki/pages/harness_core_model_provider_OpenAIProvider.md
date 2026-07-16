---
name: "harness_core.model.provider.OpenAIProvider"
description: "OpenAI provider implementation."
source: "harness_core/model/provider.py"
---

OpenAI provider implementation.

## Methods
- **__init__(self, client)** - Initialize with an OpenAI client
- **chat_completion(self, messages: list[Dict], model: str, **kwargs) -> Dict** - Get chat completion from OpenAI via the Responses API
- **chat_completion_async(self, messages: list[Dict], model: str, **kwargs) -> Dict** - Get chat completion from OpenAI via the Responses API (async)
- **tokenize(self, text: str, model: str) -> list[int] | None** - Tokenize text using OpenAI tokenizer
- **get_base_url(self) -> str** - Get OpenAI base URL

## Class Variables
None

## References
- [Module: harness_core.model.provider](harness_core_model_provider) - Parent module
- Base class: `Provider`
- [__init__](harness_core_model_provider_OpenAIProvider___init__) - Initialize with an OpenAI client
- [chat_completion](harness_core_model_provider_OpenAIProvider_chat_completion) - Get chat completion from OpenAI via the Responses API
- [chat_completion_async](harness_core_model_provider_OpenAIProvider_chat_completion_async) - Get chat completion from OpenAI via the Responses API (async)
- [tokenize](harness_core_model_provider_OpenAIProvider_tokenize) - Tokenize text using OpenAI tokenizer
- [get_base_url](harness_core_model_provider_OpenAIProvider_get_base_url) - Get OpenAI base URL
