#!/usr/bin/env python3
"""
Vampire arcana token: the vampire-counter knight redrawn in the style of a French woodcut tarot card
(after the look of MakerWorld's "Token Arcana" set, not its art). Black line art with hatched shading
on white paper, one gold accent (the moon and the sword's hilt) and red used only for blood. The name
sits in a white title plate with room around it; the 1/1 ... 9/9 dial shows through a framed window
in a matching footer plate. Simple borders: a black card edge and black rules between the plates.

Spec: see README.md in this folder.

Printing: the front and the wheel print FACE-DOWN, so the art is a flat 0.4 mm inlay (two layers) in
the first layers on the plate: a smooth face with crisp colour edges and no relief steps. Above
INLAY everything (front, wheel, back) is white. Every colour change is in layers 1-2, so the whole
plate needs ~6 swaps however much ink the art has.

The frame, mechanism and build are shared with models/vampire-counter (imported from it), which is
the same card with colour-fill alt art: plates, rules, title, footer window box and back come from
`vc.frame()` / `vc.finish()` / `vc.back_regions()`, the plate from `vc.write_plate()`. This file is
only the woodcut scene. The mechanism is the vampire-counter v1.2 wheel and detent: one wheel, 9 V
notches, a tapered filleted cantilever detent, black digits inlaid flat in the wheel's white face.

Run (from the repo root):
    .venv\\Scripts\\python.exe models\\vampire-arcana\\vampire_arcana.py
Outputs (millimetres) go to models\\vampire-arcana\\out\\
    parts/<object>_<n>_<colour>.stl   parts laid out as on the plate; load as ONE object (--assemble)
    parts/slice_args.txt              the matching slice_bambu.py arguments
    arcana_preview.png                the face at 1/1, 5/5, 9/9, a nozzle simulation, and the back
    arcana_detail.png                 the head and the window at print scale (bead-sized features)
"""
import importlib.util
from pathlib import Path

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
PARTS = OUT / "parts"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# The card frame, back, dial mechanism, build and drawing helpers come from vampire-counter (which pulls in
# vampire-token for extrusion and vampire-dial for text layout).
vc = _load("vampire_counter", HERE.parent / "vampire-counter" / "vampire_counter.py")
vt, vd = vc.vt, vc.vd
spline, taper, sym, sym_pts, disk = vc.spline, vc.taper, vc.sym, vc.sym_pts, vc.disk

# ---- Parameters (mm) -------------------------------------------------------
# Palette, card, frame (plates, rules, title, window box), inlay and slicer settings: shared, in vc.
PALETTE = vc.PALETTE
INK, BLOOD, GOLD, PAPER = vc.INK, vc.BLOOD, vc.GOLD, vc.PAPER
CARD_W, CARD_H, CX = vc.CARD_W, vc.CARD_H, vc.CX
ART = vc.ART

# Line weights. A 0.4 nozzle lays a ~0.45-0.5 mm bead: every black line is at least one bead and
# every white gap between lines at least one bead, so hatching can't be finer than ~1.2 mm pitch.
OUTLINE = 0.7                    # figure outlines
LINE = 0.55                      # strands, folds, hatching
PITCH = 1.25                     # hatching pitch (0.55 line + 0.7 gap)
MIN_HATCH = 2.0                  # shorter hatch strokes are dropped (they'd be < 1 mm^2)

# Scene (card mm). The knight's local frame: face centre at HEAD, 1 unit = 1 mm.
HEAD = (CX, 50.6)
MOON_C, MOON_R = (CX, 52.0), 16.5
MOON_COLOUR = GOLD               # BLOOD for a blood moon
RAYS = 28                        # woodcut rays around the moon
RAY_R = (MOON_R + 1.4, MOON_R + 5.0, MOON_R + 3.4)    # start, long tip, short tip
SKY_Y0 = 40.0                    # lowest engraved sky line
HALO = 0.7                       # white margin cleared around shapes drawn over the sky lines

BEAD = vc.BEAD                   # 0.45
# ---------------------------------------------------------------------------


def lines_of(g):
    if g.is_empty:
        return []
    if g.geom_type == "LineString":
        return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "LineString"]


def hatch(region, angle, pitch=PITCH, w=LINE, phase=0.0, min_len=MIN_HATCH):
    """Parallel strokes at `angle` degrees, clipped so their round caps stay inside `region`."""
    inner = region.buffer(-w / 2)
    if inner.is_empty:
        return Polygon()
    x0, y0, x1, y1 = inner.bounds
    c = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
    R = np.hypot(x1 - x0, y1 - y0) / 2 + 1
    a = np.radians(angle)
    d, n = np.array([np.cos(a), np.sin(a)]), np.array([-np.sin(a), np.cos(a)])
    out = []
    for off in np.arange(-R + phase % pitch, R, pitch):
        seg = LineString([c + off * n - R * d, c + off * n + R * d]).intersection(inner)
        out += [s.buffer(w / 2, quad_segs=8) for s in lines_of(seg) if s.length >= min_len]
    return unary_union(out) if out else Polygon()


def at(g):
    return affinity.translate(g, *HEAD)


def outlined(cv, fill, g, clip, w=OUTLINE, halo=0.0):
    """Fill g with a black outline of width w straddling its edge (g in card coordinates). A halo
    first clears a white margin around it, so lines behind stop a bead short instead of grazing it."""
    if halo:
        cv.paint(PAPER, g.buffer(w / 2 + halo), clip)
    cv.paint(INK, g.buffer(w / 2, join_style="round"), clip)
    cv.paint(fill, g.buffer(-w / 2, join_style="round"), clip)


def inside(g, w=OUTLINE):
    """The area inside g's outline where hatching may run (strokes merge into the outline)."""
    return g.buffer(-w / 2 + 0.1)


# ---- scene elements ---------------------------------------------------------------

def sky_y(n):
    """The n-th sky line's height (clouds snap their bases to this grid)."""
    return SKY_Y0 + n * PITCH


def sky_lines(cv, clip):
    """Engraved sky: horizontal strokes running in from both side edges, ragged lengths."""
    x0, _, x1, y1 = ART
    out = []
    for i, y in enumerate(np.arange(SKY_Y0, y1 - 0.6, PITCH)):
        for side, ph in ((-1, 0.0), (1, 1.7)):
            L = 8.5 + 3.5 * np.sin(0.61 * y + ph) + 1.8 * np.sin(1.73 * y + 2 * ph)
            xa = x0 - 1 if side < 0 else x1 + 1
            xb = x0 + L if side < 0 else x1 - L
            out.append(LineString([(xa, y), (xb, y)]).buffer(LINE / 2, quad_segs=8))
    cv.paint(INK, unary_union(out), clip)


def moon(cv, clip):
    rays = []
    for i in range(RAYS):
        a = np.radians(90 + 360 * i / RAYS)
        u = np.array([np.cos(a), np.sin(a)])
        tip = RAY_R[1] if i % 2 == 0 else RAY_R[2]
        p0, p1 = np.array(MOON_C) + RAY_R[0] * u, np.array(MOON_C) + tip * u
        rays.append(taper([tuple(p0), tuple(p1)], 1.0 if i % 2 == 0 else 0.8, 0.5, n=16))
    cv.paint(INK, unary_union(rays), clip)
    outlined(cv, MOON_COLOUR, disk(MOON_C, MOON_R, 128), clip, w=0.8)


def cloud(cv, clip, bumps, line):
    """A woodcut cloud: scalloped top (a row of disks) on a flat base, outlined, with a curl in each bump.
    Its base sits on sky line `line`, so the outline swallows that line and the next is a full gap below."""
    base_y = sky_y(line) + 0.35
    g = unary_union([disk((x, y), r, 32) for x, y, r in bumps])
    g = g.intersection(box(-10, base_y, 80, 100))
    cv.paint(PAPER, g.buffer(0.3 + HALO).intersection(box(-10, base_y - 0.3, 80, 100)), clip)
    outlined(cv, PAPER, g, clip, w=0.6)
    for x, y, r in bumps:
        if r < 2.4:
            continue
        t = np.linspace(np.radians(200), np.radians(330), 12)
        rr = r * 0.55
        curl = LineString(np.c_[x + rr * np.cos(t), y + 0.2 + rr * np.sin(t)])
        curl = curl.intersection(g.buffer(-0.9))
        for s in lines_of(curl):
            if s.length > 1.5:
                cv.paint(INK, s.buffer(LINE / 2, quad_segs=8), clip)


def tower(cv, clip, x0, x1, top, spire, windows=()):
    body = box(x0, 15.0, x1, top)
    roof = Polygon([(x0 - 0.6, top), (x1 + 0.6, top), ((x0 + x1) / 2, top + spire)])
    outlined(cv, PAPER, body, clip, w=0.6, halo=HALO)
    for y in np.arange(top - 2.4, 15.0, -2.4):                    # stone courses
        cv.paint(INK, LineString([(x0, y), (x1, y)]).buffer(0.25, cap_style="flat"), clip)
    outlined(cv, PAPER, roof, clip, w=0.6, halo=HALO)
    cv.paint(INK, hatch(inside(roof, 0.6), 90, pitch=1.2, min_len=1.2), clip)
    for cx, y0, w, h in windows:
        cv.paint(INK, vc.lancet(cx, y0, w, h), clip)


# ---- the knight ---------------------------------------------------------------------

def knight(cv, clip):
    """The vampire-counter knight's silhouette, re-inked: outlines, hatched armour, a black cloak with
    white folds, white hair with black strands, gold hilt and blood running down the blade."""
    S = lambda g: sym(g, 0)
    A = lambda g: at(g)

    def ink(g, colour=INK):
        cv.paint(colour, A(g), clip)

    def line(pts, w0=LINE, w1=None, colour=INK):
        ink(S(taper(pts, w0, w1 or w0)), colour)

    # cloak: a solid black mass flaring to the frame's bottom corners, with white fold lines
    cloak = spline(sym_pts([(0, -7.0), (-10.0, -8.6), (-18.5, -12.2), (-24.5, -18.5), (-27.5, -26.0),
                            (-29.5, -36.0), (0, -36.0)]), n=400)
    ink(cloak)
    for f in ([(-21.8, -19.6), (-23.6, -25.0), (-24.6, -33.0)], [(-18.6, -21.5), (-19.6, -27.0), (-20.2, -33.0)],
              [(-25.4, -23.5), (-27.0, -29.5), (-27.9, -35.0)]):
        line(f, 0.5, 0.9, PAPER)

    # breastplate: outlined, shaded down both flanks, fauld lames across the bottom
    chest = spline(sym_pts([(0, -11.5), (-7.8, -12.2), (-10.4, -17.0), (-11.6, -25.0), (-12.0, -36.0), (0, -36.0)]))
    outlined(cv, PAPER, A(chest), clip)
    flank = inside(chest).intersection(box(-13, -36, -8.4, -11))
    ink(S(hatch(flank, 98, phase=0.3)))
    for y in (-28.0, -31.2, -34.4):
        line([(-11.4, y + 0.6), (-6.0, y - 0.1), (-1.5, y - 0.3)])

    # pauldrons: three overlapping lames each side, outlined. As in an engraving, the strip of each lower
    # lame that shows under the one above is hatched (it's in that lame's shadow); the top lame is clean.
    cap = spline([(-5.0, -10.8), (-10.0, -9.6), (-16.0, -10.6), (-21.4, -13.8), (-24.6, -18.8),
                  (-23.0, -20.8), (-17.0, -18.4), (-11.0, -16.9), (-5.0, -16.6)])
    offsets = ((-2.2, -5.4), (-1.1, -2.7), (0.0, 0.0))              # lowest lame first
    for i, (dx, dy) in enumerate(offsets):
        lame = affinity.translate(cap, dx, dy)
        outlined(cv, PAPER, A(S(lame)), clip)
        if i < len(offsets) - 1:
            shade = inside(lame).intersection(box(-30, -30, -11.0, 0))
            ink(S(hatch(shade, 58, phase=0.5 * i, min_len=1.6)))
        ink(S(disk((-8.0 + dx, -12.0 + dy), 0.6, 12)))             # rivet

    # long white hair, outlined, with flowing black strands
    hair = spline(sym_pts([(0, 10.9), (-4.7, 10.2), (-7.9, 7.4), (-9.3, 2.4), (-9.8, -3.2), (-10.8, -8.4),
                           (-12.4, -12.6), (-7.6, -12.2), (-4.0, -9.8), (0, -9.4)]), n=400)
    outlined(cv, PAPER, A(hair), clip, w=0.75)
    for st in ([(-3.0, 9.45), (-5.4, 8.5), (-7.0, 6.2), (-7.7, 3.0)],
               [(-7.5, 1.6), (-7.9, -2.4), (-8.6, -6.4), (-10.2, -10.8)],
               [(-6.4, -3.6), (-6.9, -7.2), (-8.0, -10.8)]):
        line(st, LINE, 0.5)

    # gorget: two lames
    gorget = spline(sym_pts([(0, -9.4), (-4.4, -9.2), (-6.6, -10.8), (-7.2, -14.6), (0, -15.2)]))
    outlined(cv, PAPER, A(gorget), clip)
    line([(-6.2, -12.2), (-3.0, -12.8), (0, -13.0)])

    # the face: gaunt and stern
    face = spline(sym_pts([(0, 8.3), (-2.6, 8.4), (-4.6, 6.8), (-5.6, 3.4), (-5.7, 0.0), (-5.3, -3.6),
                           (-4.3, -6.4), (-2.6, -8.4), (0, -9.0)]))
    outlined(cv, PAPER, A(face), clip, w=0.65)
    line([(-5.0, 3.1), (-3.1, 2.9), (-1.0, 2.2)], 1.3, 1.0)              # heavy brows
    ink(taper([(0, 3.0), (0, 4.4)], 0.55, 0.55))                         # frown line
    eye = affinity.translate(affinity.rotate(affinity.scale(disk((0, 0), 1, 32), 1.4, 0.55), -6), -2.6, 1.05)
    ink(S(eye), BLOOD)
    ink(taper([(0.3, 1.0), (0.75, -1.4), (1.3, -3.3)], 0.6, 0.75))       # nose
    ink(taper([(-1.2, -3.8), (0, -4.2), (1.3, -3.5)], 0.6, 0.6))
    line([(-4.5, -0.8), (-4.1, -2.6), (-3.4, -3.9)], 0.55, 0.5)          # cheek hollows
    # moustache and pointed beard, outlined, with a centre strand; their outlines meet as the mouth
    beard = Polygon(sym_pts([(0, -7.4), (-2.7, -7.1), (-2.5, -9.4), (-1.2, -11.2), (0, -12.6)])).buffer(0.3).buffer(-0.3)
    outlined(cv, PAPER, A(beard), clip, w=0.55)
    ink(taper([(0, -8.3), (0, -11.2)], 0.5, 0.5))
    stache = Polygon(sym_pts([(0, -4.9), (-1.7, -5.0), (-3.3, -5.9), (-4.3, -8.0), (-2.7, -6.9),
                              (-1.2, -6.3), (0, -6.3)])).buffer(0.2).buffer(-0.2)
    outlined(cv, PAPER, A(stache), clip, w=0.55)

    # the sword, planted point-down: blood runs from the guard down the fuller and drips off it
    blade = box(-1.9, -40, 1.9, -26.0)
    outlined(cv, PAPER, A(blade), clip)
    ink(box(-0.3, -40, 0.3, -31.0))                                       # fuller below the blood
    blood = unary_union([box(-0.65, -31.6, 0.65, -26.2), disk((0, -31.6), 0.65, 16),
                         taper([(0.65, -27.4), (1.15, -29.5)], 0.6, 0.85)]).buffer(0.0)
    ink(blood, BLOOD)
    for c, r in (((0, -33.8), 0.62), ((1.2, -31.0), 0.58)):              # drops
        ink(unary_union([disk(c, r, 16), Polygon([(c[0] - r * 0.7, c[1] + 0.3), (c[0] + r * 0.7, c[1] + 0.3),
                                                   (c[0], c[1] + 1.6 * r + 0.3)])]), BLOOD)
    guard = unary_union([box(-6.5, -26.4, 6.5, -24.6), S(taper([(-6.0, -25.5), (-8.2, -25.9), (-9.0, -27.6)], 1.8, 1.0))])
    outlined(cv, GOLD, A(guard), clip, w=0.65)
    grip = box(-1.4, -24.6, 1.4, -19.2)
    ink(grip.buffer(0.3))
    for y in (-20.6, -22.4):                                              # leather wrap, white diagonals
        ink(taper([(-1.2, y - 0.5), (1.2, y + 0.5)], 0.5, 0.5).intersection(grip.buffer(-0.05)), PAPER)
    outlined(cv, GOLD, A(disk((0, -17.4), 2.2, 32)), clip, w=0.65)
    ink(disk((0, -17.4), 1.15, 24), BLOOD)


def bats(cv, clip, spec, halo=HALO):
    for c, span, tilt in spec:
        b = vc.bat(c, span, tilt)
        if halo:
            cv.paint(PAPER, b.buffer(halo), clip)
        cv.paint(INK, b, clip)


# ---- the card -----------------------------------------------------------------------------

def front_regions(card):
    """The shared frame (vc.frame), with the woodcut scene in its art plate."""
    cv = vc.Canvas(card)
    clip = vc.frame(cv)

    # the scene, painted back to front
    sky_lines(cv, clip)
    moon(cv, clip)
    cloud(cv, clip, [(2.5, 67.5, 2.8), (7.0, 69.5, 3.4), (12.0, 68.2, 2.6), (15.6, 66.6, 1.8)], 20)
    cloud(cv, clip, [(47.4, 68.0, 1.8), (51.0, 69.8, 2.7), (56.0, 70.2, 3.5), (61.0, 68.6, 2.8)], 21)
    bats(cv, clip, [((8.6, 56.0), 8.5, 10.0), ((54.6, 58.4), 7.5, -8.0)])
    bats(cv, clip, [((40.0, 60.2), 5.6, -12.0)], halo=0.0)           # crossing the moon
    tower(cv, clip, 2.6, 9.2, 39.5, 9.0, windows=[(5.9, 33.5, 1.5, 3.4)])
    tower(cv, clip, 9.2, 13.6, 34.5, 6.0, windows=[(11.4, 29.6, 1.3, 2.8)])
    tower(cv, clip, 53.8, 60.4, 41.5, 9.5, windows=[(57.1, 35.4, 1.5, 3.4)])
    tower(cv, clip, 49.4, 53.8, 36.0, 6.5, windows=[(51.6, 31.0, 1.3, 2.8)])
    knight(cv, clip)

    return vc.finish(cv, card)


# ---- previews -----------------------------------------------------------------------------

def detail(regions, wh, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_, axes = plt.subplots(1, 2, figsize=(15, 8))
    for ax, sim in zip(axes, (False, True)):
        vc.draw_face(ax, regions, wh, 3, sim)
        ax.set_xlim(HEAD[0] - 16, HEAD[0] + 16); ax.set_ylim(HEAD[1] - 22, HEAD[1] + 14)
        ax.set_title("head, sword, hilt" + (" (nozzle sim)" if sim else ""), fontsize=10)
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close(fig_)
    print(f"detail -> {path}")


# ---- build --------------------------------------------------------------------------------

def main():
    m = vc.mechanism()
    card = m["card"]
    regions = front_regions(card)
    back = vc.back_regions(card) if vc.BACK_ART else         {PAPER: card, INK: Polygon(), BLOOD: Polygon(), GOLD: Polygon()}
    vc.report(card, regions, back)
    vc.write_plate(m, regions, back, PARTS)
    vc.preview(regions, back, m["wh"], OUT / "arcana_preview.png")
    detail(regions, m["wh"], OUT / "arcana_detail.png")


if __name__ == "__main__":
    main()
