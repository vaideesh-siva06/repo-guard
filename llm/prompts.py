from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

from importlib.resources import files


def load_prompt(filename: str) -> str:
    return (
        files("llm")
        .joinpath("prompt_templates", filename)
        .read_text(encoding="utf-8")
        .replace("{current_date}", current_date)
    )

current_date = datetime.now(
    ZoneInfo("America/Chicago")
).strftime("%A, %B %d, %Y")

system_prompts = {
    "CODING": load_prompt("coding_prompt.md"),
    "DESIGN": load_prompt("design_prompt.md"),
    "GENERAL": load_prompt("general_prompt.md"),
    "ORCHESTRATOR": load_prompt("orchestrator_prompt.md"),
}
