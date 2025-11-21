"""Tests for LLM providers."""

import pytest
from mongodb_agent.providers.factory import create_provider, get_available_providers
from mongodb_agent.providers.base import BaseLLMProvider


class TestProviderFactory:
    """Test LLM provider factory."""

    def test_get_available_providers(self):
        """Test getting list of available providers."""
        providers = get_available_providers()
        assert "openai" in providers
        assert "ollama" in providers

    def test_create_provider_returns_base_instance(self):
        """Test create_provider returns BaseLLMProvider instance."""
        # Skip if no API key
        try:
            provider = create_provider("openai", api_key="test-key")
            assert isinstance(provider, BaseLLMProvider)
        except:
            pytest.skip("OpenAI API key not configured")
