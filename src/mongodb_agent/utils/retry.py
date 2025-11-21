"""
Retry logic with exponential backoff.

This module provides robust retry mechanisms for handling transient failures
in distributed systems (API calls, database connections, etc.).

Design Pattern: Decorator pattern for transparent retry logic
Best Practice: Exponential backoff to avoid overwhelming failing services

Author: AI Agent Development Team
"""

import functools
import time
from typing import Any, Callable, Optional, Tuple, Type

from mongodb_agent.utils.logger import get_logger

logger = get_logger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None,
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.

    This decorator automatically retries failed function calls with
    increasing delays between attempts. Useful for handling:
    - Network failures
    - API rate limits
    - Temporary service unavailability
    - Database connection issues

    The delay between retries follows: delay = min(initial_delay * (base ** attempt), max_delay)

    Args:
        max_attempts: Maximum number of attempts (including initial)
        initial_delay: Initial delay in seconds before first retry
        exponential_base: Base for exponential backoff calculation
        max_delay: Maximum delay between retries (cap)
        exceptions: Tuple of exception types to catch and retry
        on_retry: Optional callback function called on each retry
                 Signature: (attempt: int, exception: Exception) -> None

    Returns:
        Decorated function with retry logic

    Example:
        >>> @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        ... def fetch_data():
        ...     # May fail transiently
        ...     return api.get_data()
        >>>
        >>> # Will retry up to 3 times with delays: 1s, 2s, 4s
        >>> data = fetch_data()

    Example with specific exceptions:
        >>> from requests.exceptions import RequestException
        >>> @retry_with_backoff(
        ...     max_attempts=5,
        ...     exceptions=(RequestException, TimeoutError)
        ... )
        ... def call_api():
        ...     return requests.get("https://api.example.com")
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    # Don't retry on last attempt
                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts",
                            exc_info=True,
                            extra={
                                "function": func.__name__,
                                "attempts": max_attempts,
                                "error": str(e),
                            },
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base ** (attempt - 1)), max_delay
                    )

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}. "
                        f"Retrying in {delay:.1f}s...",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt,
                            "max_attempts": max_attempts,
                            "delay": delay,
                            "error": str(e),
                        },
                    )

                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.error(
                                f"Retry callback failed: {callback_error}", exc_info=True
                            )

                    # Wait before retry
                    time.sleep(delay)

            # Should never reach here, but satisfy type checker
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


class RetryableError(Exception):
    """
    Base exception for errors that should trigger retries.

    Custom exceptions can inherit from this to automatically
    be retried by retry_with_backoff.

    Example:
        >>> class TemporaryAPIError(RetryableError):
        ...     pass
        >>>
        >>> @retry_with_backoff(exceptions=(RetryableError,))
        ... def call_api():
        ...     raise TemporaryAPIError("Service unavailable")
    """

    pass


class NonRetryableError(Exception):
    """
    Base exception for errors that should NOT trigger retries.

    Use this for errors that are permanent and won't be fixed by retrying:
    - Invalid input
    - Authentication failures (invalid credentials)
    - Not found errors
    - Permission denied

    Example:
        >>> class InvalidParameterError(NonRetryableError):
        ...     pass
    """

    pass
