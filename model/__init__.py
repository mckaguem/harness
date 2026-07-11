"""Model module — provider abstractions and utilities for AI models.

This module provides:
1. Provider abstraction for different AI backends (OpenAI, Ollama, etc.)
2. Model utilities for tokenization, context length calculation
3. Model configuration and type definitions
"""

from .utils import get_base_url, tokenize_prompt
from .provider import Provider, OpenAIProvider, OllamaProvider, create_provider
from .types import ModelConfig, ProviderConfig, TokenUsage, CompletionResponse

__all__ = [
    "get_base_url",
    "tokenize_prompt", 
    "Provider",
    "OpenAIProvider",
    "OllamaProvider",
    "create_provider",
    "ModelConfig",
    "ProviderConfig",
    "TokenUsage",
    "CompletionResponse",
]