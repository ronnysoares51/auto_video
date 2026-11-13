#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
if [ ! -x "$PYTHON_BIN" ]; then
  echo "Ambiente virtual ausente. Execute: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi
cd "$PROJECT_DIR"
# Publication remains off unless explicitly enabled in the environment.
export ENABLE_TIKTOK_PUBLISH="${ENABLE_TIKTOK_PUBLISH:-false}"
"$PYTHON_BIN" "$PROJECT_DIR/main.py" >> "$LOG_DIR/cron.log" 2>&1
