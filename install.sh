
#!/usr/bin/env bash
set -euo pipefail

REPO_URL="git+https://github.com/vaideeshsiva-06/repo-guard.git"

echo "================================"
echo "       RepoGuard Installer"
echo "================================"

# 1. Check Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 is required."
    echo "Install Python from https://www.python.org/downloads/"
    exit 1
fi

python3 - <<'PY'
import sys

if sys.version_info < (3, 11):
    print("Error: RepoGuard requires Python 3.11 or newer.")
    sys.exit(1)
PY

# 2. Check pip
if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "Error: pip is unavailable for this Python installation."
    exit 1
fi

# 3. Check Git
if ! command -v git >/dev/null 2>&1; then
    echo "Error: Git is required to install RepoGuard from GitHub."
    echo "Install Git from https://git-scm.com/downloads"
    exit 1
fi

# 4. Check Ollama
if command -v ollama >/dev/null 2>&1; then
    echo "Ollama is installed."

    if ollama list >/dev/null 2>&1; then
        echo "Ollama is responding."
    else
        echo "Warning: Ollama may not be running."
        echo "Start Ollama before using RepoGuard."
    fi
else
    echo "Warning: Ollama is not installed."
    echo "Install it from https://ollama.com/download"
fi

# 5. Install RepoGuard in an isolated environment
if ! command -v pipx >/dev/null 2>&1; then
    echo "Installing pipx..."

    python3 -m pip install --user pipx
    python3 -m pipx ensurepath

    # Make pipx available in this installer process when possible.
    USER_BIN="$(python3 -m site --user-base)/bin"
    export PATH="$USER_BIN:$HOME/.local/bin:$PATH"
fi

if command -v pipx >/dev/null 2>&1; then
    pipx install --force "$REPO_URL"
else
    echo "Error: pipx was installed but is not available in PATH."
    echo "Open a new terminal and run:"
    echo "  pipx install \"$REPO_URL\""
    exit 1
fi

echo ""
echo "================================"
echo "RepoGuard installation complete!"
echo "================================"
echo "Try: repoguard --help"
echo "Then navigate to a project and run: repoguard"
