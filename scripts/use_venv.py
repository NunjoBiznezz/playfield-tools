"""
use_venv.py - run a script in the shared Python environment (~/.venvs/playfield-tools)

Scripts that need numpy, shapely, OpenCV ... import this first. If the script was
started with the Mac's own python3, this restarts it with the environment's Python,
so "python3 scripts/make_all_stencils.py" works the same as "bash scripts/stencils.sh".
If the environment isn't there yet, it says how to make it.
"""
import os, sys

VENV = os.path.expanduser("~/.venvs/playfield-tools")
PY = os.path.join(VENV, "bin", "python")

if os.path.realpath(sys.prefix) != os.path.realpath(VENV):
    if os.path.exists(PY):
        os.execv(PY, [PY] + sys.argv)
    sys.exit("The playfield Python environment isn't set up yet. Run this once (needs internet):\n"
             "    bash scripts/setup.sh")
