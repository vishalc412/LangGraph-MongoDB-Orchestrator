"""
Agent state management using TypedDict.

This module defines the state structure used by the LangGraph agent.
The state is passed between nodes and maintains all context needed
for query generation and response formatting.

Design: Using TypedDict (not Pydantic) as recommended by LangGraph
for better type checking and performance.

Author: AI Agent Development Team
"""

from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """
    State structure for the MongoDB AI Agent.

    This TypedDict defines all fields that can be present in the agent state
    as it flows through the LangGraph workflow.

    Fields:
        messages: Conversation history in chat format
        user_question: Current user question/query
        schema_info: MongoDB collection schema information
        query_type: Type of MongoDB query ("find" or "aggregate")
        collection: Target MongoDB collection name
        mongo_query: Generated MongoDB query (dict or list)
        query_explanation: Human-readable explanation of the query
        query_results: Raw results from MongoDB query execution
        formatted_results: User-friendly formatted results
        final_response: Complete response to show to user
        error: Error message if any step failed
        metadata: Additional metadata (execution time, token usage, etc.)

    Note: total=False allows partial state dictionaries
    """

    # Conversation context
    messages: List[Dict[str, str]]

    # User input
    user_question: str

    # Database schema
    schema_info: Dict[str, Any]

    # Query generation outputs
    query_type: str
    collection: str
    mongo_query: Dict[str, Any] | List[Dict[str, Any]]
    query_explanation: str

    # Query execution outputs
    query_results: List[Dict[str, Any]]
    formatted_results: str

    # Final output
    final_response: str

    # Error handling
    error: Optional[str]

    # Metadata
    metadata: Dict[str, Any]


def create_initial_state(user_question: str, messages: Optional[List[Dict[str, str]]] = None) -> AgentState:
    """
    Create initial agent state for a new query.

    Args:
        user_question: User's question/query
        messages: Optional conversation history

    Returns:
        Initial AgentState dictionary

    Example:
        >>> state = create_initial_state("What were the top movies in 2020?")
        >>> print(state["user_question"])
        'What were the top movies in 2020?'
    """
    if messages is None:
        messages = []

    return AgentState(
        messages=messages,
        user_question=user_question,
        metadata={}
    )


def add_message_to_state(state: AgentState, role: str, content: str) -> AgentState:
    """
    Add a message to the conversation history.

    Args:
        state: Current agent state
        role: Message role ("user", "assistant", "system")
        content: Message content

    Returns:
        Updated state with new message

    Example:
        >>> state = create_initial_state("Hello")
        >>> state = add_message_to_state(state, "assistant", "Hi there!")
        >>> print(len(state["messages"]))
        1
    """
    messages = state.get("messages", [])
    messages.append({"role": role, "content": content})
    state["messages"] = messages
    return state
