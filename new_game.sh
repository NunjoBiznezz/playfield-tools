#!/bin/bash
# Make a new game folder that uses these shared scripts.
#   bash ~/Documents/Pinball/playfield-tools/new_game.sh ~/Documents/Pinball/Williams/"Tropic Isle"
# Creates stencils/ images/ game_scripts/, a starter playfield.json (edit the board size!),
# the two csv files, a .gitignore, and "scripts" -> a link to playfield-tools/scripts,
# so "bash scripts/stencils.sh" works there just like in Lady Luck.
set -e
TOOLS="$(cd "$(dirname "$0")" && pwd)"
[ -n "$1" ] || { echo "usage: bash new_game.sh <game folder>"; exit 1; }
mkdir -p "$1"; GAME="$(cd "$1" && pwd)"; NAME="$(basename "$GAME")"
cd "$GAME"
mkdir -p stencils images game_scripts
if [ ! -e scripts ]; then
  ln -s "$(python3 -c 'import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))' "$TOOLS/scripts" "$GAME")" scripts
fi
[ -e playfield.json ] || cat > playfield.json <<JSON
{
  "name": "$NAME",
  "board_w_in": 20.25,
  "board_h_in": 42.0,
  "not_sources": {},
  "game_steps": []
}
JSON
[ -e "playfield placements.csv" ] || echo "file,origin_x_in,origin_y_in,rotation_deg,include,notes" > "playfield placements.csv"
[ -e "playfield controls.csv" ] || echo "name,x_in,y_in" > "playfield controls.csv"
[ -e .gitignore ] || cp "$TOOLS/.gitignore" .gitignore
echo "Made $GAME"
echo "Next: measure the wood and set board_w_in / board_h_in in playfield.json."
