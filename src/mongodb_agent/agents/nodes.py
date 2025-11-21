"""
Agent node functions for LangGraph workflow.

This module contains all the node functions that process the agent state.
Each node performs a specific task in the query answering workflow:

1. get_schema: Retrieve database schema
2. generate_query: Convert natural language to MongoDB query
3. execute_query: Run the MongoDB query
4. format_response: Create user-friendly response

Design: Pure functions that take state and return updated state
Best Practice: Each node should be focused, testable, and composable

Author: AI Agent Development Team
"""

import json
from typing import Any, Dict

from mongodb_agent.agents.state import AgentState
from mongodb_agent.database.mongodb_client import MongoDBClient
from mongodb_agent.database.query_executor import QueryExecutor
from mongodb_agent.prompts.templates import (
    SYSTEM_PROMPT,
    create_query_generation_prompt,
    create_response_formatting_prompt,
)
from mongodb_agent.providers.base import BaseLLMProvider
from mongodb_agent.utils.logger import get_logger

logger = get_logger(__name__)


def get_schema_node(state: AgentState, mongodb_client: MongoDBClient, collection: str) -> AgentState:
    """
    Node: Retrieve schema information for the target collection.

    This node connects to MongoDB and extracts schema information
    that will help the LLM generate accurate queries.

    Args:
        state: Current agent state
        mongodb_client: MongoDB client instance
        collection: Collection name to get schema for

    Returns:
        Updated state with schema_info populated

    Example:
        >>> state = {"user_question": "Find movies from 2020"}
        >>> state = get_schema_node(state, client, "movies")
        >>> print(state["schema_info"]["fields"])
        ['title', 'year', 'genres', ...]
    """
    try:
        logger.info(f"Retrieving schema for collection: {collection}")

        # Get schema from MongoDB
        schema_info = mongodb_client.get_collection_schema(collection)

        # Update state
        state["schema_info"] = schema_info
        state["collection"] = collection

        logger.info(
            f"Schema retrieved successfully",
            extra={
                "collection": collection,
                "field_count": len(schema_info.get("fields", [])),
            },
        )

        return state

    except Exception as e:
        logger.error(f"Failed to retrieve schema: {e}", exc_info=True)
        state["error"] = f"Failed to retrieve database schema: {str(e)}"
        return state


def generate_query_node(state: AgentState, llm_provider: BaseLLMProvider) -> AgentState:
    """
    Node: Generate MongoDB query from natural language question.

    This node uses the LLM to convert the user's question into
    a valid MongoDB query (find or aggregation pipeline).

    Args:
        state: Current agent state (must have user_question and schema_info)
        llm_provider: LLM provider instance

    Returns:
        Updated state with query_type, mongo_query, and query_explanation

    Example:
        >>> state = {
        ...     "user_question": "Top 5 movies from 2020",
        ...     "schema_info": {...}
        ... }
        >>> state = generate_query_node(state, llm_provider)
        >>> print(state["query_type"])
        'aggregate'
    """
    try:
        logger.info("Generating MongoDB query from natural language")

        # Prepare prompt
        prompt = create_query_generation_prompt(
            user_question=state["user_question"],
            schema_info=state.get("schema_info", {}),
            conversation_history=state.get("messages", []),
        )

        # Generate query using LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        logger.debug("Calling LLM for query generation")
        response = llm_provider.generate(messages, temperature=0)

        logger.debug(f"LLM response: {response[:200]}...")

        # Parse JSON response
        # LLM should return JSON with: query_type, collection, query, explanation
        try:
            # Extract JSON from response (handle markdown code blocks)
            response_cleaned = response.strip()
            if "```json" in response_cleaned:
                # Extract from code block
                start = response_cleaned.find("```json") + 7
                end = response_cleaned.find("```", start)
                response_cleaned = response_cleaned[start:end].strip()
            elif "```" in response_cleaned:
                # Extract from generic code block
                start = response_cleaned.find("```") + 3
                end = response_cleaned.find("```", start)
                response_cleaned = response_cleaned[start:end].strip()

            query_data = json.loads(response_cleaned)

            # Update state with parsed query
            state["query_type"] = query_data.get("query_type", "find")
            state["collection"] = query_data.get("collection", state.get("collection", "movies"))
            state["mongo_query"] = query_data.get("query", {})
            state["query_explanation"] = query_data.get("explanation", "")

            logger.info(
                f"Query generated successfully",
                extra={
                    "query_type": state["query_type"],
                    "explanation": state["query_explanation"][:100],
                },
            )

            return state

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {response}")
            state["error"] = f"Failed to parse LLM response: {e}"
            return state

    except Exception as e:
        logger.error(f"Query generation failed: {e}", exc_info=True)
        state["error"] = f"Failed to generate query: {str(e)}"
        return state


def execute_query_node(state: AgentState, query_executor: QueryExecutor) -> AgentState:
    """
    Node: Execute the generated MongoDB query.

    This node runs the MongoDB query and stores the results in the state.

    Args:
        state: Current agent state (must have query_type, collection, mongo_query)
        query_executor: Query executor instance

    Returns:
        Updated state with query_results and formatted_results

    Example:
        >>> state = {
        ...     "query_type": "find",
        ...     "collection": "movies",
        ...     "mongo_query": {"year": 2020}
        ... }
        >>> state = execute_query_node(state, executor)
        >>> print(len(state["query_results"]))
        15
    """
    try:
        logger.info("Executing MongoDB query")

        # Check for required fields
        if "query_type" not in state or "mongo_query" not in state:
            raise ValueError("State missing required fields: query_type or mongo_query")

        # Execute query
        result = query_executor.execute_query(
            query_type=state["query_type"],
            collection=state.get("collection", "movies"),
            query=state["mongo_query"],
            limit=100,
        )

        if result["success"]:
            # Update state with results
            state["query_results"] = result["results"]
            state["formatted_results"] = result["formatted_result"]

            logger.info(
                f"Query executed successfully",
                extra={"result_count": len(result["results"])},
            )
        else:
            # Query failed
            state["error"] = result.get("error", "Query execution failed")
            logger.error(f"Query execution failed: {state['error']}")

        return state

    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        state["error"] = f"Failed to execute query: {str(e)}"
        return state


def format_response_node(state: AgentState, llm_provider: BaseLLMProvider) -> AgentState:
    """
    Node: Format query results into user-friendly response.

    This node uses the LLM to create a natural language response
    that presents the query results in a clear, conversational manner.

    Args:
        state: Current agent state (must have user_question, mongo_query, query_results)
        llm_provider: LLM provider instance

    Returns:
        Updated state with final_response

    Example:
        >>> state = {
        ...     "user_question": "Top movies from 2020",
        ...     "query_results": [...]
        ... }
        >>> state = format_response_node(state, llm_provider)
        >>> print(state["final_response"])
        'Here are the top movies from 2020: ...'
    """
    try:
        logger.info("Formatting response for user")

        # Check for errors from previous nodes
        if "error" in state and state["error"]:
            state["final_response"] = (
                f"I encountered an error while processing your query:\n\n"
                f"{state['error']}\n\n"
                f"Please try rephrasing your question or contact support if the issue persists."
            )
            return state

        # Prepare query display
        from mongodb_agent.utils.formatting import format_query_for_display

        query_display = format_query_for_display(
            query_type=state.get("query_type", "unknown"),
            query=state.get("mongo_query", {}),
            collection=state.get("collection", "unknown"),
        )

        # Prepare prompt
        prompt = create_response_formatting_prompt(
            user_question=state["user_question"],
            query_display=query_display,
            query_results=state.get("formatted_results", "No results"),
        )

        # Generate response using LLM
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        logger.debug("Calling LLM for response formatting")
        response = llm_provider.generate(messages, temperature=0.3)  # Slightly higher temp for natural language

        # Update state
        state["final_response"] = response.strip()

        logger.info("Response formatted successfully")

        return state

    except Exception as e:
        logger.error(f"Response formatting failed: {e}", exc_info=True)
        # Fallback to simple formatting
        state["final_response"] = (
            f"Query completed successfully. Results:\n\n"
            f"{state.get('formatted_results', 'No results available')}"
        )
        return state


def error_handler_node(state: AgentState) -> AgentState:
    """
    Node: Handle errors gracefully.

    This is a fallback node that creates a user-friendly error message
    when something goes wrong in the workflow.

    Args:
        state: Current agent state (should have error field)

    Returns:
        Updated state with final_response set to error message

    Example:
        >>> state = {"error": "Connection failed"}
        >>> state = error_handler_node(state)
        >>> print(state["final_response"])
        'I encountered an error: Connection failed...'
    """
    error_message = state.get("error", "An unknown error occurred")

    state["final_response"] = (
        f"I encountered an error while processing your query:\n\n"
        f"{error_message}\n\n"
        f"Please try:\n"
        f"1. Rephrasing your question\n"
        f"2. Being more specific about what you're looking for\n"
        f"3. Checking if the database connection is working\n\n"
        f"If the problem persists, please contact support."
    )

    logger.warning(f"Error handled: {error_message}")

    return state
