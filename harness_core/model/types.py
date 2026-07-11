"""Model-related type definitions."""

from typing import Dict, List, Optional, TypedDict, Union
from dataclasses import dataclass


class ModelConfig(TypedDict, total=False):
    """Configuration for a model."""
    name: str
    provider: str  # "openai", "ollama", etc.
    context_length: int
    base_url: Optional[str]
    api_key: Optional[str]


@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    name: str  # unique identifier for the provider
    provider_type: str  # "openai", "ollama", etc.
    base_url: str
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    
    
class TokenUsage(TypedDict):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class CompletionResponse(TypedDict):
    """Standardized completion response."""
    choices: List[Dict]
    usage: TokenUsage
    

__all__ = [
    "ModelConfig",
    "ProviderConfig",
    "TokenUsage",
    "CompletionResponse",
]