"""Provider abstraction for AI model backends with singleton registry.

This module defines a common interface for different AI model backends via the
OpenAI-compatible/Responses API so that the rest of the codebase can work with any
provider interchangeably. All Provider instances are registered by name and retrieved
via get_or_create() to ensure there is only one instance per unique configuration.
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
            An OpenAIProvider instance (Ollama support was removed).

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
        """Get chat completion from OpenAI via the Responses API.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use
            **kwargs: Additional provider-specific parameters (currently only
                ``tools`` is ever passed, and may be None).

        Returns:
            Normalized completion response with ``choices`` and ``usage``.
        """
        tools = kwargs.get('tools')
        max_output_tokens = kwargs.pop('max_tokens', 16384) if 'max_tokens' in kwargs else 16384

        request_kwargs = {
            "model": model,
            "input": messages,
            "max_output_tokens": max_output_tokens,
        }
        if tools is not None:
            request_kwargs["tools"] = tools

        try:
            response = self.client.responses.create(**request_kwargs)
        except Exception as exc:
            raise RuntimeError(f"Provider chat request failed: {exc}") from exc

        content_text = ""
        tool_calls = []
        for item in response.output:
            if item.type == "message":
                parts = []
                for part in item.content:
                    parts.append(part.text)
                content_text = "".join(parts)
            elif item.type == "function_call":
                tool_calls.append({
                    "id": item.call_id,
                    "type": "function",
                    "function": {
                        "name": item.name,
                        "arguments": item.arguments,
                    },
                })

        message = {"role": "assistant", "content": content_text or None}
        if tool_calls:
            message["tool_calls"] = tool_calls

        usage = response.usage
        usage_dict = {
            "prompt_tokens": usage.input_tokens if usage else 0,
            "completion_tokens": usage.output_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
        }

        return {
            "choices": [{"message": message}],
            "usage": usage_dict,
        }

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


def create_provider(client, provider_type: str = "auto") -> Provider:
    """Create a provider instance.

    Ollama support was removed; all provider types ("openai", "auto", or any
    other value) resolve to OpenAIProvider, which now uses the OpenAI Responses API.
    """
    return OpenAIProvider(client)


__all__ = [
    "Provider",
    "OpenAIProvider",
    "create_provider",
]
