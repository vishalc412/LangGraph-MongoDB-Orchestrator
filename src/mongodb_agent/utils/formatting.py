"""
Formatting utilities for MongoDB results and conversation history.

This module provides functions to format data for display to users
and for passing to LLMs. Handles JSON serialization, text truncation,
and pretty-printing of complex data structures.

Author: AI Agent Development Team
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId


class MongoDBJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for MongoDB-specific types.

    Handles serialization of:
    - ObjectId -> string
    - datetime -> ISO format string
    - Other BSON types

    Example:
        >>> from bson import ObjectId
        >>> data = {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "Test"}
        >>> json.dumps(data, cls=MongoDBJSONEncoder)
        '{"_id": "507f1f77bcf86cd799439011", "name": "Test"}'
    """

    def default(self, obj: Any) -> Any:
        """Convert MongoDB-specific types to JSON-serializable types."""
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def format_mongodb_result(
    results: List[Dict[str, Any]],
    limit: Optional[int] = None,
    include_count: bool = True,
    pretty: bool = True,
) -> str:
    """
    Format MongoDB query results for display.

    Args:
        results: List of MongoDB documents
        limit: Maximum number of documents to include (None = all)
        include_count: Whether to include total count in output
        pretty: Whether to pretty-print JSON (vs compact)

    Returns:
        Formatted string representation of results

    Example:
        >>> results = [
        ...     {"title": "Inception", "year": 2010, "rating": 8.8},
        ...     {"title": "Interstellar", "year": 2014, "rating": 8.6}
        ... ]
        >>> print(format_mongodb_result(results, limit=10))
        Found 2 results:
        [
          {
            "title": "Inception",
            "year": 2010,
            "rating": 8.8
          },
          ...
        ]
    """
    if not results:
        return "No results found."

    # Apply limit if specified
    display_results = results[:limit] if limit else results
    total_count = len(results)
    displayed_count = len(display_results)

    # Format output
    output_parts = []

    if include_count:
        if limit and total_count > displayed_count:
            output_parts.append(
                f"Showing {displayed_count} of {total_count} results:"
            )
        else:
            output_parts.append(f"Found {total_count} result{'s' if total_count != 1 else ''}:")

    # Serialize to JSON
    indent = 2 if pretty else None
    json_output = json.dumps(
        display_results,
        cls=MongoDBJSONEncoder,
        indent=indent,
        ensure_ascii=False
    )

    output_parts.append(json_output)

    return "\n".join(output_parts)


def format_conversation_history(
    messages: List[Dict[str, str]],
    max_messages: Optional[int] = None,
    include_system: bool = False,
) -> str:
    """
    Format conversation history for display or LLM context.

    Args:
        messages: List of message dictionaries with 'role' and 'content'
        max_messages: Maximum number of recent messages to include
        include_system: Whether to include system messages

    Returns:
        Formatted conversation history

    Example:
        >>> messages = [
        ...     {"role": "user", "content": "What is MongoDB?"},
        ...     {"role": "assistant", "content": "MongoDB is a NoSQL database..."}
        ... ]
        >>> print(format_conversation_history(messages))
        User: What is MongoDB?
        Assistant: MongoDB is a NoSQL database...
    """
    if not messages:
        return "No conversation history."

    # Filter out system messages if requested
    if not include_system:
        messages = [m for m in messages if m.get("role") != "system"]

    # Apply limit to recent messages
    if max_messages:
        messages = messages[-max_messages:]

    # Format each message
    formatted_lines = []
    for msg in messages:
        role = msg.get("role", "unknown").capitalize()
        content = msg.get("content", "")

        # Truncate very long messages
        if len(content) > 500:
            content = content[:497] + "..."

        formatted_lines.append(f"{role}: {content}")

    return "\n".join(formatted_lines)


def truncate_text(
    text: str,
    max_length: int = 100,
    suffix: str = "...",
    middle: bool = False,
) -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: String to append when truncated
        middle: If True, truncate from middle (show start and end)
                If False, truncate from end (show start only)

    Returns:
        Truncated text

    Example:
        >>> truncate_text("This is a very long sentence", max_length=20)
        'This is a very lo...'
        >>> truncate_text("This is a very long sentence", max_length=20, middle=True)
        'This is...sentence'
    """
    if len(text) <= max_length:
        return text

    if middle:
        # Truncate from middle
        suffix_len = len(suffix)
        side_len = (max_length - suffix_len) // 2
        return text[:side_len] + suffix + text[-side_len:]
    else:
        # Truncate from end
        return text[: max_length - len(suffix)] + suffix


def format_query_for_display(
    query_type: str,
    query: Dict[str, Any] | List[Dict[str, Any]],
    collection: str,
) -> str:
    """
    Format MongoDB query for user-friendly display.

    Args:
        query_type: Type of query ('find' or 'aggregate')
        query: Query document or aggregation pipeline
        collection: Collection name

    Returns:
        Formatted query description

    Example:
        >>> query = {"year": {"$gte": 2020}}
        >>> print(format_query_for_display("find", query, "movies"))
        MongoDB Find Query on 'movies' collection:
        {
          "year": {"$gte": 2020}
        }
    """
    output_parts = []

    if query_type == "find":
        output_parts.append(f"MongoDB Find Query on '{collection}' collection:")
    elif query_type == "aggregate":
        output_parts.append(f"MongoDB Aggregation Pipeline on '{collection}' collection:")
    else:
        output_parts.append(f"MongoDB {query_type} on '{collection}' collection:")

    # Format query
    query_str = json.dumps(query, indent=2, ensure_ascii=False, cls=MongoDBJSONEncoder)
    output_parts.append(query_str)

    return "\n".join(output_parts)


def format_error_message(
    error: Exception,
    context: Optional[str] = None,
    include_traceback: bool = False,
) -> str:
    """
    Format error message for user display.

    Args:
        error: Exception object
        context: Optional context description
        include_traceback: Whether to include full traceback (dev mode)

    Returns:
        User-friendly error message

    Example:
        >>> try:
        ...     raise ValueError("Invalid input")
        ... except ValueError as e:
        ...     print(format_error_message(e, context="Query validation"))
        Error during Query validation:
        ValueError: Invalid input
    """
    error_type = type(error).__name__
    error_msg = str(error)

    output_parts = []

    if context:
        output_parts.append(f"Error during {context}:")
    else:
        output_parts.append("An error occurred:")

    output_parts.append(f"{error_type}: {error_msg}")

    if include_traceback:
        import traceback

        output_parts.append("\nTraceback:")
        output_parts.append(traceback.format_exc())

    return "\n".join(output_parts)
