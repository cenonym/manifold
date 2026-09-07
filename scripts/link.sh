#!/usr/bin/env bash
set -euo pipefail
COMFY="${COMFY:-$HOME/ComfyUI-Installs/ComfyUI/ComfyUI}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
ln -sfn "$REPO" "$COMFY/custom_nodes/manifold"
"$COMFY/.venv/bin/python" -m pip install -q -r "$REPO/requirements.txt"
[ -f "$REPO/manifold.toml" ] || cp "$REPO/manifold.toml.example" "$REPO/manifold.toml"
echo "linked $REPO -> $COMFY/custom_nodes/manifold"
