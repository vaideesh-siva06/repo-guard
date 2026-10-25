#!/usr/bin/env bash
set -euo pipefail

BRANCH="${REPOGUARD_BRANCH:-development}"
REPO_URL="git+https://github.com/vaideesh-siva06/repo-guard.git@${BRANCH}"
MIN_PY="3.13"   # keep in sync with requires-python in pyproject.toml

echo "================================"
echo "       RepoGuard Installer"
echo "================================"

# 1. Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 is required."
    echo "Install Python from https://www.python.org/downloads/"
    exit 1
fi

PY="$(command -v python3)"

if ! "$PY" -c "import sys; sys.exit(0 if sys.version_info >= (${MIN_PY/./,}) else 1)"; then
    echo "Error: RepoGuard requires Python ${MIN_PY} or newer."
    "$PY" --version
    exit 1
fi

# 2. Git
if ! command -v git >/dev/null 2>&1; then
    echo "Error: Git is required."
    echo "Install Git from https://git-scm.com/downloads"
    exit 1
fi

# 3. Ollama (warn only)
if command -v ollama >/dev/null 2>&1; then
    if ollama list >/dev/null 2>&1; then
        echo "Ollama is installed and responding."
    else
        echo "Warning: Ollama is installed but not running. Start it before using RepoGuard."
    fi
else
    echo "Warning: Ollama is not installed. Get it at https://ollama.com/download"
fi

# 4. pipx
if ! command -v pipx >/dev/null 2>&1; then
    echo "Installing pipx..."
    if command -v brew >/dev/null 2>&1; then
        brew install pipx
    elif "$PY" -m pip --version >/dev/null 2>&1; then
        "$PY" -m pip install --user pipx
    else
        echo "Error: could not install pipx (no brew, no pip)."
        exit 1
    fi
    USER_BIN="$("$PY" -m site --user-base)/bin"
    export PATH="$USER_BIN:$HOME/.local/bin:$PATH"
fi

if ! command -v pipx >/dev/null 2>&1; then
    echo "Error: pipx was installed but is not on PATH."
    echo "Open a new terminal and run:"
    echo "  pipx install --python python3 \"$REPO_URL\""
    exit 1
fi

# 5. Install RepoGuard
echo "Installing RepoGuard (first install can take a few minutes; it pulls in torch)..."
pipx install --force --python "$PY" "$REPO_URL"
pipx ensurepath >/dev/null 2>&1 || true

echo ""
echo "================================"
echo "RepoGuard installation complete!"
echo "================================"
echo "Open a NEW terminal, then run: repoguard --help"
echo "Then go to a project and run: repoguard"