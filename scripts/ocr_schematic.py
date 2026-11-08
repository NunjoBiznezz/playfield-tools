#!/usr/bin/env python3
"""
ocr_schematic.py - make a scanned schematic PDF searchable, including sideways labels.

The code now lives in the schematic-ocr package in ../ocr (so it can be shared on its
own; see ocr/README.md). This runs that same code in the shared playfield environment,
so the command is unchanged:

    python3 scripts/ocr_schematic.py input.pdf output.pdf [--dpi 300] ...

Run with --help for all the options. Needs: brew install tesseract poppler
"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import use_venv  # shared Python environment
import os
import sys

# realpath: game folders reach this through a "scripts" link, and ../ocr is beside the real one
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "ocr", "src"))
from schematic_ocr.cli import main

if __name__ == "__main__":
    main()
