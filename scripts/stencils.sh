#!/bin/bash
# Make stencils. Uses the shared Python environment (~/.venvs/playfield-tools);
# the first run sets it up with setup.sh (needs internet once), after that it works offline.
# Runs make_all_stencils.py, which looks at each source SVG and calls the right generator.
#   bash scripts/stencils.sh                               every source SVG in stencils/
#   bash scripts/stencils.sh "stencils/UL slingshot.svg"   just one (options may follow)
#   bash scripts/stencils.sh --dry-run                     show what would be made
set -e
VENV="$HOME/.venvs/playfield-tools"
HERE="$(cd "$(dirname "$0")" && pwd)"
if [ ! -x "$VENV/bin/python" ]; then
  echo "Setting up $VENV (one time)..."
  bash "$HERE/setup.sh"
fi
exec "$VENV/bin/python" "$HERE/make_all_stencils.py" "$@"
