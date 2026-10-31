#!/bin/bash
# One-time (or repair) setup of the Python environment for the image / OCR scripts.
# It lives in ~/.venvs/playfield-tools, outside iCloud, and is shared by every game.
# (The stencil scripts don't need this: scripts/stencils.sh makes its own small one.)
set -e
cd "$(dirname "$0")"
VENV="$HOME/.venvs/playfield-tools"
rm -rf "$VENV"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install -r requirements.txt
echo "Done. Activate with: source $VENV/bin/activate"
