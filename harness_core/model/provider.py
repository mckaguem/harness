"""Provider abstraction for AI model backends with singleton registry.

This module defines a common interface for different AI model backends via the
OpenAI-compatible/Responses API so that the rest of the codebase can work with any
provider interchangeably. All Provider instances are registered by name and retrieved
via get_or_create() to ensure there is only one instance per unique configuration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from harness_core.model.types import ProviderConfig


class Provider(ABC):
    """Abstract base class for AI providers with singleton registry by name.

    Only one Provider instance is created per unique configuration name. The
    registry is keyed on ``ProviderConfig.name`` so that agents sharing the same
    provider name will transparently share the same underlying connection pool.
    """

    # Class-level singleton registry: config-name -> Provider instance.
    _registry: dict[str, 'Provider'] = {}

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
    def get(cls, name: str) -> 'Provider' | None:
        """Return the registered Provider for *name*, or ``None`` if not yet created."""
        return cls._registry.get(name)

    @abstractmethod
    def chat_completion(self, messages: list[Dict], model: str, **kwargs) -> Dict:
        """Get chat completion from the provider.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use
            **kwargs: Additional provider-specific parameters

        Returns:
            Dictionary with completion response
        """
        pass

    async def chat_completion_async(self, messages, model, **kwargs):
        """Async chat completion; optional for providers. Default raises NotImplementedError."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement chat_completion_async"
        )

    @abstractmethod
    def tokenize(self, text: str, model: str) -> list[int] | None:
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

        return create_provider(client)


def _to_responses_input(messages: list[Dict]) -> "tuple[str | None, list[Any]]":
    """Convert chat-style ``messages`` into a valid Responses API request.

    The OpenAI **Responses** API does not accept the Chat-Completions
    message schema verbatim.  In particular it rejects ``role: "tool"`` items
    (tool results must be ``function_call_output`` items) and requires assistant
    tool calls to be ``function_call`` items.  This helper normalises the
    harness's accumulated conversation (which uses the chat schema, including
    ``role: "tool"`` results and ``tool_calls`` on assistant messages) into
    the shape the Responses API expects.

    Args:
        messages: List of chat-schema dicts (``role`` + ``content``,
            optionally ``tool_calls`` on assistant and ``tool_call_id`` on tool).

    Returns:
        A ``(instructions, input_items)`` tuple where ``instructions`` is the
        concatenated system prompt (or ``None``) and ``input_items`` is the list
        of Responses input items (``message`` / ``function_call`` /
        ``function_call_output``).
    """
    instructions_parts: list = []
    input_items: list = []

    def _text_content(text: object) -> list:
        """Wrap a message body in the Responses content-part list.

        The OpenAI **Responses** API requires ``content`` on a ``message``
        item to be a LIST of content parts (e.g. ``[{"type":
        "input_text", "text": ...}]``), NOT a bare string. Sending a
        plain string is what produced the persistent `400 invalid
        prompt / invalid responses api request` error.
        """
        return [{"type": "input_text", "text": str(text) if text is not None else ""}]

    for msg in messages:
        role = msg.get("role")
        if role == "system":
            # System prompts go in the top-level `instructions` field, not the
            # `input` array (the Responses API rejects them there).
            content = msg.get("content")
            if content:
                instructions_parts.append(content)
            continue

        if role == "user":
            input_items.append({
                "type": "message",
                "role": "user",
                "content": _text_content(msg.get("content")),
            })
            continue

        if role == "assistant":
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                # Each assistant tool call becomes a `function_call` input item.
                for tc in tool_calls:
                    func = tc.get("function", {}) or {}
                    input_items.append({
                        "type": "function_call",
                        "call_id": tc.get("id"),
                        "name": func.get("name"),
                        "arguments": func.get("arguments") or "",
                    })
            else:
                input_items.append({
                    "type": "message",
                    "role": "assistant",
                    "content": _text_content(msg.get("content")),
                })
            continue

        if role == "tool":
            # Tool results must be `function_call_output` items referencing
            # the originating `function_call` via `call_id`.
            input_items.append({
                "type": "function_call_output",
                "call_id": msg.get("tool_call_id"),
                "output": msg.get("content") or "",
            })
            continue

    instructions = "\n\n".join(instructions_parts) if instructions_parts else None
    return instructions, input_items


def _to_responses_tools(tools: list[Dict] | None) -> list[Dict] | None:
    """Convert Chat-Completions tool schemas to the Responses API `tools` shape.

    Chat Completions nests the callable under `function`:
        {"type": "function", "function": {"name": ..., "parameters": ...}}
    The Responses API requires a FLATTENED shape (name/parameters at the
    top level), matching ``openai.types.responses.FunctionToolParam``:
        {"type": "function", "name": ..., "parameters": ..., "strict": ...}
    Sending the nested Chat shape yields ``400 invalid prompt`` (the
    server reports `name`/``parameters` as `received undefined`).
    """
    if tools is None:
        return None
    converted: list = []
    for tool in tools:
        if not isinstance(tool, dict):
            converted.append(tool)
            continue
        if "function" in tool and isinstance(tool.get("function"), dict):
            func = tool["function"]
            item: dict[str, Any] = {"type": "function"}
            if "name" in func:
                item["name"] = func["name"]
            if "description" in func:
                item["description"] = func["description"]
            if "parameters" in func:
                item["parameters"] = func["parameters"]
            # Responses API defaults strict to True; mirror that when unspecified.
            item["strict"] = bool(func.get("strict", True))
            converted.append(item)
        else:
            # Already flat (or an unknown shape) — pass through untouched.
            converted.append(tool)
    return converted


def _normalize_response(response) -> dict:
    """Convert an OpenAI Responses API response into the normalized
    chat-completion dict shape (``choices`` + ``usage``) shared by both the
    sync and async chat paths.
    """
    content_text = ""
    tool_calls = []
    reasoning_text = ""
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
        elif item.type == "reasoning":
            # Responses API emits reasoning tokens as separate items.
            # `summary` (when include=["reasoning.summary"] is requested) holds
            # human-readable text; otherwise `content` holds the (often
            # encrypted) reasoning text. Prefer summary, fall back to content.
            item_text = ""
            summary = getattr(item, "summary", None)
            if summary:
                item_text = "".join(getattr(s, "text", "") or "" for s in summary)
            if not item_text:
                content = getattr(item, "content", None)
                if content:
                    item_text = "".join(getattr(c, "text", "") or "" for c in content)
            if item_text:
                reasoning_text += item_text

    message: dict[str, Any] = {
        "role": "assistant",
        "content": content_text or None,
        "reasoning": reasoning_text or None,
    }
    if tool_calls:
        message["tool_calls"] = tool_calls

    usage = response.usage
    usage_dict = {
        "prompt_tokens": usage.input_tokens if usage else 0,
        "completion_tokens": usage.output_tokens if usage else 0,
        "total_tokens": usage.total_tokens if usage else 0,
    }

    # Top-level convenience keys consumed by Agent._chat() and downstream
    # display/loop code so they don't have to re-derive them.
    reasoning_val = message.get("reasoning") or None
    pre_tool_content = content_text if (tool_calls and content_text) else ""

    return {
        "choices": [{"message": message}],
        "usage": usage_dict,
        "model": None,  # placeholder; Agent injects self._agent_type.model_name
        "reasoning": reasoning_val,
        "pre_tool_content": pre_tool_content or "",
    }


class OpenAIProvider(Provider):
    """OpenAI provider implementation."""

    def __init__(self, client):
        """Initialize with an OpenAI client.

        Args:
            client: OpenAI client instance
        """
        self.client = client

    def _build_request_kwargs(self, messages: list[Dict], model: str, tools, **model_params):
        """Build the kwargs dict for ``client.responses.create(**kwargs)``.

        Shared by both sync and async :meth:`chat_completion` paths so that
        changes to the request shape need only be made in one place.
        
        Args:
            messages: Chat-schema message list.
            model: The provider_model_name string for ``model=`` kwarg.
            tools: Tool schemas (or None).
            **model_params: Optional model-level sampling params — temperature,
                top_p, max_tokens (mapped to responses API's max_output_tokens),
                and reasoning_effort (mapped to reasoning={"effort": ...}).
        """
        instructions, input_items = _to_responses_input(messages)
        request_kwargs: dict[str, Any] = {
            "model": model,
            "input": input_items,
            "max_output_tokens": 16384,   # default — will be overridden if user provides max_tokens
        }
        if instructions is not None:
            request_kwargs["instructions"] = instructions
        if tools is not None:
            # Responses API ``tools`` are FLATTENED (name/parameters at top
            # level), not nested under ``function`` like Chat Completions.
            request_kwargs["tools"] = _to_responses_tools(tools)

        # ---- Optional model-level parameters (from config.yaml) ----
        temperature = model_params.get("temperature")
        top_p = model_params.get("top_p")
        max_tokens = model_params.get("max_tokens")
        reasoning_effort = model_params.get("reasoning_effort")

        if temperature is not None:
            request_kwargs["temperature"] = float(temperature)
        if top_p is not None:
            request_kwargs["top_p"] = float(top_p)
        if max_tokens is not None:
            # Map user-friendly "max_tokens" config key to the Responses API's
            # parameter name which is "max_output_tokens".
            request_kwargs["max_output_tokens"] = int(max_tokens)
        if reasoning_effort is not None:
            _VALID_EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh", "max")
            effort_lower = str(reasoning_effort).lower()
            if effort_lower not in _VALID_EFFORTS:
                raise ValueError(
                    f"Invalid reasoning_effort '{reasoning_effort}' for model. "
                    f"Must be one of: {', '.join(_VALID_EFFORTS)}"
                )
            request_kwargs["reasoning"] = {"effort": effort_lower}

        return request_kwargs

    def chat_completion(self, messages: list[Dict], model: str, **kwargs) -> Dict:
        """Get chat completion from OpenAI via the Responses API.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use
            **kwargs: Additional provider-specific parameters — currently ``tools``
                (may be None) plus any of ``temperature``, ``top_p``, ``max_tokens``,
                ``reasoning_effort``.

        Returns:
            Normalized completion response with ``choices``, ``usage`` and
            convenience keys (``reasoning``, ``pre_tool_content``).
        """
        tools = kwargs.get('tools')
        request_kwargs = self._build_request_kwargs(
            messages, model, tools,
            temperature=kwargs.get("temperature"),
            top_p=kwargs.get("top_p"),
            max_tokens=kwargs.get("max_tokens"),
            reasoning_effort=kwargs.get("reasoning_effort"),
        )

        try:
            response = self.client.responses.create(**request_kwargs)
        except Exception as exc:
            raise RuntimeError(f"Provider chat request failed: {exc}") from exc

        return _normalize_response(response)

    async def chat_completion_async(self, messages: list[Dict], model: str, **kwargs):
        """Get chat completion from OpenAI via the Responses API (async).

        Mirrors :meth:`chat_completion` but awaits the SDK call.
        """
        tools = kwargs.get('tools')
        request_kwargs = self._build_request_kwargs(
            messages, model, tools,
            temperature=kwargs.get("temperature"),
            top_p=kwargs.get("top_p"),
            max_tokens=kwargs.get("max_tokens"),
            reasoning_effort=kwargs.get("reasoning_effort"),
        )

        try:
            response = await self.client.responses.create(**request_kwargs)
        except Exception as exc:
            raise RuntimeError(f"Provider chat request failed: {exc}") from exc

        return _normalize_response(response)

    def tokenize(self, text: str, model: str) -> list[int] | None:
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


def create_provider(client) -> Provider:
    """Create a provider instance.

    Ollama support was removed; the provider is always an OpenAIProvider,
    which uses the OpenAI Responses API.
    """
    return OpenAIProvider(client)


__all__ = [
    "Provider",
    "OpenAIProvider",
    "create_provider",
    "_normalize_response",
]
