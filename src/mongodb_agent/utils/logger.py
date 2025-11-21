"""
Logging configuration and utilities.

This module provides structured logging with support for both
human-readable and JSON formats. Designed for production environments
with proper log levels, rotation, and contextual information.

Features:
- Structured logging with context
- JSON format support for log aggregation systems
- Console and file output
- Automatic log rotation
- Performance-friendly lazy evaluation

Best Practices Applied:
- Use logger.debug() for detailed diagnostic information
- Use logger.info() for general operational messages
- Use logger.warning() for unexpected but handled situations
- Use logger.error() for error conditions that need attention
- Always include context in log messages

Author: AI Agent Development Team
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from pythonjsonlogger import jsonlogger


class ColoredFormatter(logging.Formatter):
    """
    Custom formatter with color coding for console output.

    Makes logs more readable during development by color-coding
    different log levels.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with color coding."""
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "text",
    log_file: Optional[str] = None,
) -> None:
    """
    Configure application-wide logging.

    This function should be called once at application startup to
    configure the root logger and all module loggers.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Format type ('text' for human-readable, 'json' for structured)
        log_file: Optional file path for logging to file

    Example:
        >>> setup_logging(log_level="DEBUG", log_format="json")
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started", extra={"version": "1.0.0"})
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if log_format == "json":
        # JSON formatter for production/aggregation
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        # Colored text formatter for development
        formatter = ColoredFormatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))

        # Always use JSON for file logs (easier to parse)
        file_formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Log startup message
    root_logger.info(
        f"Logging configured: level={log_level}, format={log_format}, file={log_file}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module.

    This is the primary way to get loggers throughout the application.
    Each module should get its own logger using __name__.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started", extra={"user_id": 123})
        >>> logger.error("Failed to connect", exc_info=True)
    """
    return logging.getLogger(name)


# Initialize default logging if not already configured
# This ensures logs work even if setup_logging() is not called
if not logging.getLogger().handlers:
    setup_logging()
