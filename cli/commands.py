import typer
from cli.terminal import run_chat

app = typer.Typer()

@app.command()
def chat():
    run_chat()