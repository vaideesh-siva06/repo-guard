from rich.console import Console, Group
from rich.panel import Panel
from typer import Typer
from rich.text import Text
from rich.table import Table
from pathlib import Path
from llm.client import LLM
from rich.padding import Padding
from rich.live import Live
from rich.markdown import Markdown
from rich.syntax import Syntax
import pyperclip
import re

console = Console()
width = int(console.width * 0.7)
llm = LLM(model_name="CODING")
    

def stream_response(user_input: str):
    response = "RepoGuard > "
    status = ""

    with Live(
        Markdown(response),
        console=console,
        refresh_per_second=8,
        screen=False,
        transient=False,
    ) as live:
        live.update(Markdown(response + "▌"), refresh=True)

        for event in llm.stream(user_input):
            if not isinstance(event, dict):
                continue

            if event["type"] == "message":
                response += event["content"]
                status = ""

            elif event["type"] == "status":
                status = f" *{event['content']}...*"

            # elif event["type"] == "tool_result":
            #     status = f" *Finished: {event['tool']}*"

            display = response + status
            live.update(Markdown(display), refresh=True)

        live.update(Markdown(response), refresh=True)

def run_chat():
    """Chat interface for local coding agent"""

    model = "qwen3:8b" # Replace with your configured Ollama model
    backend = "Ollama (local)"
    project_dir = str(Path.cwd())

    info = Table.grid(padding=(0, 2))
    info.add_column(style="bold cyan", justify="right")
    info.add_column(style="white")

    info.add_row("Model", model)
    info.add_row("Backend", backend)
    info.add_row("Workspace", project_dir)
    info.add_row("Mode", "Interactive coding agent")
    info.add_row("Commands", "exit / quit to leave")

    banner = Text()
    banner.append("\nRepo", style="bold white")
    banner.append("Guard - v1.0.0\n", style="bold white")
    banner.append("\nYour local AI coding assistant", style="italic")
    banner.append("\n┌─┬─┐\n", style="white")
    banner.append("└", style="white")
    banner.append("●", style="white")
    banner.append("─", style="white")
    banner.append("●", style="white")
    banner.append("┘", style="white")

    console.print()
    console.print(
        Panel(
            info,
            title="[bold white]RepoGuard[/bold white]\n",
            subtitle="[dim]Local-first coding agent[/dim]",
            border_style="green",
            padding=(1, 3),
            expand=True,
        )
    )
    console.print(banner, justify="center")
    console.print("\n[dim]Type 'exit', 'quit', or 'Ctrl + C' to quit.[/dim]\n")

    while True:
        try:
            query = console.input("[white]You > [/white]")
            console.print()

            if query.strip().lower() in {"exit", "quit"}:
                console.print("[white]Goodbye![/white]")
                break

            if query.strip().lower() in {"clear", "cls"}:
                console.clear()
                console.print("\n")
                continue

            if not query.strip():
                continue

            if query.strip().lower() == "help":
                table = Table(title="RepoGuard Commands", border_style="white")
                table.add_column("Command", style="bold white")
                table.add_column("Description")

                table.add_row("help", "Show available commands")
                table.add_row("exit", "Exit RepoGuard")
                table.add_row("clear", "Clear the terminal")

                console.print(table)
                continue
            # Pass the input to agent
            # response = f"You said {query}"

            stream_response(query)
            print()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[white]Goodbye![/white]")
            break