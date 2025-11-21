"""
Pydantic models for API requests and responses.

Author: AI Agent Development Team
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    OLLAMA = "ollama"


class OpenAIModel(str, Enum):
    """Available OpenAI models."""
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_35_TURBO = "gpt-3.5-turbo"


class OllamaModel(str, Enum):
    """Available Ollama models."""
    LLAMA31 = "llama3.1"
    LLAMA32 = "llama3.2"
    MISTRAL = "mistral"
    CODELLAMA = "codellama"
    PHI3 = "phi3"


class ConfigRequest(BaseModel):
    """Request model for updating configuration."""
    provider: LLMProvider = Field(description="LLM provider to use")
    api_key: Optional[str] = Field(default=None, description="API key for OpenAI")
    model: Optional[str] = Field(default=None, description="Model name")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    mongodb_uri: Optional[str] = Field(default=None, description="MongoDB connection URI")
    database: Optional[str] = Field(default=None, description="MongoDB database name")
    collection: Optional[str] = Field(default=None, description="MongoDB collection name")
    ollama_host: Optional[str] = Field(default=None, description="Ollama host URL")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "openai",
                "api_key": "sk-...",
                "model": "gpt-4o-mini",
                "temperature": 0.0,
                "mongodb_uri": "mongodb://localhost:27017",
                "database": "sample_mflix",
                "collection": "movies"
            }
        }


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, description="User message/question")
    thread_id: Optional[str] = Field(default=None, description="Thread ID for conversation")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What were the top-rated movies in 2020?",
                "thread_id": "user-123"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="Agent response")
    thread_id: str = Field(..., description="Thread ID for continuing conversation")
    query_info: Optional[Dict[str, Any]] = Field(default=None, description="Query details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Here are the top-rated movies from 2020...",
                "thread_id": "user-123",
                "query_info": {
                    "query_type": "aggregate",
                    "collection": "movies"
                },
                "timestamp": "2025-01-15T10:30:00Z"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status")
    mongodb_connected: bool = Field(..., description="MongoDB connection status")
    llm_provider: str = Field(..., description="Active LLM provider")
    llm_available: bool = Field(..., description="LLM provider availability")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConfigResponse(BaseModel):
    """Response model for configuration."""
    provider: str
    model: str
    mongodb_database: str
    mongodb_collection: str
    api_key_configured: bool
    ollama_host: Optional[str] = None


class ModelsResponse(BaseModel):
    """Response model for available models."""
    openai_models: List[str]
    ollama_models: List[str]
