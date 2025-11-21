"""
LangGraph workflow definition for MongoDB AI Agent.

This module creates the agent workflow using LangGraph's StateGraph.
The workflow orchestrates the query answering process:

1. Get Schema -> 2. Generate Query -> 3. Execute Query -> 4. Format Response

Features:
- Conditional routing based on errors
- Memory checkpointing for conversation continuity
- Clean separation of concerns
- Production-ready error handling

Design: Using LangGraph for state management and workflow orchestration
Best Practice: Each node is stateless; all context in state object

Author: AI Agent Development Team
"""

from typing import Any, Dict, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from mongodb_agent.agents.nodes import (
    error_handler_node,
    execute_query_node,
    format_response_node,
    generate_query_node,
    get_schema_node,
)
from mongodb_agent.agents.state import AgentState, add_message_to_state, create_initial_state
from mongodb_agent.config.settings import get_config
from mongodb_agent.database.mongodb_client import MongoDBClient
from mongodb_agent.database.query_executor import QueryExecutor
from mongodb_agent.providers import create_provider
from mongodb_agent.providers.base import BaseLLMProvider
from mongodb_agent.utils.logger import get_logger

logger = get_logger(__name__)


def should_continue_after_schema(state: AgentState) -> str:
    """
    Conditional edge: Decide whether to continue or handle error after schema retrieval.

    Args:
        state: Current agent state

    Returns:
        "generate_query" if schema retrieved successfully, "error_handler" otherwise
    """
    if "error" in state and state["error"]:
        logger.warning("Error detected after schema retrieval, routing to error handler")
        return "error_handler"
    return "generate_query"


def should_continue_after_generation(state: AgentState) -> str:
    """
    Conditional edge: Decide whether to continue or handle error after query generation.

    Args:
        state: Current agent state

    Returns:
        "execute_query" if query generated successfully, "error_handler" otherwise
    """
    if "error" in state and state["error"]:
        logger.warning("Error detected after query generation, routing to error handler")
        return "error_handler"
    return "execute_query"


def should_continue_after_execution(state: AgentState) -> str:
    """
    Conditional edge: Decide whether to continue or handle error after query execution.

    Args:
        state: Current agent state

    Returns:
        "format_response" if query executed successfully, "error_handler" otherwise
    """
    if "error" in state and state["error"]:
        logger.warning("Error detected after query execution, routing to error handler")
        return "error_handler"
    return "format_response"


def create_agent_graph(
    llm_provider: Optional[BaseLLMProvider] = None,
    mongodb_client: Optional[MongoDBClient] = None,
    query_executor: Optional[QueryExecutor] = None,
    checkpointer: Optional[Any] = None,
    collection: str = "movies",
) -> StateGraph:
    """
    Create the LangGraph state graph for the MongoDB AI Agent.

    This function builds the complete workflow graph with all nodes and edges.

    Workflow:
        START -> get_schema -> generate_query -> execute_query -> format_response -> END
                      |              |                 |
                      v              v                 v
                error_handler -> error_handler -> error_handler

    Args:
        llm_provider: LLM provider instance (creates default if None)
        mongodb_client: MongoDB client instance (creates default if None)
        query_executor: Query executor instance (creates default if None)
        checkpointer: Checkpointer for conversation memory (creates default if None)
        collection: Default collection name

    Returns:
        Compiled StateGraph ready to use

    Example:
        >>> graph = create_agent_graph()
        >>> result = graph.invoke(
        ...     {"user_question": "Find movies from 2020"},
        ...     config={"configurable": {"thread_id": "user123"}}
        ... )
        >>> print(result["final_response"])
    """
    config = get_config()

    # Create default instances if not provided
    if llm_provider is None:
        logger.info("Creating default LLM provider")
        llm_provider = create_provider()

    if mongodb_client is None:
        logger.info("Creating default MongoDB client")
        mongodb_client = MongoDBClient()

    if query_executor is None:
        logger.info("Creating default query executor")
        query_executor = QueryExecutor(mongodb_client)

    if checkpointer is None:
        logger.info("Creating default checkpointer")
        checkpointer_type = config.checkpointer.type

        if checkpointer_type == "memory":
            checkpointer = MemorySaver()
        elif checkpointer_type == "sqlite":
            checkpointer = SqliteSaver.from_conn_string(config.checkpointer.sqlite_path)
        else:
            # Default to memory
            checkpointer = MemorySaver()

    # Create state graph
    logger.info("Building LangGraph workflow")
    workflow = StateGraph(AgentState)

    # Define nodes with partial application of dependencies
    def get_schema_wrapper(state: AgentState) -> AgentState:
        return get_schema_node(state, mongodb_client, collection)

    def generate_query_wrapper(state: AgentState) -> AgentState:
        return generate_query_node(state, llm_provider)

    def execute_query_wrapper(state: AgentState) -> AgentState:
        return execute_query_node(state, query_executor)

    def format_response_wrapper(state: AgentState) -> AgentState:
        return format_response_node(state, llm_provider)

    # Add nodes to graph
    workflow.add_node("get_schema", get_schema_wrapper)
    workflow.add_node("generate_query", generate_query_wrapper)
    workflow.add_node("execute_query", execute_query_wrapper)
    workflow.add_node("format_response", format_response_wrapper)
    workflow.add_node("error_handler", error_handler_node)

    # Define edges
    # Start with schema retrieval
    workflow.set_entry_point("get_schema")

    # Conditional edges for error handling
    workflow.add_conditional_edges(
        "get_schema",
        should_continue_after_schema,
        {
            "generate_query": "generate_query",
            "error_handler": "error_handler",
        },
    )

    workflow.add_conditional_edges(
        "generate_query",
        should_continue_after_generation,
        {
            "execute_query": "execute_query",
            "error_handler": "error_handler",
        },
    )

    workflow.add_conditional_edges(
        "execute_query",
        should_continue_after_execution,
        {
            "format_response": "format_response",
            "error_handler": "error_handler",
        },
    )

    # Terminal edges
    workflow.add_edge("format_response", END)
    workflow.add_edge("error_handler", END)

    # Compile graph with checkpointer
    logger.info("Compiling graph with checkpointer")
    compiled_graph = workflow.compile(checkpointer=checkpointer)

    logger.info("LangGraph workflow created successfully")

    return compiled_graph


class MongoDBAgent:
    """
    High-level MongoDB AI Agent interface.

    This class provides a simple, user-friendly interface to the
    LangGraph workflow. It handles state management, conversation
    history, and provides convenient methods for querying.

    Example usage:
        >>> agent = MongoDBAgent()
        >>> response = agent.query("What were the top movies in 2020?")
        >>> print(response)
        'Here are the top movies from 2020: ...'
        >>>
        >>> # With conversation history
        >>> agent = MongoDBAgent(thread_id="user123")
        >>> response = agent.query("Find action movies")
        >>> response = agent.query("Only from 2020")  # Maintains context
    """

    def __init__(
        self,
        llm_provider: Optional[BaseLLMProvider] = None,
        mongodb_client: Optional[MongoDBClient] = None,
        collection: str = "movies",
        thread_id: Optional[str] = None,
    ):
        """
        Initialize MongoDB AI Agent.

        Args:
            llm_provider: LLM provider instance (optional)
            mongodb_client: MongoDB client instance (optional)
            collection: Default collection name
            thread_id: Thread ID for conversation continuity (optional)
        """
        self.collection = collection
        self.thread_id = thread_id or "default"

        # Create dependencies
        self.llm_provider = llm_provider or create_provider()
        self.mongodb_client = mongodb_client or MongoDBClient()
        self.query_executor = QueryExecutor(self.mongodb_client)

        # Create graph
        self.graph = create_agent_graph(
            llm_provider=self.llm_provider,
            mongodb_client=self.mongodb_client,
            query_executor=self.query_executor,
            collection=self.collection,
        )

        logger.info(
            f"MongoDBAgent initialized",
            extra={
                "collection": self.collection,
                "thread_id": self.thread_id,
                "llm_provider": self.llm_provider.name,
            },
        )

    def query(self, question: str, thread_id: Optional[str] = None) -> str:
        """
        Ask a question in natural language and get a response.

        Args:
            question: Natural language question
            thread_id: Override default thread_id for this query

        Returns:
            Natural language response

        Example:
            >>> agent = MongoDBAgent()
            >>> response = agent.query("What were the top-rated movies in 2020?")
            >>> print(response)
        """
        # Use provided thread_id or default
        thread_id = thread_id or self.thread_id

        # Create initial state
        initial_state = create_initial_state(question)

        # Configure graph invocation
        config = {"configurable": {"thread_id": thread_id}}

        logger.info(
            f"Processing query",
            extra={
                "question": question[:100],
                "thread_id": thread_id,
            },
        )

        try:
            # Invoke graph
            result = self.graph.invoke(initial_state, config=config)

            # Extract and return final response
            final_response = result.get("final_response", "No response generated")

            logger.info(
                "Query processed successfully",
                extra={
                    "response_length": len(final_response),
                },
            )

            return final_response

        except Exception as e:
            logger.error(f"Query processing failed: {e}", exc_info=True)
            return (
                f"I encountered an error while processing your query: {str(e)}\n\n"
                f"Please try again or rephrase your question."
            )

    def stream_query(self, question: str, thread_id: Optional[str] = None):
        """
        Ask a question and stream the response.

        Args:
            question: Natural language question
            thread_id: Override default thread_id for this query

        Yields:
            Response chunks as they are generated

        Example:
            >>> agent = MongoDBAgent()
            >>> for chunk in agent.stream_query("Top movies in 2020"):
            ...     print(chunk, end="", flush=True)
        """
        # For now, invoke and yield complete response
        # TODO: Implement true streaming when LangGraph supports it better
        response = self.query(question, thread_id)
        yield response

    def get_conversation_history(self, thread_id: Optional[str] = None) -> list[Dict[str, str]]:
        """
        Get conversation history for a thread.

        Args:
            thread_id: Thread ID (uses default if None)

        Returns:
            List of message dictionaries

        Note: This requires checkpointer to be persistent (SQLite or Postgres)
        """
        thread_id = thread_id or self.thread_id

        # This is a placeholder - implementation depends on checkpointer type
        logger.warning("get_conversation_history not fully implemented yet")
        return []

    def close(self) -> None:
        """Close database connections and cleanup resources."""
        self.mongodb_client.close()
        logger.info("MongoDBAgent closed")

    def __enter__(self) -> "MongoDBAgent":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
