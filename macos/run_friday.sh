#!/bin/zsh
# Development runner used by the login-item installer. The packaged .app is
# preferred because it stays out of the Dock via LSUIElement.

set -eu
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON="$PROJECT_ROOT/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python3)"
fi

cd "$PROJECT_ROOT"
exec "$PYTHON" mac_app.py
