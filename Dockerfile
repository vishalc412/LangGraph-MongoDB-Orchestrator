# ============================================================================
# MongoDB AI Agent - Production Dockerfile
# ============================================================================
# Multi-stage build for optimized production image
#
# Build: docker build -t mongodb-ai-agent:latest .
# Run: docker run --env-file .env mongodb-ai-agent:latest
#
# Author: AI Agent Development Team
# ============================================================================

# Stage 1: Build dependencies
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Production image
FROM python:3.11-slim

# Set metadata
LABEL maintainer="AI Agent Development Team"
LABEL description="MongoDB AI Agent - Natural language interface for MongoDB"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    PATH="/app/src:${PATH}"

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ /app/src/
COPY data/ /app/data/
COPY scripts/ /app/scripts/

# Create necessary directories with proper permissions
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from mongodb_agent.config import get_config; get_config()" || exit 1

# Default command (can be overridden)
CMD ["python", "-m", "mongodb_agent.main", "chat"]
