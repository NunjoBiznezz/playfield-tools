#!/usr/bin/env python3
"""
make_all_stencils.py - one command for all of a game's stencils
===============================================================

Looks at each source SVG, works out what it needs from its layers, and calls the
right generator for it. Each kind of stencil keeps its own script; this one only
decides and calls them:

  make_stencils.py        bordered area - the SVG has a "centerline" layer
                          -> area stencil, area mask, border stencil
  make_layer_stencils.py  paint layers (red, blue, black ...)
                          -> one stencil per paint layer, in layer order, black last
                          -> + "1 area mask" when the SVG has an "area" layer
                          -> + trim lines from a "trim" layer on every sheet
                          A file with BOTH a centerline and paint layers gets both sets;
                          its colour stencils leave out the keyline edges (subpaths lying
                          on the keyline band), because the border stencil paints those,
                          and a layer that is only keyline gets no colour stencil.
  game steps              scripts that belong to one game only (e.g. Lady Luck's
                          game_scripts/make_green_rings.py), listed under "game_steps"
                          in that game's playfield.json - run when doing the whole
                          folder, or when the file a step makes is named

Run from the game folder (Lady Luck, Tropic Isle ...):
    bash scripts/stencils.sh                          every source SVG in stencils/
    bash scripts/stencils.sh "stencils/UL pop bumper.svg"   just this one
    bash scripts/stencils.sh stencils/UL*.svg         several
    bash scripts/stencils.sh --dry-run                show what would be made, make nothing

Options for the generators can go on the same line; each generator gets only the
ones it understands (e.g. --overlap goes to make_stencils.py, --mark-offset to
make_layer_stencils.py, --mask-grow to both).

Before a piece is made, its old sheets in _generated ("<name> - *.svg") are removed,
so nothing stale is left over from an earlier numbering (--keep-old to keep them).
The source SVGs are never changed.

Needs: Python 3.9+, numpy, shapely (stencils.sh sets these up in ~/.venvs/stencils).
"""
import argparse, fnmatch, glob, os, sys, traceback
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib.util
import make_stencils
import make_layer_stencils
import playfield_config

CFG = playfield_config.load()
# files in stencils/ that are not stencil sources (checked against the file name) - from playfield.json
NOT_SOURCES = dict(CFG['not_sources'])
GAME_STEPS = list(CFG['game_steps'])


def run_game_step(step):
    """import a game-only script from the game folder and call its main()"""
    path = os.path.join(os.getcwd(), step['script'])
    spec = importlib.util.spec_from_file_location(os.path.splitext(os.path.basename(path))[0], path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    mod.main()


def not_a_source(name):
    for pat, why in NOT_SOURCES.items():
        if fnmatch.fnmatch(name, pat): return why
    return None


def plan(path):
    """list of (generator module, extra args, description) for a source SVG; or ([], reason)"""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        return [], f'not readable as SVG ({e})'
    steps = []
    if make_stencils.applies(root):
        steps.append((make_stencils, [], make_stencils.KIND))
    if make_layer_stencils.applies(root):
        if steps:   # bordered piece with colours too: colour stencils without the keyline edges
            steps.append((make_layer_stencils, ['--except-keyline'],
                          'colour stencils for the paint layers (keyline left to the border stencil)'))
        else:
            steps.append((make_layer_stencils, [], make_layer_stencils.KIND))
    return steps, ('' if steps else 'no centerline layer and no paint layers - nothing to make')


def options_for(gen, extra):
    """keep only the --options (with their values) that this generator's parser knows"""
    known = gen.build_parser()._option_string_actions
    out, i = [], 0
    while i < len(extra):
        tok = extra[i]
        name = tok.split('=', 1)[0]
        takes_value = '=' not in tok and i + 1 < len(extra) and not extra[i + 1].startswith('--')
        if name in known:
            out.append(tok)
            if takes_value and known[name].nargs != 0: out.append(extra[i + 1])
        if takes_value: i += 1
        i += 1
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description='Make every stencil a source SVG needs (or every SVG in stencils/).')
    ap.add_argument('svgs', nargs='*', help='source SVGs or folders (default: stencils/)')
    ap.add_argument('--outdir', help='where to write (default: _generated in the current folder)')
    ap.add_argument('--dry-run', action='store_true', help='only show what would be made')
    ap.add_argument('--keep-old', action='store_true', help="don't remove a piece's old sheets first")
    a, extra = ap.parse_known_args(argv)
    outdir = a.outdir or os.path.join(os.getcwd(), '_generated')

    whole_folder = not a.svgs
    targets = []
    for t in (a.svgs or ['stencils']):
        if os.path.isdir(t): targets += sorted(glob.glob(os.path.join(t, '*.svg')))
        elif os.path.isfile(t): targets.append(t)
        else: print(f'!! {t}: not found')

    made, skipped, failed = [], [], []
    run_steps = [st for st in GAME_STEPS if whole_folder]
    for path in targets:
        name = os.path.basename(path); stem = os.path.splitext(name)[0]
        step = next((st for st in GAME_STEPS if st.get('source') == name), None)
        if step:
            if step not in run_steps: run_steps.append(step)
            continue
        why = not_a_source(name)
        if why: skipped.append((name, why)); continue
        steps, why = plan(path)
        if not steps: skipped.append((name, why)); continue
        if a.dry_run:
            print(f'  {name}: ' + ' + '.join(g.__name__ + '.py' + (' ' + ' '.join(x) if x else '') for g, x, _ in steps))
            made.append(name); continue
        if not a.keep_old and os.path.isdir(outdir):
            for old in glob.glob(os.path.join(glob.escape(outdir), glob.escape(stem) + ' - *.svg')):
                os.remove(old)
        ok = True
        for gen, x, kind in steps:
            print(f'\n== {name}: {kind}  [{gen.__name__}.py]')
            try:
                gen.main([path, '--outdir', outdir] + x + options_for(gen, extra))
            except SystemExit as e:
                ok = False; failed.append((name, str(e)))
            except Exception as e:
                ok = False; traceback.print_exc(); failed.append((name, f'{type(e).__name__}: {e}'))
        if ok: made.append(name)

    for st in run_steps:
        n = st.get('name') or st['script']
        print(f"\n== {n}  [{st['script']}]")
        if not os.path.exists(st['script']):
            failed.append((n, f"{st['script']} not found - run from the game folder"))
        elif st.get('needs') and not os.path.exists(st['needs']):
            failed.append((n, f"needs {st['needs']} - run build_playfield.py first"))
        elif a.dry_run:
            made.append(n)
        else:
            try:
                run_game_step(st); made.append(n)
            except SystemExit as e:
                failed.append((n, str(e)))
            except Exception as e:
                traceback.print_exc(); failed.append((n, f'{type(e).__name__}: {e}'))

    print(f'\n{"Would make" if a.dry_run else "Made"}: {len(made)}' + ('' if a.dry_run else f'  (in {outdir})'))
    if skipped:
        print(f'Skipped: {len(skipped)}')
        for n, why in skipped: print(f'  {n}: {why}')
    if failed:
        print(f'FAILED: {len(failed)}')
        for n, why in failed: print(f'  {n}: {why}')
        sys.exit(1)


if __name__ == '__main__':
    main()
