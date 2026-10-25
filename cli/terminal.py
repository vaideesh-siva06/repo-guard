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
from cli.theme import theme
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
import sys
import contextlib
import threading
import select
import os
import traceback

try:
    import termios
except ImportError:  # Windows
    termios = None

@contextlib.contextmanager
def watch_for_escape():
    """Hide keystrokes while streaming and yield an Event that is set when Esc is pressed."""
    stop = threading.Event()

    if termios is None or not sys.stdin.isatty():
        yield stop
        return

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] &= ~(termios.ECHO | termios.ICANON)
    done = threading.Event()

    def reader():
        while not done.is_set():
            if not select.select([fd], [], [], 0.05)[0]:
                continue
            ch = os.read(fd, 1)
            if ch == b"\x1b":
                if select.select([fd], [], [], 0.05)[0]:
                    os.read(fd, 32)   # arrow key / escape sequence: swallow it
                else:
                    stop.set()        # lone Esc

    t = threading.Thread(target=reader, daemon=True)
    try:
        termios.tcsetattr(fd, termios.TCSADRAIN, new)
        t.start()
        yield stop
    finally:
        done.set()
        t.join(timeout=0.5)
        termios.tcflush(fd, termios.TCIFLUSH)
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

@contextlib.contextmanager
def suppress_input():
    """Hide and discard keystrokes (arrow keys etc.) while the agent streams."""
    if termios is None or not sys.stdin.isatty():
        yield
        return

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] &= ~(termios.ECHO | termios.ICANON)  # index 3 = local flags
    try:
        termios.tcsetattr(fd, termios.TCSADRAIN, new)
        yield
    finally:
        termios.tcflush(fd, termios.TCIFLUSH)  # drop anything typed during streaming
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


console = Console(theme=theme, force_terminal=True)
width = int(console.width * 0.7)
llm = LLM(model_name="CODING")
session = PromptSession(
    history=InMemoryHistory()
)

def stream_response(user_input: str):
    response = "RepoGuard > "
    status = ""

    with watch_for_escape() as stop:
        events = llm.stream(user_input)

        try:
            with Live(
                Markdown(response + "▌"),
                console=console,
                refresh_per_second=8,
                screen=False,
                transient=False,  # Keep final live output
                vertical_overflow="ellipsis",
            ) as live:
                for event in events:
                    if stop.is_set():
                        break

                    if not isinstance(event, dict):
                        continue

                    if event["type"] == "message":
                        response += event["content"]
                        status = ""
                    elif event["type"] == "status":
                        status = f" *{event['content']}...*"

                    live.update(
                        Markdown(response + status + "▌"),
                        refresh=True,
                    )

                if stop.is_set():
                    response += "\n\n*[stopped]*"

                live.update(Markdown(response), refresh=True)
        except Exception:
            traceback.print_exc()
        finally:
            events.close()

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
            padding=(1, 3, 3, 0),
            expand=True,
        )
    )
    console.print(banner, justify="center")
    console.print("\n[dim]Type 'exit', 'quit', or 'Ctrl + C' to quit.[/dim]\n")

    while True:
        try:
            query = session.prompt("You > ")
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