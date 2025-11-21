"""
MongoDB AI Agent - Production-ready AI agent system for natural language MongoDB queries.

This package provides a complete AI agent system built with LangGraph for orchestrating
natural language interactions with MongoDB databases. Features include:

- Multi-LLM support (OpenAI GPT-4o-mini, Llama via Ollama)
- LangGraph-based agent orchestration with state management
- Conversation memory checkpointing for session continuity
- Complex MongoDB aggregation pipeline support
- Extensible architecture for adding new providers and features
- Production-ready error handling, logging, and monitoring

Architecture:
    - config: Configuration management with environment variable support
    - providers: LLM provider abstraction (OpenAI, Ollama, custom)
    - database: MongoDB client with connection pooling and query execution
    - agents: LangGraph state machine, nodes, and workflow orchestration
    - prompts: Prompt templates with few-shot examples
    - utils: Logging, retry logic, and helper functions

Example usage:
    >>> from mongodb_agent import MongoDBAgent
    >>> agent = MongoDBAgent()
    >>> response = agent.query("What were the top-rated movies in 2020?")
    >>> print(response)

Author: AI Agent Development Team
Version: 1.0.0
License: MIT
"""

__version__ = "1.0.0"
__author__ = "AI Agent Development Team"
__license__ = "MIT"

# Import main components for easy access
from mongodb_agent.config.settings import get_config, AppConfig
from mongodb_agent.providers import create_provider, BaseLLMProvider
from mongodb_agent.database.mongodb_client import MongoDBClient

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "get_config",
    "AppConfig",
    "create_provider",
    "BaseLLMProvider",
    "MongoDBClient",
]
