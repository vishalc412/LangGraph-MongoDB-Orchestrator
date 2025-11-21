"""
FastAPI server for MongoDB AI Agent.

This module provides the REST API server for the MongoDB AI Agent,
enabling integration with web frontends and other services.

Usage:
    # Start server
    uvicorn mongodb_agent.api.server:app --reload

    # Or programmatically
    from mongodb_agent.api import create_app
    app = create_app()

Author: AI Agent Development Team
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mongodb_agent.api.routes import router
from mongodb_agent.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    setup_logging(log_level="INFO")
    logger.info("MongoDB AI Agent API starting up...")

    yield

    # Shutdown
    logger.info("MongoDB AI Agent API shutting down...")
    # Cleanup sessions
    from mongodb_agent.api.routes import _sessions
    for thread_id, agent in _sessions.items():
        try:
            agent.close()
        except:
            pass
    _sessions.clear()


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="MongoDB AI Agent API",
        description="""
REST API for MongoDB AI Agent - Natural language interface for MongoDB queries.

## Features

- **Chat**: Send natural language questions and get MongoDB query results
- **Configuration**: Configure LLM providers and MongoDB connection at runtime
- **Health**: Check system health and connectivity
- **Models**: Get list of available LLM models

## Quick Start

1. Configure your API key: `POST /api/config`
2. Start chatting: `POST /api/chat`
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add CORS middleware for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.include_router(router, prefix="/api")

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "MongoDB AI Agent API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/api/health",
        }

    return app


# Create default app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "mongodb_agent.api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
