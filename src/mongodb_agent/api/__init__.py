"""FastAPI REST API for MongoDB AI Agent."""

from mongodb_agent.api.server import app, create_app
from mongodb_agent.api.routes import router
from mongodb_agent.api.models import (
    ChatRequest,
    ChatResponse,
    ConfigRequest,
    HealthResponse,
)

__all__ = [
    "app",
    "create_app",
    "router",
    "ChatRequest",
    "ChatResponse",
    "ConfigRequest",
    "HealthResponse",
]
