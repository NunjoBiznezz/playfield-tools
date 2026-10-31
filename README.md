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
