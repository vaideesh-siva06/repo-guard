from cli.commands import app
from config import set_project_root

if __name__ == "__main__":
    root = set_project_root()
    app()
