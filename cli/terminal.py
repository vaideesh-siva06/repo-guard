from rich.console import Console
from rich.panel import Panel
from typer import Typer
from rich.text import Text
from rich.table import Table
from pathlib import Path

console = Console()

def run_chat():
    """Chat interface for local coding agent"""

    model = "qwen3:8b"  # Replace with your configured Ollama model
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
    banner.append("Guard\n", style="bold white")
    banner.append("\nYour local AI coding assistant", style="italic")

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
    console.print("\n[dim]Type 'exit' to quit.[/dim]\n")

    while True:
        try:
            user_input = console.input("[white]You > [/white]")
            console.print()

            if user_input.strip().lower() in {"exit", "quit", "q"}:
                console.print("[white]Goodbye![/white]")
                break

            if not user_input.strip():
                continue

            # Pass the input to agent
            response = f"You said {user_input}"
            console.print(f"[bold white]RepoGuard >[/bold white] {response}")
            console.print()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[white]Goodbye![/white]")
            break