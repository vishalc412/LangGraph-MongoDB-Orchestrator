"""
Factory for creating LLM provider instances.

This module implements the Factory pattern for creating LLM providers,
enabling easy switching between different providers and extensibility
for adding new providers.

Design Pattern: Factory Pattern
Purpose: Centralize provider creation logic

Benefits:
- Single point of configuration
- Easy to add new providers
- Consistent initialization
- Runtime provider selection

Author: AI Agent Development Team
"""

from typing import Any, Dict, Optional, Type

from mongodb_agent.config.settings import get_config
from mongodb_agent.providers.base import BaseLLMProvider
from mongodb_agent.providers.ollama_provider import OllamaProvider
from mongodb_agent.providers.openai_provider import OpenAIProvider
from mongodb_agent.utils.logger import get_logger

logger = get_logger(__name__)

# Registry of available providers
# This allows adding new providers without modifying the factory code
PROVIDER_REGISTRY: Dict[str, Type[BaseLLMProvider]] = {
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def register_provider(name: str, provider_class: Type[BaseLLMProvider]) -> None:
    """
    Register a new LLM provider.

    This allows extending the system with custom providers without
    modifying the core code. Useful for:
    - Adding proprietary LLM integrations
    - Testing with mock providers
    - Supporting new LLM APIs

    Args:
        name: Provider identifier (lowercase, alphanumeric)
        provider_class: Provider class (must inherit from BaseLLMProvider)

    Raises:
        ValueError: If provider_class doesn't inherit from BaseLLMProvider

    Example:
        >>> class CustomProvider(BaseLLMProvider):
        ...     def generate(self, messages, **kwargs):
        ...         return "custom response"
        ...     def stream(self, messages, **kwargs):
        ...         yield "custom response"
        ...     @property
        ...     def name(self):
        ...         return "custom"
        >>>
        >>> register_provider("custom", CustomProvider)
        >>> provider = create_provider("custom")
    """
    if not issubclass(provider_class, BaseLLMProvider):
        raise ValueError(
            f"Provider class must inherit from BaseLLMProvider, " f"got {provider_class}"
        )

    PROVIDER_REGISTRY[name.lower()] = provider_class
    logger.info(f"Registered provider: {name}")


def create_provider(
    provider_name: Optional[str] = None, **kwargs: Any
) -> BaseLLMProvider:
    """
    Create LLM provider instance using factory pattern.

    This function creates and configures an LLM provider based on the
    provided name and configuration. If no provider name is given,
    uses the default from application config.

    Provider Selection Priority:
    1. Explicitly provided provider_name parameter
    2. Configuration's default_llm_provider setting
    3. Fallback to "openai"

    Configuration Priority:
    1. Explicitly provided kwargs
    2. Provider-specific config from application settings
    3. Provider's default values

    Args:
        provider_name: Provider identifier ("openai", "ollama", etc.)
                      If None, uses config.default_llm_provider
        **kwargs: Provider-specific configuration parameters.
                 If not provided, uses values from application config.
                 Common parameters:
                 - api_key (OpenAI)
                 - model (all providers)
                 - temperature (all providers)
                 - max_tokens (all providers)

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider name is unknown

    Example:
        >>> # Use default provider from config
        >>> provider = create_provider()
        >>> response = provider.generate([{"role": "user", "content": "Hi"}])
        >>>
        >>> # Explicitly specify provider
        >>> provider = create_provider("openai", api_key="sk-...")
        >>>
        >>> # Use config values
        >>> config = get_config()
        >>> provider = create_provider("openai", **config.openai.dict())
    """
    config = get_config()

    # Determine provider to use
    provider_name = provider_name or config.default_llm_provider

    # Normalize provider name
    provider_name = provider_name.lower()

    # Check if provider exists
    if provider_name not in PROVIDER_REGISTRY:
        available = ", ".join(PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Unknown provider: '{provider_name}'. " f"Available providers: {available}"
        )

    # Get provider configuration from app config if not provided
    if not kwargs:
        llm_config = config.get_llm_config(provider_name)
        kwargs = llm_config.model_dump()

        # Validate provider configuration
        try:
            config.validate_provider_config(provider_name)
        except ValueError as e:
            logger.error(f"Provider configuration invalid: {e}")
            raise

    # Create and return provider instance
    provider_class = PROVIDER_REGISTRY[provider_name]

    logger.info(
        f"Creating provider",
        extra={
            "provider": provider_name,
            "class": provider_class.__name__,
        },
    )

    try:
        provider = provider_class(**kwargs)
        logger.info(f"Provider created successfully: {provider_name}")
        return provider

    except Exception as e:
        logger.error(f"Failed to create provider '{provider_name}': {e}", exc_info=True)
        raise


def get_available_providers() -> list[str]:
    """
    Get list of available provider names.

    Returns:
        List of registered provider names

    Example:
        >>> providers = get_available_providers()
        >>> print(providers)
        ['openai', 'ollama']
    """
    return list(PROVIDER_REGISTRY.keys())
