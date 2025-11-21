"""Prompt templates for the MongoDB AI Agent."""

from mongodb_agent.prompts.templates import (
    SYSTEM_PROMPT,
    QUERY_GENERATION_PROMPT,
    RESPONSE_FORMATTING_PROMPT,
    create_query_generation_prompt,
    create_response_formatting_prompt,
)

__all__ = [
    "SYSTEM_PROMPT",
    "QUERY_GENERATION_PROMPT",
    "RESPONSE_FORMATTING_PROMPT",
    "create_query_generation_prompt",
    "create_response_formatting_prompt",
]
