import typer
from cli.terminal import run_chat
from config import set_project_root

app = typer.Typer()


@app.callback()
def initialize() -> None:
    """Initialize application state for the installed CLI entry point."""
    set_project_root()


@app.command()
def chat():
    run_chat()
