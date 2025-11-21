"""
Ollama LLM provider implementation for local model deployment.

This module implements Ollama integration, enabling the use of local
LLMs like Llama 3.1, Mistral, Phi-3, etc. without API costs.

Features:
- Local model deployment (no API costs, data privacy)
- Support for all Ollama-compatible models
- Streaming and non-streaming generation
- No external API dependencies

Prerequisites:
    1. Install Ollama: https://ollama.com/download
    2. Pull a model: `ollama pull llama3.1`
    3. Ensure Ollama service is running: `ollama serve`

Best Practices:
- Use llama3.1 for best quality
- Use smaller models (phi-3) for development/testing
- Ensure sufficient RAM (8GB+ recommended)
- Consider GPU acceleration for better performance

Author: AI Agent Development Team
"""

from typing import Any, Dict, Iterator, List

try:
    from ollama import ChatResponse, chat

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

from mongodb_agent.providers.base import BaseLLMProvider, LLMProviderError
from mongodb_agent.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaProvider(BaseLLMProvider):
    """
    Ollama LLM provider for local model deployment.

    Ollama enables running LLMs locally without API costs. Supports models like:
    - llama3.1 (Meta's latest, highly capable, 8B and 70B variants)
    - mistral (Fast and efficient, 7B)
    - phi-3 (Microsoft's small but capable model, 3.8B)
    - codellama (Specialized for code, 7B-34B)
    - Many others from Ollama model library

    Advantages:
    - No API costs
    - Data privacy (everything local)
    - No rate limits
    - Works offline

    Disadvantages:
    - Requires local resources (RAM, CPU/GPU)
    - Slower than cloud APIs (depending on hardware)
    - Need to manage model updates

    Prerequisites:
        1. Install Ollama: https://ollama.com
        2. Pull model: `ollama pull llama3.1`
        3. Ensure Ollama service is running

    Example usage:
        >>> provider = OllamaProvider(
        ...     host="http://localhost:11434",
        ...     model="llama3.1",
        ...     temperature=0
        ... )
        >>> response = provider.generate([
        ...     {"role": "user", "content": "What is MongoDB?"}
        ... ])
    """

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "llama3.1",
        temperature: float = 0.0,
        timeout: int = 120,
        **kwargs: Any,
    ):
        """
        Initialize Ollama provider.

        Args:
            host: Ollama server URL (default: http://localhost:11434)
            model: Model name (must be pulled first via `ollama pull <model>`)
            temperature: Sampling temperature 0-2 (0=deterministic)
            timeout: Request timeout in seconds (local models can be slower)
            **kwargs: Additional parameters

        Raises:
            ImportError: If ollama package not installed
            LLMProviderError: If cannot connect to Ollama server
        """
        if not OLLAMA_AVAILABLE:
            raise ImportError(
                "Ollama package not installed. Install with: pip install ollama\n"
                "Also ensure Ollama is installed: https://ollama.com/download"
            )

        super().__init__(
            host=host,
            model=model,
            temperature=temperature,
            timeout=timeout,
            **kwargs,
        )

        self.host = host
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

        logger.info(
            f"Initialized Ollama provider",
            extra={"model": model, "host": host, "temperature": temperature},
        )

        # Test connection on initialization
        self._test_connection()

    def _test_connection(self) -> None:
        """
        Test Ollama connection and model availability.

        Raises:
            LLMProviderError: If connection fails or model not available
        """
        try:
            # Simple test query with minimal output
            logger.debug(f"Testing Ollama connection to {self.host}")

            response = chat(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                options={"num_predict": 1},  # Only generate 1 token for test
            )

            logger.info(
                f"Ollama connection test successful",
                extra={"model": self.model, "host": self.host},
            )

        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            raise LLMProviderError(
                f"Failed to connect to Ollama at {self.host}. "
                f"Ensure:\n"
                f"1. Ollama is installed (https://ollama.com/download)\n"
                f"2. Ollama service is running (`ollama serve`)\n"
                f"3. Model '{self.model}' is pulled (`ollama pull {self.model}`)\n"
                f"Error: {e}"
            )

    def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """
        Generate text response using Ollama.

        Args:
            messages: Conversation messages in chat format
            **kwargs: Override default parameters
                     - temperature: Sampling temperature
                     - max_tokens: Maximum tokens (maps to num_predict)

        Returns:
            Generated text response

        Raises:
            LLMProviderError: If generation fails

        Example:
            >>> messages = [
            ...     {"role": "system", "content": "You are a MongoDB expert"},
            ...     {"role": "user", "content": "Explain aggregation pipelines"}
            ... ]
            >>> response = provider.generate(messages)
        """
        try:
            # Prepare generation options
            options: Dict[str, Any] = {
                "temperature": kwargs.get("temperature", self.temperature),
            }

            # Add num_predict if max_tokens specified
            if "max_tokens" in kwargs:
                options["num_predict"] = kwargs["max_tokens"]

            logger.debug(
                f"Generating with Ollama",
                extra={"model": self.model, "message_count": len(messages)},
            )

            # Make request to Ollama
            response: ChatResponse = chat(
                model=self.model, messages=messages, options=options
            )

            generated_text = response.message.content

            logger.info(
                f"Ollama generation complete",
                extra={
                    "response_length": len(generated_text),
                    "model": self.model,
                },
            )

            return generated_text

        except Exception as e:
            logger.error(f"Ollama generation error: {e}", exc_info=True)
            raise LLMProviderError(
                f"Ollama error: {e}. "
                f"Check that Ollama is running and model '{self.model}' is available."
            )

    def stream(self, messages: List[Dict[str, str]], **kwargs: Any) -> Iterator[str]:
        """
        Stream text response token by token.

        Args:
            messages: Conversation messages
            **kwargs: Override default parameters

        Yields:
            Text chunks as they are generated

        Raises:
            LLMProviderError: If streaming fails

        Example:
            >>> messages = [{"role": "user", "content": "Tell me about MongoDB"}]
            >>> for chunk in provider.stream(messages):
            ...     print(chunk, end="", flush=True)
        """
        try:
            options: Dict[str, Any] = {
                "temperature": kwargs.get("temperature", self.temperature),
            }

            if "max_tokens" in kwargs:
                options["num_predict"] = kwargs["max_tokens"]

            logger.debug("Starting Ollama streaming generation")

            # Create streaming request
            stream = chat(
                model=self.model, messages=messages, options=options, stream=True
            )

            # Yield chunks as they arrive
            chunk_count = 0
            for chunk in stream:
                if chunk.get("message", {}).get("content"):
                    chunk_count += 1
                    yield chunk["message"]["content"]

            logger.debug(f"Ollama streaming complete", extra={"chunks": chunk_count})

        except Exception as e:
            logger.error(f"Ollama streaming error: {e}", exc_info=True)
            raise LLMProviderError(f"Ollama streaming error: {e}")

    @property
    def name(self) -> str:
        """Return provider name."""
        return "ollama"

    @property
    def supports_structured_output(self) -> bool:
        """
        Ollama doesn't natively support structured output.

        Note: Some models can generate JSON when prompted correctly,
        but it's not guaranteed to be valid.
        """
        return False
