"""
Abstract base class for LLM providers.

This module defines the interface that all LLM providers must implement,
enabling seamless switching between different LLM backends (OpenAI, Ollama, etc.).

Design Pattern: Strategy Pattern
Purpose: Decouple LLM provider implementation from agent logic

Best Practices:
- All providers implement the same interface
- Errors are normalized to common exception types
- Streaming is optional but encouraged for better UX
- Configuration is injected via constructor

Author: AI Agent Development Team
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    This class defines the contract that all LLM providers must follow,
    enabling the application to work with multiple LLM backends without
    code changes in the agent layer.

    Implementing classes must provide:
    - generate(): Synchronous text generation
    - stream(): Streaming text generation
    - name: Provider identifier

    Optional features:
    - generate_structured(): Structured output generation (JSON schema)

    Example implementation:
        >>> class CustomProvider(BaseLLMProvider):
        ...     def generate(self, messages, **kwargs):
        ...         # Your implementation
        ...         return "response"
        ...
        ...     def stream(self, messages, **kwargs):
        ...         yield "response"
        ...
        ...     @property
        ...     def name(self):
        ...         return "custom"
    """

    def __init__(self, **kwargs: Any):
        """
        Initialize LLM provider with configuration.

        Args:
            **kwargs: Provider-specific configuration parameters
        """
        self.config = kwargs

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """
        Generate text response from messages.

        This method must be implemented by all providers. It should:
        1. Accept messages in standard chat format
        2. Call the provider's API
        3. Return the generated text
        4. Handle errors and convert to standard exceptions

        Args:
            messages: List of message dictionaries with "role" and "content" keys.
                     Standard roles: "system", "user", "assistant"
                     Example: [
                         {"role": "system", "content": "You are a helpful assistant"},
                         {"role": "user", "content": "Hello"}
                     ]
            **kwargs: Additional generation parameters:
                     - temperature: Sampling temperature (0-2)
                     - max_tokens: Maximum tokens in response
                     - top_p: Nucleus sampling parameter
                     - stop: Stop sequences

        Returns:
            Generated text response as string

        Raises:
            LLMProviderError: Base exception for provider errors
            AuthenticationError: If API key/auth is invalid
            RateLimitError: If rate limit is exceeded
            InvalidRequestError: If request parameters are invalid

        Example:
            >>> messages = [{"role": "user", "content": "What is 2+2?"}]
            >>> response = provider.generate(messages, temperature=0)
            >>> print(response)
            "2+2 equals 4"
        """
        pass

    @abstractmethod
    def stream(self, messages: List[Dict[str, str]], **kwargs: Any) -> Iterator[str]:
        """
        Stream text response token by token.

        This enables real-time display of responses as they are generated,
        improving user experience by reducing perceived latency.

        Args:
            messages: List of message dictionaries (same format as generate())
            **kwargs: Additional generation parameters

        Yields:
            Text chunks as they are generated

        Raises:
            Same exceptions as generate()

        Example:
            >>> messages = [{"role": "user", "content": "Tell me a story"}]
            >>> for chunk in provider.stream(messages):
            ...     print(chunk, end="", flush=True)
            Once upon a time...
        """
        pass

    def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_format: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate structured output (JSON) from messages.

        This is an optional method that providers can implement to support
        structured output generation. Useful for:
        - Function calling
        - JSON mode
        - Extracting structured data

        Args:
            messages: List of message dictionaries
            response_format: JSON schema or format specification
                           Example: {"type": "json_object"}
            **kwargs: Additional generation parameters

        Returns:
            Structured response as dictionary

        Raises:
            NotImplementedError: If provider doesn't support structured output

        Example:
            >>> messages = [{"role": "user", "content": "Extract: John is 30"}]
            >>> schema = {
            ...     "type": "object",
            ...     "properties": {
            ...         "name": {"type": "string"},
            ...         "age": {"type": "integer"}
            ...     }
            ... }
            >>> result = provider.generate_structured(messages, schema)
            >>> print(result)
            {"name": "John", "age": 30}
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support structured output. "
            f"This feature is provider-specific."
        )

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return provider name/identifier.

        Returns:
            Provider name (e.g., "openai", "ollama", "anthropic")
        """
        pass

    @property
    def supports_streaming(self) -> bool:
        """
        Whether provider supports streaming.

        Returns:
            True if streaming is supported, False otherwise
        """
        return True

    @property
    def supports_structured_output(self) -> bool:
        """
        Whether provider supports structured output.

        Returns:
            True if structured output is supported, False otherwise
        """
        return False

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"{self.__class__.__name__}(name='{self.name}')"


# ============================================================================
# Exception Hierarchy
# ============================================================================


class LLMProviderError(Exception):
    """
    Base exception for all LLM provider errors.

    All provider-specific errors should be caught and converted to
    this exception hierarchy for consistent error handling.
    """

    pass


class RateLimitError(LLMProviderError):
    """
    Raised when API rate limit is exceeded.

    This should trigger retry logic with exponential backoff.
    """

    pass


class AuthenticationError(LLMProviderError):
    """
    Raised when API authentication fails.

    Common causes:
    - Invalid API key
    - Expired credentials
    - Insufficient permissions

    This should NOT trigger retries - user action required.
    """

    pass


class InvalidRequestError(LLMProviderError):
    """
    Raised when request parameters are invalid.

    Common causes:
    - Invalid model name
    - Malformed messages
    - Unsupported parameters
    - Token limit exceeded

    This should NOT trigger retries - fix request parameters.
    """

    pass


class ContextLengthExceededError(InvalidRequestError):
    """
    Raised when input exceeds model's context window.

    This requires reducing input size (e.g., truncating history).
    """

    pass
