# playfield-tools

Shared scripts for making pinball playfield stencils (Silhouette Cameo / Inkscape),
split out of the Williams Lady Luck restoration so every game can use them.

## Layout

```
Pinball/
  playfield-tools/          this repo - scripts, fonts, setup
  Williams/Lady Luck/       a game folder
    playfield.json          that game's settings (name, board size, game-only steps)
    scripts -> ../../playfield-tools/scripts     link, so the commands below just work
    stencils/  images/  game_scripts/  _generated/
```

## Starting a new game

```bash
bash ~/Documents/Pinball/playfield-tools/new_game.sh ~/Documents/Pinball/Williams/"Tropic Isle"
```

Then measure the wood and set `board_w_in` / `board_h_in` in its `playfield.json`.
`python3 scripts/playfield_config.py` (run in the game folder) shows the settings in use.

## Everyday commands (run in the game folder)

```bash
bash scripts/stencils.sh                               every source SVG in stencils/
bash scripts/stencils.sh "stencils/UL pop bumper.svg"  just one
bash scripts/stencils.sh --dry-run                     show what would be made
python3 scripts/build_playfield.py                     assemble "<game> playfield.svg"
```

Game-only scripts go in that game's `game_scripts/` folder and are listed under
`game_steps` in its `playfield.json` (see `scripts/playfield_config.py`), so they run
with everything else without being part of this shared repo.

## What each script does

Every script starts with a description of what it does and how to run it, and each
function has a one-line note on what it's for. For the stencil workflow, see
`scripts/README-stencils.md`. In brief:

**Commands you run (from the game folder)**

| Script | What it does |
|---|---|
| `stencils.sh` → `make_all_stencils.py` | Makes every stencil a source SVG needs (or all of `stencils/`), by calling the generators below |
| `make_stencils.py` | Bordered pieces (a `centerline` layer): area stencil, area mask, border stencil |
| `make_layer_stencils.py` | Flat-colour art: one stencil per paint layer + area mask, shared registration marks, trim lines |
| `decals.sh` → `make_black_decal.py` | Black-only waterslide decal file for each piece with a black layer |
| `build_playfield.py` | Puts every piece together into `<game> playfield.svg`, using `playfield placements.csv` |
| `playfield_config.py` | Reads the game's `playfield.json`; run on its own to show the settings in use |

**Photos and images**

| Script | What it does |
|---|---|
| `stencil_rectify.py` | Straightens photos taken over graph paper and sets true scale (finds the grid itself, or you click 4 points) |
| `crop_paper.py` | Crops the graph paper off rectified photos, keeping the artwork |
| `rectify_cleanup.py` | Afterwards: `NAME_rectified.png` (or `_cropped`) replaces `NAME.png`; removes the `_check.png` files |
| `rescale_images.py` | Fixes a uniform scale error (e.g. grid paper printed slightly too big) |
| `png2stencil.py` | Flat-colour PNG → one traced SVG per colour |
| `extract_b2s_images.py` | Pulls the backglass/DMD images out of a Visual Pinball `.directb2s` file |
| `ocr_schematic.py` | Makes a scanned schematic PDF searchable, including sideways labels |

**Helper libraries** (imported by other scripts or used in a working session; not run on their own)

| Script | What it does |
|---|---|
| `use_venv.py` | Restarts a script in the shared Python environment |
| `curvefit.py` | Fits traced outlines with a few smooth Bezier curves, keeping sharp corners |
| `lineart.py` | Rebuilds painted line art (from a label image) as constant-width lines and colour areas |
| `arcpath.py` | Writes shapely shapes as SVG paths with true arcs (needs a game's `lanes/build.py`) |
| `twostar_model.py` | Lady Luck "two overlapping stars" art built from measurements |

**Old, kept for reference** (won't run as-is: they have paths from an old cloud session) -
`multiorient_ocr.py`, `ocr_one_rotation.py`, `build_final.py`: the first try at schematic
OCR, replaced by `ocr_schematic.py`.

**Setup:** `setup.sh` (makes the shared environment), `update.sh` (updates it after you
change `requirements.txt`), `layer_stencils.sh` (old name for `stencils.sh`).
`new_game.sh` (in the repo root) starts a new game folder.

## Python

All the scripts share one environment, `~/.venvs/playfield-tools`, kept outside iCloud
on purpose (iCloud doesn't sync Python environments well). Set it up once, from any
game folder (needs internet):

```bash
bash scripts/setup.sh
```

After that the scripts find it by themselves - `python3 scripts/make_all_stencils.py`
works without activating anything, and `stencils.sh` runs setup for you the first time.
To add a package, put its name in `scripts/requirements.txt` and run `bash scripts/update.sh`.
