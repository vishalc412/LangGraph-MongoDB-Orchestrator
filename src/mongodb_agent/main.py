"""
Main application and CLI interface for MongoDB AI Agent.

This module provides the command-line interface for interacting with
the MongoDB AI Agent. Built with Typer for CLI and Rich for beautiful output.

Usage:
    # Interactive mode
    $ python -m mongodb_agent.main chat

    # Single query
    $ python -m mongodb_agent.main query "What were the top movies in 2020?"

    # With different provider
    $ python -m mongodb_agent.main chat --provider ollama

Author: AI Agent Development Team
"""

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from mongodb_agent.agents.graph import MongoDBAgent
from mongodb_agent.config.settings import get_config
from mongodb_agent.utils.logger import get_logger, setup_logging

# Create Typer app
app = typer.Typer(
    name="mongodb-agent",
    help="MongoDB AI Agent - Natural language interface for MongoDB queries",
    add_completion=False,
)

# Rich console for beautiful output
console = Console()

# Logger
logger = get_logger(__name__)


@app.command()
def chat(
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="LLM provider to use (openai or ollama)",
    ),
    collection: str = typer.Option(
        "movies",
        "--collection",
        "-c",
        help="MongoDB collection to query",
    ),
    thread_id: Optional[str] = typer.Option(
        None,
        "--thread-id",
        "-t",
        help="Thread ID for conversation continuity",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug logging",
    ),
) -> None:
    """
    Start interactive chat session with the MongoDB AI Agent.

    Example:
        $ mongodb-agent chat
        $ mongodb-agent chat --provider ollama --collection users
    """
    # Setup logging
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(log_level=log_level, log_format="text")

    # Load config
    config = get_config()

    # Override provider if specified
    if provider:
        config.default_llm_provider = provider

    # Display welcome message
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]MongoDB AI Agent[/bold cyan]\n\n"
            f"Provider: [yellow]{config.default_llm_provider}[/yellow]\n"
            f"Collection: [yellow]{collection}[/yellow]\n"
            f"Thread ID: [yellow]{thread_id or 'default'}[/yellow]\n\n"
            "Ask questions in natural language about your MongoDB data.\n"
            "Type 'exit' or 'quit' to end the session.",
            title="🤖 Welcome",
            border_style="cyan",
        )
    )
    console.print()

    # Initialize agent
    try:
        with console.status("[bold yellow]Initializing agent...", spinner="dots"):
            agent = MongoDBAgent(collection=collection, thread_id=thread_id)

        console.print("[green]✓[/green] Agent initialized successfully!\n")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to initialize agent: {e}")
        logger.error(f"Agent initialization failed: {e}", exc_info=True)
        raise typer.Exit(1)

    # Chat loop
    try:
        while True:
            # Get user input
            try:
                question = Prompt.ask("\n[bold blue]You[/bold blue]")
            except (KeyboardInterrupt, EOFError):
                console.print("\n\n[yellow]Goodbye![/yellow]")
                break

            # Check for exit commands
            if question.lower() in ["exit", "quit", "bye"]:
                console.print("\n[yellow]Goodbye![/yellow]")
                break

            # Skip empty input
            if not question.strip():
                continue

            # Process query
            try:
                with console.status(
                    "[bold yellow]Thinking...", spinner="dots"
                ):
                    response = agent.query(question)

                # Display response
                console.print()
                console.print(
                    Panel(
                        Markdown(response),
                        title="🤖 Assistant",
                        border_style="green",
                    )
                )

            except KeyboardInterrupt:
                console.print("\n[yellow]Query interrupted[/yellow]")
                continue

            except Exception as e:
                console.print(f"\n[red]Error:[/red] {e}")
                logger.error(f"Query processing error: {e}", exc_info=True)

    except Exception as e:
        console.print(f"\n[red]Unexpected error:[/red] {e}")
        logger.error(f"Chat loop error: {e}", exc_info=True)
        raise typer.Exit(1)

    finally:
        # Cleanup
        try:
            agent.close()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")


@app.command()
def query(
    question: str = typer.Argument(..., help="Natural language question"),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="LLM provider to use (openai or ollama)",
    ),
    collection: str = typer.Option(
        "movies",
        "--collection",
        "-c",
        help="MongoDB collection to query",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug logging",
    ),
) -> None:
    """
    Execute a single query and exit.

    Example:
        $ mongodb-agent query "What were the top movies in 2020?"
        $ mongodb-agent query "Average rating by genre" --provider ollama
    """
    # Setup logging
    log_level = "DEBUG" if debug else "WARNING"  # Less verbose for single queries
    setup_logging(log_level=log_level, log_format="text")

    # Load config
    config = get_config()

    # Override provider if specified
    if provider:
        config.default_llm_provider = provider

    # Initialize agent
    try:
        agent = MongoDBAgent(collection=collection)

        # Process query
        response = agent.query(question)

        # Display response
        console.print()
        console.print(Markdown(response))
        console.print()

        # Cleanup
        agent.close()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}", file=sys.stderr)
        logger.error(f"Query execution failed: {e}", exc_info=True)
        raise typer.Exit(1)


@app.command()
def test_connection(
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug logging",
    ),
) -> None:
    """
    Test MongoDB connection and LLM provider availability.

    This command verifies that all required services are accessible.

    Example:
        $ mongodb-agent test-connection
    """
    # Setup logging
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(log_level=log_level, log_format="text")

    # Load config
    config = get_config()

    console.print("\n[bold]Testing MongoDB AI Agent Configuration[/bold]\n")

    # Test MongoDB connection
    console.print("[cyan]Testing MongoDB connection...[/cyan]")
    try:
        from mongodb_agent.database.mongodb_client import MongoDBClient

        with MongoDBClient() as client:
            if client.ping():
                console.print("[green]✓[/green] MongoDB connection successful")
                collections = client.list_collections()
                console.print(f"  Available collections: {', '.join(collections)}")
            else:
                console.print("[red]✗[/red] MongoDB ping failed")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]✗[/red] MongoDB connection failed: {e}")
        raise typer.Exit(1)

    # Test LLM provider
    console.print(f"\n[cyan]Testing LLM provider ({config.default_llm_provider})...[/cyan]")
    try:
        from mongodb_agent.providers import create_provider

        provider = create_provider()
        console.print(f"[green]✓[/green] LLM provider '{provider.name}' initialized")

        # Test generation
        test_response = provider.generate(
            [{"role": "user", "content": "Say 'OK' if you can read this"}],
            max_tokens=10,
        )
        console.print(f"[green]✓[/green] Test generation successful")
        console.print(f"  Response: {test_response[:50]}...")

    except Exception as e:
        console.print(f"[red]✗[/red] LLM provider test failed: {e}")
        raise typer.Exit(1)

    console.print("\n[bold green]All tests passed![/bold green]\n")


@app.command()
def info() -> None:
    """
    Display system information and configuration.

    Example:
        $ mongodb-agent info
    """
    config = get_config()

    info_text = f"""
# MongoDB AI Agent - System Information

## Configuration
- **Environment**: {config.environment}
- **Log Level**: {config.log_level}
- **Debug Mode**: {config.debug}

## LLM Provider
- **Default Provider**: {config.default_llm_provider}
- **OpenAI Model**: {config.openai.model}
- **Ollama Model**: {config.ollama.model}

## MongoDB
- **Database**: {config.mongodb.database}
- **Collection**: {config.mongodb.collection}
- **Connection Pool**: {config.mongodb.max_pool_size}

## Checkpointer
- **Type**: {config.checkpointer.type}
- **SQLite Path**: {config.checkpointer.sqlite_path if config.checkpointer.type == 'sqlite' else 'N/A'}

## Agent Settings
- **Max Conversation Turns**: {config.max_conversation_turns}
- **Streaming Enabled**: {config.enable_streaming}
"""

    console.print(Markdown(info_text))


def main() -> None:
    """Main entry point for the application."""
    app()


if __name__ == "__main__":
    main()
