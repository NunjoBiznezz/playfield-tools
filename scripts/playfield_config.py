#!/usr/bin/env python3
"""
playfield_config.py - the per-game settings for the shared playfield scripts
============================================================================

Every game folder (Lady Luck, Tropic Isle ...) has a small "playfield.json" next to
its stencils/ folder. The shared scripts read it from the folder you run them in, so
the same scripts work for any game. Anything left out of the file uses the default
below; a game folder with no playfield.json at all uses the defaults, named after
the folder.

    {
      "name": "Lady Luck",                 game name (used in file names and titles)
      "board_w_in": 20.3125,               wood size, inches
      "board_h_in": 42.0,
      "art_centre_x_in": 9.20,             artwork centre line (default: middle of the board)
      "master_svg": "Lady Luck playfield.svg",        default "<name> playfield.svg"
      "hole_list": "Lady Luck hole list.csv",         default "<name> hole list.csv"
      "placements": "playfield placements.csv",
      "controls": "playfield controls.csv",
      "underlay": "images/playfield aligned 150ppi.jpg",
      "colour_order": ["yellow", "green", "teal", "blue", "red", "black"],
      "not_sources": {"<file pattern>": "why it is not a stencil source"},
      "game_steps": [                      game-only scripts make_all_stencils.py also runs
        {"name": "LC green rings",
         "script": "game_scripts/make_green_rings.py",   must have a main()
         "source": "LC green rings stencil pieces.svg",  file in stencils/ it makes (skipped as a source;
                                                         naming it on the command line runs the step)
         "needs": "Lady Luck playfield.svg"}             file that must exist first (optional)
      ]
    }
"""
import json, os

FILE = "playfield.json"


def load(folder=None):
    folder = folder or os.getcwd()
    path = os.path.join(folder, FILE)
    cfg = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    name = cfg.get("name") or os.path.basename(os.path.abspath(folder))
    out = {
        "name": name,
        "board_w_in": 20.25,
        "board_h_in": 42.0,
        "art_centre_x_in": None,
        "master_svg": f"{name} playfield.svg",
        "hole_list": f"{name} hole list.csv",
        "placements": "playfield placements.csv",
        "controls": "playfield controls.csv",
        "underlay": "images/playfield aligned 150ppi.jpg",
        "colour_order": ["yellow", "green", "teal", "blue", "red", "black"],
        "not_sources": {},
        "game_steps": [],
    }
    out.update({k: v for k, v in cfg.items() if v is not None})
    if out["art_centre_x_in"] is None:
        out["art_centre_x_in"] = out["board_w_in"] / 2
    out["found"] = os.path.exists(path)
    return out


if __name__ == "__main__":
    c = load()
    print(("" if c["found"] else "(no playfield.json here - defaults)\n") + json.dumps(c, indent=2))
