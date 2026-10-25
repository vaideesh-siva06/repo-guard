#!/usr/bin/env bash
set -euo pipefail

BRANCH="${REPOGUARD_BRANCH:-development}"
REPO_URL="git+https://github.com/vaideesh-siva06/repo-guard.git@${BRANCH}"

echo "Installing RepoGuard..."

if ! command -v uv >/dev/null 2>&1; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh </dev/null
    export PATH="$HOME/.local/bin:$PATH"
fi

uv tool install --force --python 3.13 "$REPO_URL" </dev/null
uv tool update-shell >/dev/null 2>&1 || true

if ! command -v ollama >/dev/null 2>&1; then
    echo "Note: Ollama is not installed. Get it at https://ollama.com/download"
fi

echo "Done. Open a NEW terminal and run: repoguard --help"