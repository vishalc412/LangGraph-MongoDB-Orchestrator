"""
FastAPI routes for MongoDB AI Agent API.

Author: AI Agent Development Team
"""

import os
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from mongodb_agent.api.models import (
    ChatRequest,
    ChatResponse,
    ConfigRequest,
    ConfigResponse,
    ErrorResponse,
    HealthResponse,
    ModelsResponse,
    OpenAIModel,
    OllamaModel,
)
from mongodb_agent.config.settings import get_config, reload_config
from mongodb_agent.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# In-memory session storage (for demo - use Redis in production)
_sessions: dict = {}
_runtime_config: dict = {}


def get_runtime_config() -> dict:
    """Get runtime configuration."""
    return _runtime_config


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns system health status including MongoDB and LLM availability.
    """
    config = get_config()
    runtime = get_runtime_config()

    # Check MongoDB connection
    mongodb_connected = False
    try:
        from mongodb_agent.database.mongodb_client import MongoDBClient
        uri = runtime.get("mongodb_uri") or config.mongodb.uri
        with MongoDBClient() as client:
            mongodb_connected = client.ping()
    except Exception as e:
        logger.warning(f"MongoDB health check failed: {e}")

    # Check LLM availability
    provider = runtime.get("provider") or config.default_llm_provider
    api_key = runtime.get("api_key") or config.openai.api_key
    llm_available = bool(api_key) if provider == "openai" else True

    return HealthResponse(
        status="healthy" if mongodb_connected else "degraded",
        mongodb_connected=mongodb_connected,
        llm_provider=provider,
        llm_available=llm_available,
        version="1.0.0",
    )


@router.get("/config", response_model=ConfigResponse, tags=["Configuration"])
async def get_current_config() -> ConfigResponse:
    """Get current configuration."""
    config = get_config()
    runtime = get_runtime_config()

    provider = runtime.get("provider") or config.default_llm_provider

    if provider == "openai":
        model = runtime.get("model") or config.openai.model
    else:
        model = runtime.get("model") or config.ollama.model

    api_key = runtime.get("api_key") or config.openai.api_key

    return ConfigResponse(
        provider=provider,
        model=model,
        mongodb_database=runtime.get("database") or config.mongodb.database,
        mongodb_collection=runtime.get("collection") or config.mongodb.collection,
        api_key_configured=bool(api_key and len(api_key) > 10),
        ollama_host=runtime.get("ollama_host") or config.ollama.host,
    )


@router.post("/config", response_model=ConfigResponse, tags=["Configuration"])
async def update_config(request: ConfigRequest) -> ConfigResponse:
    """
    Update runtime configuration.

    Allows changing LLM provider, API keys, and MongoDB settings at runtime.
    """
    global _runtime_config

    # Update runtime config
    if request.provider:
        _runtime_config["provider"] = request.provider.value
    if request.api_key:
        _runtime_config["api_key"] = request.api_key
        # Also set in environment for providers to pick up
        os.environ["OPENAI_API_KEY"] = request.api_key
    if request.model:
        _runtime_config["model"] = request.model
    if request.mongodb_uri:
        _runtime_config["mongodb_uri"] = request.mongodb_uri
    if request.database:
        _runtime_config["database"] = request.database
    if request.collection:
        _runtime_config["collection"] = request.collection
    if request.ollama_host:
        _runtime_config["ollama_host"] = request.ollama_host
    if request.temperature is not None:
        _runtime_config["temperature"] = request.temperature

    logger.info(f"Configuration updated: provider={request.provider}")

    return await get_current_config()


@router.get("/models", response_model=ModelsResponse, tags=["Configuration"])
async def get_available_models() -> ModelsResponse:
    """Get list of available models for each provider."""
    return ModelsResponse(
        openai_models=[m.value for m in OpenAIModel],
        ollama_models=[m.value for m in OllamaModel],
    )


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the AI agent and get a response.

    Converts natural language questions to MongoDB queries and returns results.
    """
    try:
        runtime = get_runtime_config()
        config = get_config()

        # Generate thread_id if not provided
        thread_id = request.thread_id or str(uuid.uuid4())

        # Get or create agent for this session
        agent = await _get_or_create_agent(thread_id, runtime, config)

        logger.info(f"Processing chat request", extra={
            "thread_id": thread_id,
            "message_length": len(request.message),
        })

        # Get response from agent
        response = agent.query(request.message, thread_id=thread_id)

        return ChatResponse(
            response=response,
            thread_id=thread_id,
            query_info=None,  # Could extract from agent state
        )

    except Exception as e:
        logger.error(f"Chat request failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post("/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatRequest):
    """
    Stream response from the AI agent.

    Returns a streaming response for real-time output.
    """
    try:
        runtime = get_runtime_config()
        config = get_config()

        thread_id = request.thread_id or str(uuid.uuid4())
        agent = await _get_or_create_agent(thread_id, runtime, config)

        async def generate():
            try:
                # For now, yield complete response (streaming support pending)
                response = agent.query(request.message, thread_id=thread_id)
                yield f"data: {response}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: Error: {str(e)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except Exception as e:
        logger.error(f"Streaming request failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/{thread_id}", tags=["Chat"])
async def clear_chat_history(thread_id: str):
    """Clear chat history for a specific thread."""
    if thread_id in _sessions:
        # Close agent and remove from sessions
        try:
            _sessions[thread_id].close()
        except:
            pass
        del _sessions[thread_id]
        logger.info(f"Cleared session: {thread_id}")
        return {"message": f"Session {thread_id} cleared"}

    return {"message": f"Session {thread_id} not found"}


async def _get_or_create_agent(thread_id: str, runtime: dict, config):
    """Get existing agent or create a new one for the session."""
    from mongodb_agent.agents.graph import MongoDBAgent
    from mongodb_agent.providers import create_provider
    from mongodb_agent.database.mongodb_client import MongoDBClient

    # Check if agent exists for this thread
    if thread_id in _sessions:
        return _sessions[thread_id]

    # Create new agent with runtime config
    provider_name = runtime.get("provider") or config.default_llm_provider

    # Build provider kwargs
    if provider_name == "openai":
        provider_kwargs = {
            "api_key": runtime.get("api_key") or config.openai.api_key,
            "model": runtime.get("model") or config.openai.model,
            "temperature": runtime.get("temperature", config.openai.temperature),
        }
    else:
        provider_kwargs = {
            "host": runtime.get("ollama_host") or config.ollama.host,
            "model": runtime.get("model") or config.ollama.model,
            "temperature": runtime.get("temperature", config.ollama.temperature),
        }

    # Create provider
    try:
        llm_provider = create_provider(provider_name, **provider_kwargs)
    except Exception as e:
        logger.error(f"Failed to create provider: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to initialize LLM provider: {str(e)}"
        )

    # Create MongoDB client
    collection = runtime.get("collection") or config.mongodb.collection

    # Create agent
    agent = MongoDBAgent(
        llm_provider=llm_provider,
        collection=collection,
        thread_id=thread_id,
    )

    # Store in sessions
    _sessions[thread_id] = agent

    logger.info(f"Created new agent for thread: {thread_id}")

    return agent
