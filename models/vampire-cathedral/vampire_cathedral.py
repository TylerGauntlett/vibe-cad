#!/usr/bin/env python3
"""
Vampire cathedral token: a third art for the shared vampire card, blending its two siblings by one
rule: FLAT COLOUR for cloth, glass and gold (vampire-counter's language), WOODCUT LINE for skin,
hair, steel and stone (vampire-arcana's). So the knight wears the counter's red cloak (black folds)
and a red-lined high collar, arcana's outlined, hatched armour, a spiked gold crown, and a sword
that joins arcana's blood-run blade to the counter's banded copper grip. He stands in a cathedral:
an engraved white stone nave (arcana's ragged hatching, running in from the arch) under a pointed
arch of black stone with a gold moulding and a white bat in each spandrel, a gold rose window with
heavy black leading as his halo, and a woodcut candle either side.

Spec: see README.md in this folder.

Everything outside the art plate is shared and imported: the frame (plates, rules, Georgia title,
ruled dial footer), the back, the dial mechanism and the face-down build come from
models/vampire-counter (`vc`); the knight's parts (armour, head, sword) and the woodcut helpers
come from models/vampire-arcana (`va`). This file is the background, the red cloak, the collar,
the crown and the grip.

Printing: face-down flat inlay, as on both siblings (0.4 mm of colour in layers 1-2, white above),
so the 4 colours still cost ~6 swaps.

Run (from the repo root):
    .venv\\Scripts\\python.exe models\\vampire-cathedral\\vampire_cathedral.py
Outputs (millimetres) go to models\\vampire-cathedral\\out\\
    parts/<object>_<n>_<colour>.stl   parts laid out as on the plate; load as ONE object (--assemble)
    parts/slice_args.txt              the matching slice_bambu.py arguments
    cathedral_preview.png             the face at 1/1, 5/5, 9/9, a nozzle simulation, and the back
    cathedral_detail.png              head, crown, collar and hilt at print scale
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


# The woodcut knight (vampire-arcana), which in turn brings the shared frame and build (vampire-counter).
va = _load("vampire_arcana", HERE.parent / "vampire-arcana" / "vampire_arcana.py")
vc = va.vc
spline, taper, sym, disk = vc.spline, vc.taper, vc.sym, vc.disk

# ---- Parameters (mm) -------------------------------------------------------
INK, BLOOD, GOLD, PAPER = vc.INK, vc.BLOOD, vc.GOLD, vc.PAPER
CARD_W, CX = vc.CARD_W, vc.CX
ART = vc.ART                     # art plate (1.8, 19.2, 61.2, 72.6)
HEAD = va.HEAD                   # the knight's face centre (arcana's placement)
LINE, OUTLINE, BEAD = va.LINE, va.OUTLINE, vc.BEAD

# The nave: a pointed (two-centred) arch, its inner edge springing at y SPRING from x BAY_X, each
# side an arc of radius ARCH_RHO centred on the far side. Its apex is above the plate, so the arch
# meets the title rule with a ~9 mm opening. Outside it: black stone spandrels and piers.
BAY_X = (5.0, CARD_W - 5.0)
SPRING = 40.8
ARCH_RHO = 34.0
MOULDING = 0.8                   # gold line along the arch's inner edge
CAPITAL = (3.8, 1.2)             # gold capital on each pier at the springing (w, h)
# Engraved stone inside the arch (white): horizontal strokes running in from the moulding, ragged lengths,
# so the walls are shaded at the edges and light behind the figure (arcana's sky lines, shortened).
COURSE_Y0 = 36.0                 # lowest stroke (below this the cloak covers the wall)
COURSE_L = (5.2, 1.4, 0.7)       # stroke length: mean, and the amplitudes of two sine wobbles
HALO = va.HALO                   # white margin around shapes over the strokes (0.7)
SPANDREL_BATS = [((9.6, 66.6), 8.8, 10.0), ((CARD_W - 9.6, 66.6), 8.8, -10.0)]   # white, on the stone

# Rose window (behind the head, as the moon was), kept deliberately plain so it doesn't merge with the
# crown: a black leaded disc with ONE ring of gold glass split by black spokes, and a black rim. The
# ring starts ~1.6 mm beyond the crown's tallest spike (r ~12.8), so a clear black band separates them.
# (v1 had 16 pointed petals from r 12.4 plus 16 white roundels: petals and spikes read as one crown.)
ROSE_C = (CX, 53.5)
ROSE_R = 17.6                    # rim outer radius (top at 71.1; the plate ends at 72.6)
ROSE_RIM = 1.0
ROSE_RING_R0 = 14.4              # gold ring from here to the rim
ROSE_SEGMENTS = 12               # a spoke points straight up, behind the crown's centre spike
ROSE_SPOKE = 1.0

# Candles in pricket stands, between the arch and the window (woodcut: outlined wax and flame, black iron)
CANDLES = [(10.2, 42.0, 6.6), (CARD_W - 10.2, 42.0, 6.6)]    # (x, wax bottom, wax height)
CANDLE_CLEAR = 1.0               # the flame's outline keeps at least this far inside the moulding (asserted)
CANDLE_W = 2.4

# The knight, in his local frame (face centre at HEAD, 1 unit = 1 mm). Cloth is flat colour:
CLOAK = BLOOD                    # the counter's red cloak, on arcana's cloak silhouette...
CLOAK_FOLD_W = (0.8, 1.3)        # ...with the counter's black tapered folds
GRIP = box(-1.4, -24.6, 1.4, -19.2)     # the counter's copper grip with two black bands, in arcana's hilt
GRIP_BANDS = (-21.0, -22.9)
COLLAR_LINING = BLOOD            # the collar's lining: red reads against the window's black leading
COLLAR_RIBS = 5                  # black ribs fanned across each wing of the collar
COLLAR_FOCUS = (-2.0, -13.0)     # the ribs fan from the neck (hidden under the gorget)...
COLLAR_FAN = (108.0, 148.0)      # ...up and out across each wing (deg)
# Spikes stand on the window's black centre, so their outlines may merge: only the gold silhouette counts.
CROWN_SPIKES = [(0.0, 15.4, 1.15), (3.0, 14.4, 1.05), (5.8, 13.0, 0.9)]    # (x, tip y, base half-width)
CROWN_HALF_W = 6.4               # band half-width
CROWN_OUTLINE = 0.55
# ---------------------------------------------------------------------------


def at(g):
    return va.at(g)


# ---- the cathedral: black stone, engraved white nave, flat gold and glass --------------

def bay():
    """The nave opening: the pointed arch above SPRING plus straight jambs below it (extends past the plate)."""
    (xl, xr), ys, rho = BAY_X, SPRING, ARCH_RHO
    left = disk((xl + rho, ys), rho, 256)            # the left flank's arc is centred to the right
    right = disk((xr - rho, ys), rho, 256)
    arch = left.intersection(right).intersection(box(-10, ys, 80, 200))
    return unary_union([arch, box(xl, ART[1] - 5, xr, ys + 0.01)])


def WALL():
    """The white wall inside the arch's gold moulding. Halos (white margins that stop the wall strokes short
    of a shape) are clipped to it, so they never bite into the black stone or the moulding."""
    return bay().buffer(-MOULDING, join_style="mitre")


def halo(cv, clip, g, margin):
    cv.paint(PAPER, g.buffer(margin).intersection(WALL()), clip)


def cathedral(cv, clip):
    x0, y0, x1, y1 = ART
    nave = bay()
    # the stone: vc.frame() left the plate white, so lay it black, then open the nave with its moulding
    cv.paint(INK, clip, clip)
    cv.paint(GOLD, nave, clip)
    wall = WALL()
    cv.paint(PAPER, wall, clip)
    courses(cv, clip, wall)
    for x in (BAY_X[0], BAY_X[1]):                   # gold capitals where the arch springs from the piers
        cw, ch = CAPITAL
        cx = x - cw / 2 + 0.4 if x < CX else x + cw / 2 - 0.4
        cv.paint(GOLD, box(cx - cw / 2, SPRING - ch / 2, cx + cw / 2, SPRING + ch / 2), clip)
    stone = vc.rrect(ART, vc.PLATE_R).difference(nave)
    for c, span, tilt in SPANDREL_BATS:
        b = vc.bat(c, span, tilt)
        assert stone.buffer(-1.0).contains(b), f"spandrel bat at {c} is too close to the arch"
        cv.paint(PAPER, b, clip)
    for x, yb, h in CANDLES:
        candle(cv, clip, x, yb, h)
    rose(cv, clip)


def keep_out():
    """Where the wall strokes must not run: the window, the candles and the cloak, each plus its halo."""
    g = [disk(ROSE_C, ROSE_R, 192).buffer(HALO), at(va.cloak_shape()).buffer(OUTLINE / 2 + HALO)]
    g += [unary_union(candle_parts(*c)).buffer(OUTLINE / 2 + HALO) for c in CANDLES]
    return unary_union(g)


def courses(cv, clip, wall):
    """Engraved shading on the nave walls: strokes running in from each side of the arch. They are cut
    around the keep-out shapes BEFORE drawing, and pieces under va.MIN_HATCH dropped, so no stub is left
    where a halo would otherwise have erased all but a sliver of a stroke."""
    a, b, c = COURSE_L
    field = wall.difference(keep_out()).buffer(-LINE / 2)
    out = []
    for y in np.arange(COURSE_Y0, ART[3] - 0.6, va.PITCH):
        row = LineString([(-10, y), (80, y)]).intersection(wall.buffer(0.3))
        segs = va.lines_of(row)
        if not segs:
            continue
        xl, xr = min(s.bounds[0] for s in segs), max(s.bounds[2] for s in segs)
        for side, ph in ((-1, 0.0), (1, 1.7)):
            L = a + b * np.sin(0.61 * y + ph) + c * np.sin(1.73 * y + 2 * ph)
            xa, xb = (xl - 1, xl + L) if side < 0 else (xr - L, xr + 1)
            pieces = va.lines_of(LineString([(xa, y), (xb, y)]).intersection(field))
            if not pieces:
                continue
            # only the piece at the moulding (one beyond a keep-out shape would float), run into the moulding
            p = min(pieces, key=lambda q: q.bounds[0]) if side < 0 else max(pieces, key=lambda q: q.bounds[2])
            pa, _, pb, _ = p.bounds
            if pb - pa < va.MIN_HATCH or (pa - xl if side < 0 else xr - pb) > 2.0:
                continue
            pa, pb = (xl - 1, pb) if side < 0 else (pa, xr + 1)
            out.append(LineString([(pa, y), (pb, y)]).buffer(LINE / 2, quad_segs=8))
    cv.paint(INK, unary_union(out).intersection(wall), clip)


def candle_parts(x, yb, h):
    """The candle's iron (stem, knop, drip pan), wax, drip and flame."""
    w = CANDLE_W
    iron = unary_union([box(x - 0.55, ART[1] - 2, x + 0.55, yb), affinity.scale(disk((x, yb - 4.2), 1, 32), 1.4, 0.8),
                        affinity.scale(disk((x, yb - 0.2), 1, 32), 2.6, 0.65)])
    wax = box(x - w / 2, yb, x + w / 2, yb + h).buffer(0.25).buffer(-0.25)
    drip = unary_union([box(x + 0.2, yb + h - 2.6, x + 0.9, yb + h), disk((x + 0.55, yb + h - 2.6), 0.35, 12)])
    tip = yb + h + 0.9
    flame = unary_union([disk((x, tip + 1.05), 1.05, 24),
                         Polygon([(x - 0.92, tip + 1.4), (x + 0.92, tip + 1.4), (x + 0.1, tip + 4.4)])])
    return iron, wax, drip, flame.buffer(0.1).buffer(-0.1)


def candle(cv, clip, x, yb, h):
    """Pricket candlestick (black iron), outlined white wax with a drip, outlined gold flame."""
    iron, wax, drip, flame = candle_parts(x, yb, h)
    clear = WALL().exterior.distance(flame.buffer(0.55 / 2))
    assert clear >= CANDLE_CLEAR, f"candle flame at x {x} is {clear:.2f} mm from the arch's moulding"
    halo(cv, clip, unary_union([iron, wax, flame]), OUTLINE / 2 + HALO)
    cv.paint(INK, iron, clip)
    va.outlined(cv, PAPER, wax.union(drip), clip, w=0.6)
    va.outlined(cv, GOLD, flame, clip, w=0.55)


def rose(cv, clip):
    c = np.array(ROSE_C)
    halo(cv, clip, disk(ROSE_C, ROSE_R, 192), HALO)                   # the wall strokes stop short of it
    # black leading, rim and centre (the centre is behind the head; black makes the gold crown stand out)
    cv.paint(INK, disk(ROSE_C, ROSE_R, 192), clip)
    ring = disk(ROSE_C, ROSE_R - ROSE_RIM, 192).difference(disk(ROSE_C, ROSE_RING_R0, 192))
    spoke = box(0, -ROSE_SPOKE / 2, ROSE_R + 1, ROSE_SPOKE / 2)
    spokes = unary_union([affinity.translate(affinity.rotate(spoke, 90 + 360 * i / ROSE_SEGMENTS, origin=(0, 0)), *c)
                          for i in range(ROSE_SEGMENTS)])
    cv.paint(GOLD, ring.difference(spokes).buffer(-0.25).buffer(0.25), clip)


# ---- the knight: the counter's cloth, arcana's steel and face, new crown and collar -------

def cloak(cv, clip):
    """Arcana's cloak silhouette in the counter's flat red, outlined (it meets the engraved wall), with
    the counter's black tapered folds along arcana's fold lines."""
    g = va.cloak_shape()
    halo(cv, clip, at(g), OUTLINE / 2 + HALO)
    va.outlined(cv, CLOAK, at(g), clip)
    for f in va.CLOAK_FOLDS:
        cv.paint(INK, at(sym(taper(f, *CLOAK_FOLD_W), 0)), clip)


def grip(cv, clip):
    """The counter's grip: copper, outlined, two black bands (replaces arcana's leather wrap)."""
    va.outlined(cv, GOLD, at(GRIP), clip, w=0.7)
    for y in GRIP_BANDS:
        cv.paint(INK, at(box(GRIP.bounds[0], y - 0.35, GRIP.bounds[2], y + 0.35)), clip)


def collar_shape():
    """The high vampire collar, local frame: rises from the shoulders behind the hair to a point beside
    each temple. Only the parts outside the hair and pauldrons show (the knight is painted over it)."""
    top = spline([(0, 5.8), (-4.0, 6.3), (-8.0, 7.3), (-11.0, 8.5), (-12.9, 9.9)], closed=False, n=60)
    out = spline([(-12.9, 9.9), (-13.7, 5.2), (-13.6, -0.5), (-12.6, -6.5), (-10.0, -12.0)], closed=False, n=80)
    half = Polygon(list(top.coords) + list(out.coords)[1:] + [(0, -12.0)]).buffer(0)
    return sym(half, 0).buffer(0.05).buffer(-0.05)


def collar(cv, clip):
    """Black outline, red lining, black ribs fanned from the neck out to the rim (they merge into it)."""
    g = collar_shape()
    va.outlined(cv, COLLAR_LINING, at(g), clip)
    F = np.array(COLLAR_FOCUS)
    ribs = []
    for th in np.radians(np.linspace(*COLLAR_FAN, COLLAR_RIBS)):
        seg = LineString([F, F + 30 * np.array([np.cos(th), np.sin(th)])]).intersection(g)
        ribs += [s.buffer(LINE / 2, quad_segs=8) for s in va.lines_of(seg) if s.length > 1.5]
    cv.paint(INK, at(sym(unary_union(ribs), 0)), clip)


def crown(cv, clip):
    """A gold circlet over the hairline, five spikes, a blood-red gem at the front."""
    hw_b = CROWN_HALF_W
    xs = np.linspace(-hw_b, hw_b, 41)
    low = 8.0 - 0.4 * (1 - (xs / hw_b) ** 2)         # the band dips at the front (seen a little from above)
    band = Polygon(list(zip(xs, low)) + list(zip(xs[::-1], (low + 2.0)[::-1]))).buffer(0.3).buffer(-0.3)
    spikes = []
    for x, tip, hw in CROWN_SPIKES:
        for sx in ((1,) if x == 0 else (1, -1)):
            base = 9.6 - 0.4 * (1 - (x / hw_b) ** 2)
            spikes.append(Polygon([(sx * x - hw, base), (sx * x + hw, base), (sx * x, tip)]))
    g = unary_union([band] + spikes)
    va.outlined(cv, GOLD, at(g), clip, w=CROWN_OUTLINE)
    cv.paint(BLOOD, at(disk((0, 8.6), 0.78, 24)), clip)


# ---- the card ------------------------------------------------------------------------

def front_regions(card):
    cv = vc.Canvas(card)
    clip = vc.frame(cv)
    cathedral(cv, clip)
    cloak(cv, clip)                  # counter: flat red cloth
    collar(cv, clip)                 # new: red lining (cloth), black stays
    va.knight_armour(cv, clip)       # arcana: outlined, hatched steel
    va.knight_head(cv, clip)         # both cards' face and hair (arcana's woodcut inking)
    va.knight_sword(cv, clip, grip=grip)    # arcana's blade and blood + the counter's banded grip
    crown(cv, clip)                  # new: flat gold, outlined
    return finish(cv, card)


def finish(cv, card):
    """vc.finish, plus the sliver clean-up for the flat red and gold too: where the black cloak or
    collar crosses the nave or moulding at a shallow angle, the leftover wedge is narrower than a bead."""
    cv.paint(PAPER, vc.mouth())
    regions = {k: g.intersection(card).buffer(0) for k, g in cv.r.items()}
    for colour in (PAPER, BLOOD, GOLD):
        regions = vc.fill_slivers(regions, colour)
    regions = vc.absorb_islands(regions)
    return {k: vc.tidy(g) for k, g in regions.items()}


def detail(regions, wh, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_, axes = plt.subplots(1, 2, figsize=(15, 9))
    for ax, sim in zip(axes, (False, True)):
        vc.draw_face(ax, regions, wh, 3, sim)
        ax.set_xlim(ART[0] - 0.5, CX + 6); ax.set_ylim(ART[1] - 0.5, ART[3] + 0.5)
        ax.set_title("left half: stone, candle, window, crown, cloak, hilt" + (" (nozzle sim)" if sim else ""),
                     fontsize=10)
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close(fig_)
    print(f"detail -> {path}")


def main():
    m = vc.mechanism()
    card = m["card"]
    regions = front_regions(card)
    back = vc.back_regions(card) if vc.BACK_ART else \
        {PAPER: card, INK: Polygon(), BLOOD: Polygon(), GOLD: Polygon()}
    vc.report(card, regions, back)
    vc.write_plate(m, regions, back, PARTS)
    vc.preview(regions, back, m["wh"], OUT / "cathedral_preview.png")
    detail(regions, m["wh"], OUT / "cathedral_detail.png")


if __name__ == "__main__":
    main()
