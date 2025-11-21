"""Tests for configuration management."""

import pytest
from mongodb_agent.config.settings import AppConfig, get_config, reload_config


class TestConfiguration:
    """Test configuration loading and validation."""

    def test_default_config(self):
        """Test default configuration loads successfully."""
        config = get_config()
        assert isinstance(config, AppConfig)
        assert config.app_name == "MongoDB AI Agent"

    def test_get_llm_config_openai(self):
        """Test getting OpenAI configuration."""
        config = get_config()
        openai_config = config.get_llm_config("openai")
        assert openai_config.model == "gpt-4o-mini"

    def test_get_llm_config_ollama(self):
        """Test getting Ollama configuration."""
        config = get_config()
        ollama_config = config.get_llm_config("ollama")
        assert ollama_config.model == "llama3.1"

    def test_invalid_provider(self):
        """Test invalid provider raises error."""
        config = get_config()
        with pytest.raises(ValueError):
            config.get_llm_config("invalid")
