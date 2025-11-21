"""
LLM Provider abstraction layer.

This module provides a unified interface for working with multiple LLM providers,
enabling seamless switching between OpenAI, Ollama, and future providers.

Design Pattern: Strategy + Factory patterns
- Strategy: BaseLLMProvider defines the interface
- Factory: create_provider() instantiates the right provider

Usage:
    >>> from mongodb_agent.providers import create_provider
    >>> provider = create_provider("openai")
    >>> response = provider.generate([{"role": "user", "content": "Hello"}])
"""

from mongodb_agent.providers.base import (
    BaseLLMProvider,
    LLMProviderError,
    RateLimitError,
    AuthenticationError,
    InvalidRequestError,
)
from mongodb_agent.providers.factory import create_provider, register_provider
from mongodb_agent.providers.openai_provider import OpenAIProvider
from mongodb_agent.providers.ollama_provider import OllamaProvider

__all__ = [
    "BaseLLMProvider",
    "LLMProviderError",
    "RateLimitError",
    "AuthenticationError",
    "InvalidRequestError",
    "create_provider",
    "register_provider",
    "OpenAIProvider",
    "OllamaProvider",
]
