"""Provider abstraction for AI model backends with singleton registry.

This module defines a common interface for different AI providers (OpenAI, Ollama, etc.)
so that the rest of the codebase can work with any provider interchangeably. All Provider
instances are registered by name and retrieved via get_or_create() to ensure there is only
one instance per unique configuration.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class Provider(ABC):
    """Abstract base class for AI providers with singleton registry by name.

    Only one Provider instance is created per unique configuration name. The
    registry is keyed on ``ProviderConfig.name`` so that agents sharing the same
    provider name will transparently share the same underlying connection pool.
    """

    # Class-level singleton registry: config-name -> Provider instance.
    _registry: Dict[str, 'Provider'] = {}

    @classmethod
    def get_or_create(cls, config: 'ProviderConfig') -> 'Provider':
        """Get or create a singleton Provider for the given configuration.

        If a Provider with ``config.name`` already exists in the registry it is
        returned unchanged; otherwise a new instance is created via
        :meth:`from_config` and registered before being returned. This ensures
        that all agents referencing the same provider name share exactly one
        underlying client/connection pool.

        Args:
            config: A ProviderConfig with a non-empty ``name`` field.

        Returns:
            The singleton Provider instance for this configuration name.

        Raises:
            ValueError: If *config* has no ``name`` attribute or it is empty.
        """
        if not hasattr(config, 'name') or not config.name:
            raise ValueError("ProviderConfig must include a non-empty 'name' field")

        provider_name = config.name
        if provider_name in cls._registry:
            return cls._registry[provider_name]

        instance = cls.from_config(config)
        cls._registry[provider_name] = instance
        return instance

    @classmethod
    def get(cls, name: str) -> Optional['Provider']:
        """Return the registered Provider for *name*, or ``None`` if not yet created."""
        return cls._registry.get(name)

    @abstractmethod
    def chat_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        """Get chat completion from the provider.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use
            **kwargs: Additional provider-specific parameters

        Returns:
            Dictionary with completion response
        """
        pass

    @abstractmethod
    def get_context_length(self, model: str) -> int:
        """Get context length for a model.

        Args:
            model: Model name

        Returns:
            Context length in tokens
        """
        pass

    @abstractmethod
    def tokenize(self, text: str, model: str) -> Optional[List[int]]:
        """Tokenize text using the provider's tokenizer.

        Args:
            text: Text to tokenize
            model: Model name (for model-specific tokenization)

        Returns:
            List of token IDs, or None if tokenization fails
        """
        pass

    @abstractmethod
    def get_base_url(self) -> str:
        """Get the base URL for the provider's API.

        Returns:
            Base URL as string
        """
        pass

    @classmethod
    def from_config(cls, config: 'ProviderConfig') -> 'Provider':
        """Create a Provider instance from a configuration object.

        Args:
            config: A ProviderConfig with provider_type, base_url,
                    and optional api_key fields.

        Returns:
            An appropriate subclass of Provider (e.g. OpenAIProvider or OllamaProvider).

        Raises:
            ValueError: If required fields are missing from the configuration.
        """
        from openai import OpenAI as _OpenAIClient

        if not config.provider_type:
            raise ValueError("ProviderConfig must include a 'provider_type' field")
        if not config.base_url:
            raise ValueError("ProviderConfig must include a 'base_url' field")

        client = _OpenAIClient(
            base_url=config.base_url,
            api_key=config.api_key or "",
        )

        return create_provider(client, provider_type=config.provider_type)


class OpenAIProvider(Provider):
    """OpenAI provider implementation."""

    def __init__(self, client):
        """Initialize with an OpenAI client.

        Args:
            client: OpenAI client instance
        """
        self.client = client

    def chat_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        """Get chat completion from OpenAI."""
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        msg = {
            "content": response.choices[0].message.content,
            "role": response.choices[0].message.role
        }
        if response.choices[0].message.tool_calls:
            msg["tool_calls"] = [
                {"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in response.choices[0].message.tool_calls
            ]
        return {
            "choices": [{"message": msg}],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
        }

    def get_context_length(self, model: str) -> int:
        """Get context length for OpenAI model.

        Note: OpenAI doesn't expose context length via API, so we use
        model.utils.get_context_length as fallback.
        """
        from .utils import get_context_length
        return get_context_length(self.client, model)

    def tokenize(self, text: str, model: str) -> Optional[List[int]]:
        """Tokenize text using OpenAI tokenizer."""
        from .utils import tokenize_prompt
        # OpenAI doesn't have a direct tokenize API, use our utility
        messages = [{"role": "user", "content": text}]
        count = tokenize_prompt(self.client, messages, model)
        if count is not None:
            # We don't have actual token IDs, just count
            # Return a dummy list for compatibility
            return list(range(count))
        return None

    def get_base_url(self) -> str:
        """Get OpenAI base URL."""
        from .utils import get_base_url
        return get_base_url(self.client)


class OllamaProvider(Provider):
    """Ollama provider implementation."""

    def __init__(self, client):
        """Initialize with an Ollama client.

        Args:
            client: Ollama client instance (OpenAI-compatible client configured for Ollama)
        """
        self.client = client

    def chat_completion(self, messages: List[Dict], model: str, **kwargs) -> Dict:
        """Get chat completion from Ollama."""
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        msg = {
            "content": response.choices[0].message.content,
            "role": response.choices[0].message.role
        }
        if response.choices[0].message.tool_calls:
            msg["tool_calls"] = [
                {"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in response.choices[0].message.tool_calls
            ]
        return {
            "choices": [{"message": msg}],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }
        }

    def get_context_length(self, model: str) -> int:
        """Get context length for Ollama model."""
        from .utils import get_context_length
        return get_context_length(self.client, model)

    def tokenize(self, text: str, model: str) -> Optional[List[int]]:
        """Tokenize text using Ollama tokenizer."""
        from .utils import tokenize_prompt
        messages = [{"role": "user", "content": text}]
        count = tokenize_prompt(self.client, messages, model)
        if count is not None:
            # We don't have actual token IDs, just count
            # Return a dummy list for compatibility
            return list(range(count))
        return None

    def get_base_url(self) -> str:
        """Get Ollama base URL."""
        from .utils import get_base_url
        return get_base_url(self.client)


def create_provider(client, provider_type: str = "auto") -> Provider:
    """Create a provider instance based on client configuration.

    Args:
        client: AI client instance (OpenAI, etc.)
        provider_type: Provider type ("openai", "ollama", or "auto" for auto-detection)

    Returns:
        Provider instance
    """
    if provider_type == "openai":
        return OpenAIProvider(client)
    elif provider_type == "ollama":
        return OllamaProvider(client)
    elif provider_type == "auto":
        # Auto-detect based on base_url
        from .utils import get_base_url
        base_url = get_base_url(client)
        if "localhost" in base_url or "127.0.0.1" in base_url or "ollama" in base_url:
            return OllamaProvider(client)
        else:
            return OpenAIProvider(client)
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")


__all__ = [
    "Provider",
    "OpenAIProvider",
    "OllamaProvider",
    "create_provider",
]
