from pathlib import Path

_project_root: Path | None = None

def set_project_root(path: str | Path | None = None) -> Path:
    global _project_root
    _project_root = Path(path or Path.cwd()).expanduser().resolve()
    return _project_root

def get_project_root() -> Path:
    if _project_root is None:
        raise RuntimeError("Project root not set. Call set_project_root() at startup.")
    return _project_root