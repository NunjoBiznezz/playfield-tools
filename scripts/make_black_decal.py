#!/usr/bin/env python3
"""Black-only waterslide decal files for the Lady Luck pieces.

Run from the game folder (e.g. Documents/Pinball/Williams/Lady Luck):
    bash scripts/decals.sh                          # every piece in stencils/ with a black layer
    bash scripts/decals.sh "stencils/UL queen lane.svg" [--margin 0.0625]

Writes _generated/"<name> - black decal.svg":
  * layer "black (print)"  - the piece's black layer only, recoloured pure #000000
    so the laser prints it with black toner alone (no CMY halftone dots).
  * layer "decal cut"      - one rounded rectangle round the black art
    (margin and corner radius --margin, default 1/16in; 8 nodes). In Silhouette
    Studio set it to cut with no line colour, and set the black art to no cut.
Colour, holes, centerline and reference layers are left out: paint the colours
through the stencils, then apply the clear decal over them.
Standard library only. 300 units = 1 inch.
"""
import argparse, copy, math, os, re, sys
import xml.etree.ElementTree as ET

SVG = 'http://www.w3.org/2000/svg'
INK = 'http://www.inkscape.org/namespaces/inkscape'
ET.register_namespace('', SVG)
ET.register_namespace('inkscape', INK)
ET.register_namespace('sodipodi', 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd')
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
GM, LB = '{%s}groupmode' % INK, '{%s}label' % INK
U = 300.0
K = 0.5522847498

def layers(root):
    """All Inkscape layers in the SVG."""
    return [g for g in root.iter('{%s}g' % SVG) if g.get(GM) == 'layer']

def is_black(g):
    """True if this layer is the black layer (id 'black' or a name starting with 'black')."""
    return g.get('id') == 'black' or (g.get(LB) or '').strip().lower().startswith('black')

TOK = re.compile(r'[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')
NARGS = dict(M=2, L=2, H=1, V=1, C=6, S=4, Q=4, T=2, A=7, Z=0)

def arc_points(x1, y1, rx, ry, rot, large, sweep, x2, y2, n=48):
    """Points along an SVG elliptical arc (endpoint -> centre parametrisation)."""
    rx, ry = abs(rx), abs(ry)
    if rx == 0 or ry == 0 or (x1 == x2 and y1 == y2):
        return [(x1, y1), (x2, y2)]
    ph = math.radians(rot); cp, sp = math.cos(ph), math.sin(ph)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = cp * dx + sp * dy, -sp * dx + cp * dy
    lam = x1p ** 2 / rx ** 2 + y1p ** 2 / ry ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2
    den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
    co = math.sqrt(max(0.0, num / den)) * (-1 if large == sweep else 1)
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    cx = cp * cxp - sp * cyp + (x1 + x2) / 2
    cy = sp * cxp + cp * cyp + (y1 + y2) / 2
    ang = lambda ux, uy, vx, vy: math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
    t1 = ang(1, 0, (x1p - cxp) / rx, (y1p - cyp) / ry)
    dt = ang((x1p - cxp) / rx, (y1p - cyp) / ry, (-x1p - cxp) / rx, (-y1p - cyp) / ry)
    if not sweep and dt > 0: dt -= 2 * math.pi
    elif sweep and dt < 0: dt += 2 * math.pi
    out = []
    for k in range(n + 1):
        t = t1 + dt * k / n
        ux, uy = rx * math.cos(t), ry * math.sin(t)
        out.append((cp * ux - sp * uy + cx, sp * ux + cp * uy + cy))
    return out

def path_points(d):
    """Every end/control point of a path (absolute). The box round them contains the curve."""
    pts, t = [], TOK.findall(d)
    i, cmd, x, y, sx, sy = 0, None, 0.0, 0.0, 0.0, 0.0
    while i < len(t):
        if t[i].isalpha():
            cmd = t[i]; i += 1
            if cmd in 'Zz':
                x, y = sx, sy; continue
        n = NARGS[cmd.upper()]
        a = [float(v) for v in t[i:i + n]]; i += n
        rel = cmd.islower(); C = cmd.upper()
        if C == 'H':
            x = a[0] + (x if rel else 0); pts.append((x, y))
        elif C == 'V':
            y = a[0] + (y if rel else 0); pts.append((x, y))
        elif C == 'A':
            ex, ey = a[5] + (x if rel else 0), a[6] + (y if rel else 0)
            pts += arc_points(x, y, a[0], a[1], a[2], a[3], a[4], ex, ey)
            x, y = ex, ey
        else:
            for j in range(0, n, 2):
                px, py = a[j] + (x if rel else 0), a[j + 1] + (y if rel else 0)
                pts.append((px, py))
            x, y = pts[-1]
            if C == 'M':
                sx, sy = x, y
                cmd = 'l' if rel else 'L'
    return pts

def count_nodes(d):
    """Number of nodes in SVG path data (every drawing command except Z)."""
    return sum(1 for c in re.findall(r'[A-Za-z]', d) if c not in 'Zz')

def recolour(el):
    """Set every fill and stroke under `el` (attributes and style) to pure black #000000,
    leaving 'none' alone."""
    for e in el.iter():
        for k in ('fill', 'stroke'):
            v = e.get(k)
            if v and v != 'none':
                e.set(k, '#000000')
        st = e.get('style')
        if st:
            e.set('style', re.sub(r'(fill|stroke)\s*:\s*(?!none)[^;]+', r'\1:#000000', st))

def rounded_rect(x0, y0, x1, y1, r):
    """SVG path data for a rectangle x0,y0 - x1,y1 with corners of radius r: 4 lines + 4 one-
    curve corners (8 nodes)."""
    c = r * K
    f = lambda v: ('%.2f' % v).rstrip('0').rstrip('.')
    p = [('M', x0 + r, y0), ('L', x1 - r, y0), ('C', x1 - r + c, y0, x1, y0 + r - c, x1, y0 + r),
         ('L', x1, y1 - r), ('C', x1, y1 - r + c, x1 - r + c, y1, x1 - r, y1),
         ('L', x0 + r, y1), ('C', x0 + r - c, y1, x0, y1 - r + c, x0, y1 - r),
         ('L', x0, y0 + r), ('C', x0, y0 + r - c, x0 + r - c, y0, x0 + r, y0)]
    return ' '.join(s[0] + ' ' + ' '.join(f(v) for v in s[1:]) for s in p) + ' Z'

def make(src, outdir, margin_in):
    """Make the black decal file for one piece. Returns (output path, summary) or (None, reason
    skipped)."""
    tree = ET.parse(src); root = tree.getroot()
    blacks = [g for g in layers(root) if is_black(g)]
    if not blacks:
        return None, 'no black layer - skipped'
    for g in blacks:
        if any(e.get('transform') for e in g.iter()):
            return None, 'black layer has transforms - not handled, skipped'
    new = ET.Element(root.tag, {k: v for k, v in root.attrib.items()})
    for d in root.findall('{%s}defs' % SVG):
        new.append(copy.deepcopy(d))
    lay = ET.SubElement(new, '{%s}g' % SVG, {'id': 'black-print', GM: 'layer', LB: 'black (print)'})
    pts, nodes = [], 0
    for g in blacks:
        for ch in g:
            c = copy.deepcopy(ch); recolour(c); lay.append(c)
        for p in g.iter('{%s}path' % SVG):
            d = p.get('d') or ''
            pts += path_points(d); nodes += count_nodes(d)
        for tag in ('rect', 'circle', 'ellipse', 'polygon', 'polyline', 'line', 'text', 'use'):
            if g.find('.//{%s}%s' % (SVG, tag)) is not None:
                return None, 'black layer has <%s> elements - not handled, skipped' % tag
    if not pts:
        return None, 'black layer is empty - skipped'
    m = margin_in * U
    x0 = min(p[0] for p in pts) - m; x1 = max(p[0] for p in pts) + m
    y0 = min(p[1] for p in pts) - m; y1 = max(p[1] for p in pts) + m
    cut = ET.SubElement(new, '{%s}g' % SVG, {'id': 'decal-cut', GM: 'layer', LB: 'decal cut'})
    ET.SubElement(cut, '{%s}path' % SVG, {'id': 'decal-cut-line', 'd': rounded_rect(x0, y0, x1, y1, m),
                                          'fill': 'none', 'stroke': '#ff0000', 'stroke-width': '1'})
    # canvas = the cut rectangle plus a small pad, same coordinates, 300 units/in
    pad = 0.05 * U
    vx, vy, vw, vh = x0 - pad, y0 - pad, (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    new.set('viewBox', '%.2f %.2f %.2f %.2f' % (vx, vy, vw, vh))
    new.set('width', '%.4fin' % (vw / U)); new.set('height', '%.4fin' % (vh / U))
    name = os.path.splitext(os.path.basename(src))[0]
    out = os.path.join(outdir, name + ' - black decal.svg')
    ET.ElementTree(new).write(out, encoding='utf-8', xml_declaration=True)
    return out, 'black %d nodes, cut 8 nodes, decal %.2f x %.2fin' % (nodes, (x1 - x0) / U, (y1 - y0) / U)

def main():
    """Command line: make a decal file for each named piece, or for every piece in stencils/
    with a black layer."""
    base = os.getcwd()
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('files', nargs='*')
    ap.add_argument('--margin', type=float, default=0.0625, help='cut margin and corner radius, inches')
    ap.add_argument('--out', default=os.path.join(base, '_generated'))
    a = ap.parse_args()
    files = a.files or sorted(os.path.join(base, 'stencils', f) for f in os.listdir(os.path.join(base, 'stencils'))
                              if f.endswith('.svg') and 'calibration' not in f)
    os.makedirs(a.out, exist_ok=True)
    made = 0
    for f in files:
        out, msg = make(f, a.out, a.margin)
        if out: made += 1
        if out or a.files:
            print('%-40s %s' % (os.path.basename(f)[:40], msg))
    print('%d black decal file(s) in %s' % (made, a.out))

if __name__ == '__main__':
    main()
