"""Model abstraction that wraps a Provider and routes Agent LLM calls.

A :class:`Model` pairs a resolved :class:`Provider` instance with the
provider-facing model name (``provider_model_name``) and the model-level
sampling parameters (temperature, top_p, max_tokens, reasoning_effort).

Agent turns are routed through :meth:`Model.chat_turn`, which delegates to the
Provider's ``chat_completion_async`` and sends the full conversation transcript
as ``input`` on every turn.
"""

from typing import Any, Dict, Mapping, Optional

from harness_core.config import get_provider_config
from harness_core.model.provider import Provider


class Model:
    """Wraps a :class:`Provider` with model-level configuration.

    Instances are normally created via :meth:`from_model_config`, which
    resolves the :class:`Provider` from a :data:`ModelConfig` mapping (looking
    up the named provider via the shared config registry) and stores the
    model-facing parameters needed for every turn.
    """

    def __init__(self,
                 provider: Provider,
                 provider_model_name: str,
                 temperature: float | None = None,
                 top_p: float | None = None,
                 max_tokens: int | None = None,
                 reasoning_effort: str | None = None):
        """Initialize a Model.

        Args:
            provider: The resolved Provider instance used for all turns.
            provider_model_name: The model string handed to the provider API.
            temperature: Optional sampling temperature.
            top_p: Optional nucleus sampling parameter.
            max_tokens: Optional max output tokens.
            reasoning_effort: Optional reasoning effort level.
        """
        self._provider = provider
        self._provider_model_name = provider_model_name
        self._temperature = temperature
        self._top_p = top_p
        self._max_tokens = max_tokens
        self._reasoning_effort = reasoning_effort

    @property
    def provider(self) -> Provider:
        """The underlying Provider instance."""
        return self._provider

    @property
    def provider_model_name(self) -> str:
        """The model string handed to the provider API."""
        return self._provider_model_name

    @classmethod
    def from_model_config(cls, model_config: Mapping[str, Any],
                          provider: Optional[Provider] = None) -> "Model":
        """Build a Model from a :data:`ModelConfig` mapping.

        The ``model_config`` may be a :class:`~harness_core.model.types.ModelConfig`
        TypedDict or any Mapping with the relevant keys. The ``provider`` field on
        the config is a *string name* (e.g. ``"openai"``); this method looks up the
        corresponding :class:`~harness_core.model.types.ProviderConfig` via
        :func:`harness_core.config.get_provider_config` and resolves a singleton
        Provider via :meth:`Provider.get_or_create`. If an explicit ``provider``
        instance is supplied it is used directly instead.

        Args:
            model_config: Mapping containing at least ``provider_model_name`` and
                ``provider`` (a string name). Model-level params are read from
                ``temperature``, ``top_p``, ``max_tokens`` and ``reasoning_effort``
                when present.
            provider: Optional pre-built Provider. When provided it is used as-is
                and the lookup from ``model_config`` is skipped.

        Returns:
            A fully-configured Model instance.
        """
        if provider is None:
            provider_name = model_config.get("provider")
            provider_config = get_provider_config(provider_name) if provider_name else None
            if provider_config is None:
                raise ValueError(
                    f"Could not resolve a ProviderConfig for provider '{provider_name}' "
                    f"referenced by model config '{model_config.get('name')}'."
                )
            provider = Provider.get_or_create(provider_config)

        provider_model_name = model_config.get("provider_model_name") or model_config.get("name") or ""
        temperature = model_config.get("temperature")
        top_p = model_config.get("top_p")
        max_tokens = model_config.get("max_tokens")
        reasoning_effort = model_config.get("reasoning_effort")

        return cls(
            provider=provider,
            provider_model_name=provider_model_name,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
        )

    async def chat_turn(self, session: "Session") -> dict[str, Any]:
        """Run one LLM turn for *session* and return the normalized response.

        Delegates to the wrapped Provider's ``chat_completion_async``. The full
        conversation transcript (``session.get_messages()``) is sent as ``input``
        on every turn.

        Args:
            session: The conversation :class:`~harness_core.session.session.Session`.
                Must expose ``get_messages()`` and ``get_tools()``.

        Returns:
            The provider-normalized response dict (``choices`` / ``usage`` / plus
            convenience keys).
        """
        # Local import to avoid circular dependency with harness_core.session.session
        from harness_core.session.session import Session  # noqa: F811

        kwargs: dict[str, Any] = {
            "model": self._provider_model_name,
            "tools": session.get_tools(),
            "temperature": self._temperature,
            "top_p": self._top_p,
            "max_tokens": self._max_tokens,
            "reasoning_effort": self._reasoning_effort,
        }

        response = await self._provider.chat_completion_async(
            messages=session.get_messages(),
            **kwargs,
        )

        return response


__all__ = ["Model"]
