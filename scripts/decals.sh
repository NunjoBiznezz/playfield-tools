#!/bin/bash
# Black-only waterslide decal files (make_black_decal.py). Run from the game folder:
#   bash scripts/decals.sh                                 every piece in stencils/ with a black layer
#   bash scripts/decals.sh "stencils/UL queen lane.svg"    just one (options may follow, e.g. --margin 0.08)
# Standard library only, so it runs with any python3; uses the shared environment if it is there.
set -e
VENV="$HOME/.venvs/playfield-tools"
HERE="$(cd "$(dirname "$0")" && pwd)"
PY=python3; [ -x "$VENV/bin/python" ] && PY="$VENV/bin/python"
exec "$PY" "$HERE/make_black_decal.py" "$@"
