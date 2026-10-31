#!/bin/bash
# One-time (or repair) setup of the Python environment for all the playfield scripts.
# It lives in ~/.venvs/playfield-tools, outside iCloud, and is shared by every game.
# Run from a game folder:   bash scripts/setup.sh     (needs internet once)
# Packages go in one at a time, so if one won't install (e.g. not built yet for a
# brand-new Python) the others - and the stencil scripts - still work.
set -e
cd "$(dirname "$0")"
VENV="$HOME/.venvs/playfield-tools"
rm -rf "$VENV"
python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip
failed=""
for pkg in $(grep -v '^\s*#' requirements.txt); do
  echo "installing $pkg ..."
  "$VENV/bin/pip" install --quiet "$pkg" || failed="$failed $pkg"
done
if [ -n "$failed" ]; then
  echo
  echo "These didn't install:$failed"
  echo "(Python $("$VENV/bin/python" -V 2>&1 | cut -d' ' -f2)). The stencil scripts only need numpy + shapely."
  exit 1
fi
echo "Done. The scripts use it by themselves - no need to activate it."
