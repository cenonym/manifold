#!/usr/bin/env bash
set -euo pipefail
PY="$HOME/ComfyUI-Installs/ComfyUI/ComfyUI/.venv/bin/python"
cd "$(dirname "$0")/.."
"$PY" -m pytest "$@"
