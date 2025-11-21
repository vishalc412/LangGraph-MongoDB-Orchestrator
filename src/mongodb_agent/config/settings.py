"""
Configuration management for MongoDB AI Agent system.

This module provides type-safe configuration management using Pydantic Settings.
All settings can be overridden via environment variables for flexibility across
different deployment environments.

The configuration is organized into logical sections:
- Application settings (environment, logging, debug mode)
- LLM provider configurations (OpenAI, Ollama)
- MongoDB connection settings
- Checkpointer configuration for conversation memory
- Agent behavior settings

Design Pattern: Singleton pattern for global configuration access
Best Practice: Environment-based configuration with sensible defaults

Author: AI Agent Development Team
Date: 2025
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAIConfig(BaseSettings):
    """
    OpenAI-specific configuration settings.

    Environment variables should be prefixed with OPENAI_
    Example: OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE

    Attributes:
        api_key: OpenAI API key (required for OpenAI provider)
        model: Model identifier (gpt-4o-mini, gpt-4o, etc.)
        temperature: Sampling temperature (0=deterministic, 2=creative)
        max_tokens: Maximum tokens in response
        timeout: API request timeout in seconds
    """

    api_key: str = Field(
        default="", description="OpenAI API key - REQUIRED if using OpenAI provider"
    )
    model: str = Field(default="gpt-4o-mini", description="OpenAI model identifier")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum response tokens")
    timeout: int = Field(default=60, gt=0, description="API timeout in seconds")

    model_config = SettingsConfigDict(env_prefix="OPENAI_", case_sensitive=False)


class OllamaConfig(BaseSettings):
    """
    Ollama-specific configuration for local LLM deployment.

    Ollama enables running LLMs locally without API costs, ideal for:
    - Development and testing
    - Privacy-sensitive applications
    - Cost optimization
    - Offline operation

    Environment variables should be prefixed with OLLAMA_

    Attributes:
        host: Ollama server URL
        model: Model name (must be pulled via `ollama pull <model>`)
        temperature: Sampling temperature
        timeout: Request timeout (local models may be slower)
    """

    host: str = Field(default="http://localhost:11434", description="Ollama server URL")
    model: str = Field(default="llama3.1", description="Ollama model name")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Sampling temperature")
    timeout: int = Field(default=120, gt=0, description="Request timeout in seconds")

    model_config = SettingsConfigDict(env_prefix="OLLAMA_", case_sensitive=False)


class MongoDBConfig(BaseSettings):
    """
    MongoDB connection configuration.

    Supports both local MongoDB and MongoDB Atlas (cloud).
    Uses connection pooling for efficient resource utilization.

    Environment variables should be prefixed with MONGODB_

    Attributes:
        uri: MongoDB connection string
        database: Target database name
        collection: Default collection name
        max_pool_size: Connection pool size for performance
        timeout_ms: Connection timeout in milliseconds
    """

    uri: str = Field(
        default="mongodb://localhost:27017", description="MongoDB connection URI"
    )
    database: str = Field(default="sample_mflix", description="Database name")
    collection: str = Field(default="movies", description="Default collection name")
    max_pool_size: int = Field(default=10, gt=0, description="Connection pool size")
    timeout_ms: int = Field(default=5000, gt=0, description="Connection timeout (ms)")

    model_config = SettingsConfigDict(env_prefix="MONGODB_", case_sensitive=False)

    @field_validator("uri")
    @classmethod
    def validate_uri(cls, v: str) -> str:
        """Validate MongoDB URI format."""
        if not (v.startswith("mongodb://") or v.startswith("mongodb+srv://")):
            raise ValueError(
                "MongoDB URI must start with mongodb:// or mongodb+srv://. "
                f"Got: {v[:20]}..."
            )
        return v


class CheckpointerConfig(BaseSettings):
    """
    Configuration for LangGraph memory checkpointing.

    Checkpointing enables conversation continuity across sessions by
    persisting agent state. Supports multiple backend types:

    - memory: In-memory (lost on restart, for development)
    - sqlite: SQLite database (persistent, single-instance)
    - postgres: PostgreSQL (persistent, multi-instance, production)

    Environment variables should be prefixed with CHECKPOINTER_

    Attributes:
        type: Backend type selection
        sqlite_path: SQLite database file path
        postgres_uri: PostgreSQL connection URI (if using postgres)
    """

    type: Literal["memory", "sqlite", "postgres"] = Field(
        default="sqlite", description="Checkpointer backend type"
    )
    sqlite_path: str = Field(default="./data/checkpoints.db", description="SQLite DB path")
    postgres_uri: Optional[str] = Field(
        default=None, description="PostgreSQL connection URI"
    )

    model_config = SettingsConfigDict(env_prefix="CHECKPOINTER_", case_sensitive=False)

    @field_validator("sqlite_path")
    @classmethod
    def ensure_sqlite_directory(cls, v: str) -> str:
        """Ensure SQLite directory exists."""
        path = Path(v)
        path.parent.mkdir(parents=True, exist_ok=True)
        return v


class AppConfig(BaseSettings):
    """
    Main application configuration combining all sub-configs.

    This is the primary configuration class used throughout the application.
    It aggregates all component-specific configurations and provides
    global application settings.

    Configuration Priority (highest to lowest):
    1. Environment variables
    2. .env file
    3. Default values

    Attributes:
        app_name: Application name for logging and display
        environment: Deployment environment (dev/staging/production)
        debug: Enable debug mode with verbose logging
        log_level: Logging level (DEBUG/INFO/WARNING/ERROR)
        default_llm_provider: Default LLM provider selection
        max_conversation_turns: Conversation history limit
        enable_streaming: Enable streaming responses
    """

    # Application settings
    app_name: str = Field(default="MongoDB AI Agent", description="Application name")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Deployment environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )

    # LLM Provider selection
    default_llm_provider: Literal["openai", "ollama"] = Field(
        default="openai", description="Default LLM provider"
    )

    # Sub-configurations (initialized with defaults)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    mongodb: MongoDBConfig = Field(default_factory=MongoDBConfig)
    checkpointer: CheckpointerConfig = Field(default_factory=CheckpointerConfig)

    # Agent settings
    max_conversation_turns: int = Field(
        default=10, gt=0, description="Maximum conversation turns to keep in memory"
    )
    enable_streaming: bool = Field(default=True, description="Enable response streaming")

    # Retry configuration
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    retry_delay_seconds: float = Field(default=2.0, gt=0, description="Retry delay")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    def get_llm_config(self, provider: Optional[str] = None) -> OpenAIConfig | OllamaConfig:
        """
        Get LLM configuration for specified provider.

        Args:
            provider: LLM provider name ("openai" or "ollama").
                     If None, uses default_llm_provider.

        Returns:
            Configuration object for the specified provider.

        Raises:
            ValueError: If provider is unknown.

        Example:
            >>> config = get_config()
            >>> openai_config = config.get_llm_config("openai")
            >>> print(openai_config.model)
            'gpt-4o-mini'
        """
        provider = provider or self.default_llm_provider

        if provider == "openai":
            return self.openai
        elif provider == "ollama":
            return self.ollama
        else:
            raise ValueError(
                f"Unknown LLM provider: {provider}. " f"Supported: openai, ollama"
            )

    def validate_provider_config(self, provider: Optional[str] = None) -> bool:
        """
        Validate that required configuration is present for provider.

        Args:
            provider: Provider to validate (uses default if None)

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid or incomplete
        """
        provider = provider or self.default_llm_provider

        if provider == "openai":
            if not self.openai.api_key or self.openai.api_key == "":
                raise ValueError(
                    "OpenAI API key not configured. "
                    "Set OPENAI_API_KEY environment variable."
                )
        elif provider == "ollama":
            if not self.ollama.host:
                raise ValueError("Ollama host not configured.")

        return True


# Global configuration instance (Singleton pattern)
# This is initialized once and reused throughout the application lifecycle
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """
    Get global configuration instance (Singleton pattern).

    This function ensures only one configuration instance exists,
    preventing redundant file reads and ensuring consistency.

    Returns:
        AppConfig instance with all settings loaded.

    Example:
        >>> from mongodb_agent.config import get_config
        >>> config = get_config()
        >>> print(config.default_llm_provider)
        'openai'
    """
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def reload_config() -> AppConfig:
    """
    Force reload of configuration from environment/files.

    Useful for testing or when configuration changes at runtime.
    In production, configuration should remain stable after initialization.

    Returns:
        Newly loaded AppConfig instance.

    Example:
        >>> # Update environment variable
        >>> os.environ['DEFAULT_LLM_PROVIDER'] = 'ollama'
        >>> config = reload_config()
        >>> print(config.default_llm_provider)
        'ollama'
    """
    global _config
    _config = AppConfig()
    return _config
