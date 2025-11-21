"""
OpenAI LLM provider implementation.

This module implements the OpenAI-specific LLM provider using the official
OpenAI Python SDK. Supports GPT-4o-mini, GPT-4o, and other OpenAI models.

Features:
- Synchronous and streaming generation
- Automatic retry with exponential backoff
- Error handling and rate limit management
- Token usage tracking
- Structured output support (JSON mode)

Best Practices:
- Use temperature=0 for deterministic query generation
- Enable streaming for better user experience
- Monitor token usage for cost optimization
- Handle rate limits gracefully

Author: AI Agent Development Team
"""

from typing import Any, Dict, Iterator, List, Optional

import openai
from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from mongodb_agent.providers.base import (
    AuthenticationError,
    BaseLLMProvider,
    InvalidRequestError,
    LLMProviderError,
    RateLimitError,
)
from mongodb_agent.utils.logger import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM provider implementation.

    This provider supports all OpenAI chat models including:
    - gpt-4o-mini (recommended for most tasks, cost-effective)
    - gpt-4o (more capable, higher cost)
    - gpt-4-turbo (fast and capable)
    - gpt-3.5-turbo (legacy, cost-effective)

    Configuration:
        api_key: OpenAI API key (required)
        model: Model identifier
        temperature: 0 for deterministic, higher for creative
        max_tokens: Maximum response length

    Example usage:
        >>> provider = OpenAIProvider(
        ...     api_key="sk-...",
        ...     model="gpt-4o-mini",
        ...     temperature=0
        ... )
        >>> response = provider.generate([
        ...     {"role": "system", "content": "You are a MongoDB expert"},
        ...     {"role": "user", "content": "Convert to MongoDB query: top movies"}
        ... ])
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        max_tokens: int = 2000,
        timeout: int = 60,
        **kwargs: Any,
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (starts with 'sk-')
            model: Model name (default: gpt-4o-mini)
            temperature: Sampling temperature 0-2 (default: 0 for deterministic)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
            **kwargs: Additional parameters passed to OpenAI client
        """
        super().__init__(
            api_key=api_key,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            **kwargs,
        )

        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        logger.info(
            f"Initialized OpenAI provider",
            extra={"model": model, "temperature": temperature},
        )

    @retry(
        retry=retry_if_exception_type((RateLimitError, openai.APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=1, max=60),
    )
    def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """
        Generate text response using OpenAI Chat Completions API.

        This method includes automatic retry logic for transient errors
        using exponential backoff (1s, 2s, 4s delays).

        Args:
            messages: Conversation messages in OpenAI format
            **kwargs: Override default parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response

        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit exceeded (after retries)
            InvalidRequestError: If request parameters are invalid
            LLMProviderError: For other API errors

        Example:
            >>> messages = [
            ...     {"role": "system", "content": "You are helpful"},
            ...     {"role": "user", "content": "Hello"}
            ... ]
            >>> response = provider.generate(messages, temperature=0.7)
        """
        try:
            # Merge default config with call-specific overrides
            generation_params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            }

            logger.debug(
                f"Generating response",
                extra={
                    "model": generation_params["model"],
                    "message_count": len(messages),
                    "temperature": generation_params["temperature"],
                },
            )

            # Make API call
            response = self.client.chat.completions.create(**generation_params)

            # Extract generated text
            generated_text = response.choices[0].message.content or ""

            # Log token usage for monitoring and cost tracking
            usage = response.usage
            if usage:
                logger.info(
                    f"Generation complete",
                    extra={
                        "total_tokens": usage.total_tokens,
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "response_length": len(generated_text),
                    },
                )

            return generated_text

        except openai.AuthenticationError as e:
            logger.error(f"OpenAI authentication failed: {e}")
            raise AuthenticationError(
                f"OpenAI authentication failed. Check your API key. Error: {e}"
            )

        except openai.RateLimitError as e:
            logger.warning(f"OpenAI rate limit hit: {e}")
            raise RateLimitError(f"OpenAI rate limit exceeded. Please retry later. Error: {e}")

        except openai.BadRequestError as e:
            logger.error(f"Invalid OpenAI request: {e}")
            raise InvalidRequestError(f"Invalid request to OpenAI: {e}")

        except openai.APIError as e:
            # Transient API errors - will be retried by decorator
            logger.warning(f"OpenAI API error (will retry): {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected OpenAI error: {e}", exc_info=True)
            raise LLMProviderError(f"OpenAI API error: {e}")

    def stream(self, messages: List[Dict[str, str]], **kwargs: Any) -> Iterator[str]:
        """
        Stream text response token by token.

        This method enables real-time display of responses as they are generated,
        improving perceived latency and user experience.

        Args:
            messages: Conversation messages
            **kwargs: Override default parameters

        Yields:
            Text chunks as they are generated

        Raises:
            Same exceptions as generate()

        Example:
            >>> messages = [{"role": "user", "content": "Tell me a story"}]
            >>> for chunk in provider.stream(messages):
            ...     print(chunk, end="", flush=True)
        """
        try:
            generation_params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "stream": True,  # Enable streaming
            }

            logger.debug("Starting streaming generation")

            # Create streaming request
            stream = self.client.chat.completions.create(**generation_params)

            # Yield chunks as they arrive
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            logger.debug("Streaming complete")

        except openai.AuthenticationError as e:
            raise AuthenticationError(f"OpenAI authentication failed: {e}")
        except openai.RateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit exceeded: {e}")
        except openai.BadRequestError as e:
            raise InvalidRequestError(f"Invalid request to OpenAI: {e}")
        except Exception as e:
            raise LLMProviderError(f"OpenAI streaming error: {e}")

    def generate_structured(
        self, messages: List[Dict[str, str]], response_format: Dict[str, Any], **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output using OpenAI's JSON mode.

        OpenAI's JSON mode ensures the model generates valid JSON that
        conforms to the specified format.

        Args:
            messages: Conversation messages
            response_format: Format specification
                           Example: {"type": "json_object"}
            **kwargs: Additional parameters

        Returns:
            Parsed JSON response as dictionary

        Example:
            >>> messages = [
            ...     {"role": "system", "content": "Extract data as JSON"},
            ...     {"role": "user", "content": "John is 30 years old"}
            ... ]
            >>> result = provider.generate_structured(
            ...     messages,
            ...     response_format={"type": "json_object"}
            ... )
            >>> print(result)
            {"name": "John", "age": 30}
        """
        import json

        try:
            generation_params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "response_format": response_format,
            }

            logger.debug("Generating structured output")

            response = self.client.chat.completions.create(**generation_params)

            generated_text = response.choices[0].message.content or "{}"

            # Parse JSON
            structured_output = json.loads(generated_text)

            logger.debug("Structured output generated successfully")

            return structured_output

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise LLMProviderError(f"Invalid JSON in response: {e}")
        except Exception as e:
            logger.error(f"Structured generation error: {e}")
            raise LLMProviderError(f"Failed to generate structured output: {e}")

    @property
    def name(self) -> str:
        """Return provider name."""
        return "openai"

    @property
    def supports_structured_output(self) -> bool:
        """OpenAI supports structured output via response_format parameter."""
        return True
