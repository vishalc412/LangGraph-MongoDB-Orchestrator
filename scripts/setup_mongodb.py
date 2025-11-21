#!/usr/bin/env python3
"""
MongoDB setup script for MongoDB AI Agent.

This script sets up a MongoDB database with sample movie data
for testing and demonstration purposes.

Usage:
    python scripts/setup_mongodb.py
    python scripts/setup_mongodb.py --uri mongodb://localhost:27017
    python scripts/setup_mongodb.py --database test_db --collection test_movies

Author: AI Agent Development Team
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

import typer
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

app = typer.Typer()
console = Console()


def load_sample_data(file_path: str) -> List[Dict[str, Any]]:
    """Load sample movie data from JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] File not found: {file_path}")
        raise typer.Exit(1)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON in file: {e}")
        raise typer.Exit(1)


@app.command()
def setup(
    uri: str = typer.Option(
        "mongodb://localhost:27017",
        "--uri",
        "-u",
        help="MongoDB connection URI",
    ),
    database: str = typer.Option(
        "sample_mflix",
        "--database",
        "-d",
        help="Database name",
    ),
    collection: str = typer.Option(
        "movies",
        "--collection",
        "-c",
        help="Collection name",
    ),
    data_file: str = typer.Option(
        "data/sample_movies.json",
        "--data-file",
        "-f",
        help="Path to sample data JSON file",
    ),
    drop_existing: bool = typer.Option(
        False,
        "--drop-existing",
        help="Drop existing collection before inserting data",
    ),
) -> None:
    """
    Set up MongoDB with sample movie data.

    This command:
    1. Connects to MongoDB
    2. Creates database and collection if they don't exist
    3. Loads sample movie data
    4. Creates indexes for common queries
    """
    console.print("\n[bold cyan]MongoDB AI Agent - Database Setup[/bold cyan]\n")

    # Connect to MongoDB
    console.print(f"[cyan]Connecting to MongoDB...[/cyan]")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        console.print(f"[green]✓[/green] Connected successfully to {uri}\n")
    except ConnectionFailure as e:
        console.print(f"[red]✗[/red] Connection failed: {e}")
        console.print("\n[yellow]Make sure MongoDB is running:[/yellow]")
        console.print("  - Local: brew services start mongodb-community")
        console.print("  - Docker: docker run -d -p 27017:27017 mongo:latest")
        raise typer.Exit(1)

    # Get database and collection
    db = client[database]
    coll = db[collection]

    # Drop existing collection if requested
    if drop_existing:
        console.print(f"[yellow]Dropping existing collection '{collection}'...[/yellow]")
        coll.drop()
        console.print(f"[green]✓[/green] Collection dropped\n")

    # Check if collection already has data
    existing_count = coll.count_documents({})
    if existing_count > 0:
        console.print(
            f"[yellow]Warning:[/yellow] Collection already contains {existing_count} documents"
        )
        if not typer.confirm("Do you want to add more data?"):
            console.print("\n[yellow]Setup cancelled[/yellow]")
            raise typer.Exit(0)
        console.print()

    # Load sample data
    console.print(f"[cyan]Loading sample data from {data_file}...[/cyan]")
    sample_data = load_sample_data(data_file)
    console.print(f"[green]✓[/green] Loaded {len(sample_data)} movies\n")

    # Insert data
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Inserting data into MongoDB...", total=None)

        try:
            result = coll.insert_many(sample_data)
            progress.update(task, completed=True)
            console.print(
                f"\n[green]✓[/green] Successfully inserted {len(result.inserted_ids)} documents\n"
            )
        except Exception as e:
            console.print(f"\n[red]✗[/red] Insert failed: {e}")
            raise typer.Exit(1)

    # Create indexes
    console.print("[cyan]Creating indexes...[/cyan]")
    try:
        # Index on year for common queries
        coll.create_index("year")
        console.print("  [green]✓[/green] Created index on 'year'")

        # Index on genres for filtering
        coll.create_index("genres")
        console.print("  [green]✓[/green] Created index on 'genres'")

        # Index on rating for sorting
        coll.create_index([("imdb.rating", -1)])
        console.print("  [green]✓[/green] Created index on 'imdb.rating'")

        # Text index for title search
        coll.create_index([("title", "text"), ("plot", "text")])
        console.print("  [green]✓[/green] Created text index on 'title' and 'plot'")

    except Exception as e:
        console.print(f"  [yellow]Warning:[/yellow] Index creation failed: {e}")

    # Summary
    total_count = coll.count_documents({})
    console.print("\n[bold green]Setup Complete![/bold green]\n")
    console.print(f"Database: [cyan]{database}[/cyan]")
    console.print(f"Collection: [cyan]{collection}[/cyan]")
    console.print(f"Total documents: [cyan]{total_count}[/cyan]")
    console.print()

    # Show sample query
    console.print("[bold]Test the setup with this query:[/bold]")
    console.print(
        f'  mongodb-agent query "What are the highest rated movies from 2020?"'
    )
    console.print()

    # Close connection
    client.close()


if __name__ == "__main__":
    app()
