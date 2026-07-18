"""Model-related type definitions."""

from typing import (TypedDict, Union, Dict)
from dataclasses import dataclass


class ModelConfig(TypedDict, total=False):
    """Configuration for a model."""
    name: str
    provider_model_name: str  # actual model string handed to the provider API
    provider: str  # "openai" (Ollama support was removed)
    context_length: int
    base_url: str | None
    api_key: str | None
    temperature: float | None          # NEW — sampling temperature, optional
    top_p: float | None                # NEW — nucleus sampling parameter, optional
    max_tokens: int | None             # NEW — alias for max_output_tokens in config.yaml, optional
    reasoning_effort: str | None       # NEW — "none", "minimal", "low", "medium", "high", "xhigh", "max" (case-insensitive), optional


@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    name: str  # unique identifier for the provider
    provider_type: str  # "openai" (Ollama support was removed)
    base_url: str
    api_key: str | None = None
    default_model: str | None = None
    
    
class TokenUsage(TypedDict):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionResponse(TypedDict):
    """Standardized completion response."""
    choices: list[Dict]
    usage: TokenUsage
    

__all__ = [
    "ModelConfig",
    "ProviderConfig",
    "TokenUsage",
    "CompletionResponse",
]