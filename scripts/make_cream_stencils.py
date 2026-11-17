#!/usr/bin/env python3
"""
make_cream_stencils.py - stencils for the cream parts of a piece
================================================================

Cream is the base coat, so the art files have no cream layer: cream is whatever the
paint layers leave open inside the piece's area. This writes two sheets per piece:

    <name> - cream base stencil.svg      the whole area, less bare wood / hardware
    <name> - cream touch-up stencil.svg  only the cream you see on the finished piece

Base: for the cream coat before the piece's colours and black go on (they cover it).
  One opening = the "area" outline, minus anything marked as never painted: a layer
  labelled "no paint (reference - no cut)" (or "wood ...") in the source - e.g. the lane
  inside the CARD VALUE oval and the card's insert - and the holes in a "holes
  (registration)" layer (not the posts). Without such a layer it is the area outline.
Touch-up: for fixing cream after the colours and black are on. Openings = the area minus
  every paint layer, ending at the black's edge (--trap 0.013 instead runs them that far
  under the black, if the black will be repainted afterwards). Cream narrower than --min
  (default 0.02in) is left closed - it can't be cut and weeded cleanly; brush those bits.
  Loose bits of film inside an opening (letters, dots, details) must stay put: keep them
  on transfer tape. Usually you cut only the part you need.

Openings are refitted with as few nodes as hold the shape (straight lines, arcs or smooth
curves, whichever needs fewer); no point is more than ~0.003in off.
Both sheets have the SAME registration marks, windows and reference outline as the
piece's sheets from make_layer_stencils.py (same frame code), so they line up the same way.
They are not numbered: when you use them depends on the job.
Not needed for a plain bordered area (slings, lamp strips): their area stencil is the
cream stencil. A paint layer with "cream" in its name (e.g. pop bumper suits) counts as cream.
The master script (make_all_stencils.py) makes these sheets only for the pieces listed under
"cream_stencils" in the game's playfield.json: a piece with bare wood inside its area (pop
bumper wood rings ...) needs that wood in a "no paint" layer first, or it would get cream.

Runs on source SVGs with an "area" layer and paint layers. Run (from the game folder):
    bash scripts/stencils.sh "stencils/LC lady luck girl.svg"
    python3 scripts/make_cream_stencils.py "stencils/LC lady luck girl.svg" --trap 0
Options (inches): --trap 0  --min 0.02  (touch-up sheet; + the mark options of make_layer_stencils.py)
Needs: Python 3.9+, numpy, shapely
"""
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import use_venv  # shared Python environment
import argparse, os, sys, copy
import xml.etree.ElementTree as ET
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_layer_stencils as MLS
from make_stencils import ring_to_d, U
import curvefit as CF

KIND = 'cream stencils: base (whole area less bare wood) and touch-up (the visible cream)'


def applies(root):
    """True if the SVG has an "area" layer and paint layers (a cream stencil can be made)."""
    has_area = any((g.get(f'{{{MLS.INK}}}label') or g.get('id') or '').strip().lower().startswith('area')
                   and any(p.get('d') for p in g.iter(f'{{{MLS.SVG_NS}}}path'))
                   for g in root.iter(f'{{{MLS.SVG_NS}}}g') if g.get(f'{{{MLS.INK}}}groupmode') == 'layer')
    return has_area and MLS.applies(root)


def build_parser():
    """Command-line options: the cream ones plus the sheet/mark options shared with
    make_layer_stencils.py (so the marks come out the same)."""
    ap = argparse.ArgumentParser(description='Cream stencil: the area minus the paint layers.')
    ap.add_argument('svg')
    ap.add_argument('--trap', type=float, default=0.0, help='touch-up sheet: how far the openings run under the black (in)')
    ap.add_argument('--min', type=float, default=0.02, help='touch-up sheet: narrowest cream that gets an opening (in)')
    ap.add_argument('--mark-offset', type=float, default=0.20)
    ap.add_argument('--mark-size', type=float, default=0.25)
    ap.add_argument('--window', type=float, default=0.0625)
    ap.add_argument('--outdir')
    ap.add_argument('--except-keyline', action='store_true',
                    help='file also has a centerline (marks then match its keyline-less colour sheets)')
    return ap


def _sample(d):
    """path data -> list of closed point rings (for measuring a fit)"""
    from make_stencils import path_to_rings
    return [np.asarray(r) for r in path_to_rings(d) if len(r) > 2]


def fit_ring(coords, tol=0.5):
    """One closed outline -> (path data, nodes, max deviation in units): the fewer-node of
    lines+arcs (ring_to_d) and smooth curves (curvefit), as long as it stays within ~1 unit."""
    P = np.asarray(coords, float)[:-1]
    ref = LineString(list(P) + [P[0]])
    best = None
    cands = []
    d1, n1 = ring_to_d(coords); cands.append((d1, n1))
    try:
        segs = CF.fit_closed(P, tol=tol, sharpen=False)
        if segs: cands.append((CF.to_d(segs), len(segs)))
    except Exception:
        pass
    for d, n in cands:
        rings = _sample(d)
        if not rings: continue
        Q = rings[0]
        dev = max(max(ref.distance(__import__('shapely').geometry.Point(q)) for q in Q[::3]),
                  LineString(list(Q) + [Q[0]]).hausdorff_distance(ref))
        if dev <= 1.0 and (best is None or n < best[1]): best = (d, n, dev)
    if best is None:   # neither within tolerance: keep the lines+arcs version
        d, n = cands[0]; best = (d, n, float('nan'))
    return best


def no_paint(root):
    """Shapes that are never painted, from the source: a layer labelled "no paint ..." or
    "wood ..." (bare wood / hardware inside a piece, e.g. the lane inside the CARD VALUE
    oval, an insert), and the holes in the "holes (registration)" layer (not the posts).
    Returns (no-paint shape, holes shape)."""
    nop, holes = [], []
    for g in root.iter(f'{{{MLS.SVG_NS}}}g'):
        if g.get(f'{{{MLS.INK}}}groupmode') != 'layer': continue
        lab = (g.get(f'{{{MLS.INK}}}label') or g.get('id') or '').strip().lower()
        paths = [q for q in g.iter(f'{{{MLS.SVG_NS}}}path') if q.get('d')]
        if lab.startswith(('no paint', 'nopaint', 'wood')):
            nop += [MLS.evenodd_poly(q.get('d')) for q in paths]
        elif lab.startswith('holes'):
            in_post = {id(q) for grp in g.iter(f'{{{MLS.SVG_NS}}}g') if (grp.get('id') or '').lower().startswith('post')
                       for q in grp.iter(f'{{{MLS.SVG_NS}}}path')}
            holes += [MLS.evenodd_poly(q.get('d')) for q in paths
                      if id(q) not in in_post and not (q.get('id') or '').lower().startswith('post') and not q.get('transform')]
    return unary_union(nop) if nop else Polygon(), unary_union(holes) if holes else Polygon()


def cream_geometry(layers, geo, area_d, trap, minw, nopaint=Polygon(), holes=Polygon()):
    """area minus colours minus (black shrunk by trap) minus no-paint areas (grown by trap, so
    the cream never creeps under the black next to bare wood) minus holes, with bits narrower
    than minw closed"""
    area = MLS.evenodd_poly(area_d)
    if not nopaint.is_empty: area = area.difference(nopaint.buffer(trap, join_style=2, mitre_limit=10) if trap > 0 else nopaint)
    if not holes.is_empty: area = area.difference(holes)
    black = [geo[lab] for lab, _, _ in layers if lab.lower() == 'black']
    other = [geo[lab] for lab, _, _ in layers if lab.lower() != 'black' and 'cream' not in lab.lower()]   # a "cream" layer is cream
    paint = unary_union(other + [b.buffer(-trap, join_style=2, mitre_limit=10) if trap > 0 else b for b in black])
    cream = area.difference(paint)
    h = minw / 2
    cream = cream.buffer(-h, join_style=2, mitre_limit=10).buffer(h, join_style=2, mitre_limit=10).intersection(area)
    polys = [p for p in getattr(cream, 'geoms', [cream]) if p.geom_type == 'Polygon' and p.area >= minw * minw]
    return polys


def main(argv=None):
    """Make the cream stencil sheet for one source SVG."""
    a = build_parser().parse_args(argv)
    root = ET.parse(a.svg).getroot()
    if not applies(root):
        print('  no "area" layer - no cream stencil'); return
    # the sheet frame (marks, windows, size) exactly as make_layer_stencils.py lays it out
    fa = MLS.build_parser().parse_args([a.svg, '--mark-offset', str(a.mark_offset), '--mark-size', str(a.mark_size),
                                        '--window', str(a.window)] + (['--outdir', a.outdir] if a.outdir else [])
                                       + (['--except-keyline'] if a.except_keyline else []))
    P = MLS.prepare(fa, generator='make_cream_stencils.py')
    if P is None: return
    # the paint to keep out of the cream: ALL paint layers, keyline included
    full = P if not a.except_keyline else MLS.prepare(argparse.Namespace(**{**vars(fa), "except_keyline": False}),
                                                      generator='make_cream_stencils.py')
    nop, holes = no_paint(root)

    def sheet(kind, polys, note, as_drawn=None):
        """Refit the openings and write one sheet in the piece's frame (as_drawn = path data
        to cut exactly as it is in the source instead)."""
        if as_drawn:
            import re
            g = MLS.evenodd_poly(as_drawn); gp = [q for q in getattr(g, 'geoms', [g]) if q.geom_type == 'Polygon']
            isl = sum(len(q.interiors) for q in gp)
            nodes = len(re.findall(r'[LCAQSHVTlcaqshvt]', as_drawn))
            P.write('cream', kind, [('cream-' + kind.split()[0], as_drawn)], nodes, note, '#f6e39c',
                    f'{len(gp)} opening(s)' + (f', {isl} loose film island(s) inside openings - keep them on transfer tape' if isl else '')
                    + ', the area outline exactly as drawn')
            return
        parts = []; nodes = 0; worst = 0.0; isl = 0
        for poly in sorted(polys, key=lambda p: (p.bounds[1], p.bounds[0])):
            for ring in [poly.exterior, *poly.interiors]:
                d, n, dev = fit_ring(list(ring.coords))
                parts.append(d); nodes += n; worst = max(worst, dev if dev == dev else 0)
            isl += len(poly.interiors)
        pieces = (f'{len(polys)} opening(s)' + (f', {isl} loose film island(s) inside openings - keep them on transfer tape' if isl else '')
                  + f', fit within {worst / U:.4f} in')
        # unnumbered sheet: write() names files "<stem> - <step> <kind>.svg"
        P.write('cream', kind, [('cream-' + kind.split()[0], ' '.join(parts))], nodes, note, '#f6e39c', pieces)

    # base: the whole area less what is never painted
    area = MLS.evenodd_poly(P.area_d)
    base = area.difference(unary_union([nop, holes])) if not (nop.is_empty and holes.is_empty) else area
    base = [p for p in getattr(base, 'geoms', [base]) if p.geom_type == 'Polygon' and p.area > 1.0]
    sheet('base stencil', base,
          'Cream base coat for the whole piece, before its colours and black go on (they cover it). '
          'Bare wood, inserts and holes marked in the source are left closed.',
          as_drawn=P.area_d if (nop.is_empty and holes.is_empty) else None)
    # touch-up: only the visible cream
    polys = cream_geometry(full.layers, full.geo, P.area_d, a.trap * U, a.min * U, nop, holes)
    if not polys:
        print('  no cream left open in the area - no touch-up stencil'); return
    sheet('touch-up stencil', polys,
          f'Touch up cream after the colours and black are on: openings = the area minus the paint layers'
          + (f', running {a.trap}in under the black' if a.trap > 0 else ', ending at the edge of the black')
          + f'; cream narrower than {a.min}in left closed (brush those).')

if __name__ == '__main__':
    main()
