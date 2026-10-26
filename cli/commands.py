import typer
from cli.terminal import main
from config import set_project_root
import asyncio

app = typer.Typer()


@app.callback()
def initialize() -> None:
    """Initialize application state for the installed CLI entry point."""
    set_project_root()


@app.command()
def chat():
    asyncio.run(main())
