from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

current_date = datetime.now(
    ZoneInfo("America/Chicago")
).strftime("%A, %B %d, %Y")

coding_prompt = Path("./prompts/coding_prompt.md").read_text()
design_prompt = Path("./prompts/design_prompt.md").read_text()
general_prompt = Path("./prompts/general_prompt.md").read_text()

system_prompts = {
    
"CODING": coding_prompt,

"DESIGN": design_prompt,

"GENERAL": general_prompt

}