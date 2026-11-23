#!/usr/bin/env python3
"""
Sleeve counter: five PROTOTYPE layouts that use the art panel (80.4 x 35.3 mm under the digit row) to show
game information to players across the table, in place of a purely decorative scene.

These are previews only (drawn on the real v3.1 face, frame and wheels at true scale). Nothing here is
exported for printing: pick a direction first, then it gets built into sleeve_counter.py with its checks.

  A  flip tiles     five keyword tiles (14.7 x 34.8 mm) in bays; icon side up = the card has it
  B  dice dock      two 20 mm count dice in corner-fenced seats: copies and +1/+1 counters
  C  word strips    two half-panel strips (80 x 17.4 mm), one keyword each in 10 mm capitals
  D  count chips    numbered O31 chips that stack in a ring: the top chip is the number of copies
  E  third wheel    a built-in x1-x6 copies wheel (rim out of the bottom edge); nothing loose

A-D share one new printed part, the "rail": a 1.2 mm wide, 1.6 mm tall frame glued onto the ink border of
the art panel (the face prints face-down, so it cannot carry a raised edge itself).

Run (from the repo root):  .venv/bin/python models/sleeve-counter/info_prototypes.py
Output: models/sleeve-counter/out/prototypes/info_prototypes.png and one <letter>_<name>.png each.
"""
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

import sleeve_counter as sc

ec, vc, vd = sc.ec, sc.vc, sc.vd
rrect, disk, spline = sc.rrect, sc.disk, sc.spline
INK, ACC_A, ACC_B, PAPER = sc.INK, sc.ACC_A, sc.ACC_B, sc.PAPER
OUT = sc.OUT / "prototypes"

# ---- Parameters (mm) -------------------------------------------------------
PALETTE = "castle"              # Dark Chocolate lines, Terracotta, Ivory White, Desert Tan ground
RAIL_W, RAIL_H = 1.2, 1.6       # the glued-on rail round the art panel
FIT = 0.2                       # clearance per side, loose piece in its seat
TILE_N, TILE_T = 5, 2.4         # A: tiles per panel, thickness (0.8 proud of the rail)
DIE = 20.0                      # B: cube edge
STRIP_T = 2.4                   # C
CHIP_R, CHIP_T = 15.5, 2.4      # D
CELL_W = 35.0                   # D, E: width of the info cell at the right of the panel
WHEEL3_R, WHEEL3_PROTRUDE = 14.0, 2.0   # E: the copies wheel and how far its rim passes the bottom edge
# ---------------------------------------------------------------------------

X0, Y0, X1, Y1 = ec.ART
PW, PH = X1 - X0, Y1 - Y0
PCX, PCY = (X0 + X1) / 2, (Y0 + Y1) / 2
HX = ec.hexes(PALETTE)
PIECE = HX[ACC_B]               # loose pieces are ivory, so they stand out from the tan face
SHOWN = (4, 4)                  # power / toughness on the wheels in every preview


# ---- small drawing kit -----------------------------------------------------------------------

def word(s, c, cap, max_w=None, squeeze=0.8):
    """Bold capitals as a shapely shape, cap height `cap`, centred on c (a stand-in for Bahnschrift)."""
    tp = TextPath((0, 0), s, size=10, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    g = Polygon()
    for p in sorted((Polygon(p).buffer(0) for p in tp.to_polygons() if len(p) >= 3), key=lambda p: -p.area):
        g = g.symmetric_difference(p)
    k = cap / 7.29
    g = affinity.scale(g, k * squeeze, k, origin=(0, 0))
    b = g.bounds
    if max_w and b[2] - b[0] > max_w:
        g = affinity.scale(g, max_w / (b[2] - b[0]), 1.0, origin=(0, 0))
        b = g.bounds
    return affinity.translate(g, c[0] - (b[0] + b[2]) / 2, c[1] - cap / 2)


def numeral(v, c, h):
    """A wheel digit (the real outlines) scaled to height h."""
    return affinity.translate(affinity.scale(ec.digit(v, (0, 0)), h / sc.DIGIT_H, h / sc.DIGIT_H, origin=(0, 0)), *c)


def times(c, s):
    """A multiplication sign s across."""
    bar = box(-s / 2, -s * 0.13, s / 2, s * 0.13)
    return affinity.translate(unary_union([affinity.rotate(bar, a, origin=(0, 0)) for a in (45, -45)]), *c)


def lined(g, fill, w=0.7):
    """Woodcut style: an ink outline straddling the edge of g, filled."""
    return [(INK, g.buffer(w / 2, join_style="round")), (fill, g.buffer(-w / 2, join_style="round"))]


def icon(name, c, s):
    """A keyword icon about s across, as (slot, shape) layers to paint in order."""
    u = lambda pts: Polygon([(c[0] + s * x, c[1] + s * y) for x, y in pts])
    at = lambda x, y: (c[0] + s * x, c[1] + s * y)
    if name == "flying":          # wing
        g = u([(-0.5, -0.12), (-0.38, 0.22), (-0.1, 0.42), (0.3, 0.5), (0.5, 0.44), (0.3, 0.3), (0.46, 0.2),
               (0.24, 0.08), (0.38, -0.06), (0.14, -0.14), (0.24, -0.3), (-0.02, -0.3), (0.02, -0.46), (-0.3, -0.36)])
        g = g.buffer(0.06 * s).buffer(-0.06 * s)
        return lined(g, ACC_B) + [(INK, LineString([at(-0.32, 0.02), at(0.06, 0.26)]).buffer(0.3))]
    if name == "haste":           # lightning bolt
        return lined(u([(0.12, 0.5), (-0.34, -0.04), (-0.06, -0.04), (-0.2, -0.5), (0.34, 0.1), (0.04, 0.1), (0.3, 0.5)]),
                     ACC_A)
    if name == "lifelink":        # heart
        t = np.linspace(0, 2 * np.pi, 80)
        x = 16 * np.sin(t) ** 3
        y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
        return lined(Polygon(np.c_[c[0] + s * x / 34, c[1] + s * (y + 2.5) / 34]), ACC_A)
    if name == "deathtouch":      # skull
        g = unary_union([disk(at(0, 0.1), 0.4 * s, 48), box(*at(-0.2, -0.46), *at(0.2, -0.1))])
        g = g.buffer(0.05 * s).buffer(-0.05 * s)
        return lined(g, ACC_B) + [(INK, unary_union(
            [disk(at(-0.17, 0.06), 0.11 * s, 24), disk(at(0.17, 0.06), 0.11 * s, 24),
             u([(0, -0.06), (-0.06, -0.19), (0.06, -0.19)]),
             box(*at(-0.03, -0.46), *at(0.03, -0.27))]))]
    if name == "vigilance":       # eye
        lens = disk(at(0, -0.42), 0.68 * s, 96).intersection(disk(at(0, 0.42), 0.68 * s, 96))
        return lined(lens, ACC_B) + [(INK, disk(c, 0.2 * s, 32)), (ACC_A, disk(c, 0.12 * s, 32))]
    if name == "trample":         # paw print
        g = unary_union([affinity.scale(disk(at(0, -0.16), 0.26 * s, 40), 1.15, 0.9)] +
                        [disk(at(x, y), 0.105 * s, 24) for x, y in ((-0.34, 0.1), (-0.13, 0.33), (0.13, 0.33), (0.34, 0.1))])
        return [(INK, g)]
    if name == "first strike":    # sword
        blade, hilt, grip = ec.sword(c, s)
        return lined(blade, ACC_B, 0.6) + lined(hilt, ACC_A, 0.6) + [(INK, grip)]
    if name == "defender":        # shield
        sh = ec.shield(c, s * 0.72, s)
        return lined(sh, ACC_B) + [(ACC_A, sh.buffer(-1.4, join_style="round"))]
    if name == "copies":          # a fan of three cards
        out = []
        for a, dx in ((16, -0.14), (0, 0.0), (-16, 0.14)):
            g = affinity.rotate(rrect((c[0] - 0.24 * s, c[1] - 0.36 * s, c[0] + 0.24 * s, c[1] + 0.36 * s), 0.07 * s),
                                a, origin=at(0, -0.6))
            out += lined(affinity.translate(g, dx * s, 0), ACC_B, 0.6)
        return out
    if name == "counters":        # +1/+1: a plus in a hexagon
        hexa = Polygon([at(0.46 * math.cos(math.radians(a)), 0.46 * math.sin(math.radians(a))) for a in range(30, 390, 60)])
        plus = unary_union([box(*at(-0.24, -0.07), *at(0.24, 0.07)), box(*at(-0.07, -0.24), *at(0.07, 0.24))])
        return lined(hexa, ACC_A) + [(ACC_B, plus)]
    raise KeyError(name)


def stamp(ax, layers, clip=None):
    for k, g in layers:
        g = g if clip is None else g.intersection(clip)
        vd.draw(ax, g, HX[k] if isinstance(k, int) else k)


def piece(ax, g, colour=None, lift=0.7):
    """A loose piece seen from above: drop shadow, body, a lighter top edge."""
    vd.draw(ax, affinity.translate(g, lift, -lift), "#000000", alpha=0.28)
    vd.draw(ax, g, ec.shade(colour or PIECE, 0.86))
    vd.draw(ax, g.buffer(-0.35, join_style="round"), colour or PIECE)


def scalloped(c, r, n=18, depth=0.55):
    t = np.linspace(0, 2 * np.pi, n * 16, endpoint=False)
    rr = r - depth * (0.5 + 0.5 * np.cos(n * t))
    return Polygon(np.c_[c[0] + rr * np.cos(t), c[1] + rr * np.sin(t)])


def rail_shape(cells=()):
    """The glued-on rail: a frame on the panel's ink border, plus any ribs."""
    panel = rrect(ec.ART, ec.PLATE_R)
    return unary_union([panel.buffer(RAIL_W, join_style="mitre").difference(panel), *cells])


def draw_rail(ax, g):
    vd.draw(ax, affinity.translate(g, 0.4, -0.4), "#000000", alpha=0.25)
    vd.draw(ax, g, HX[INK])
    vd.draw(ax, g.buffer(-0.4), "#6a4c3b")


def face(panel_art=None, scene=None, scene_clip=None):
    """The v3.1 face with an empty (paper) art panel; optionally a scene clipped to part of it."""
    card = M["card"]
    cv = vc.Canvas(card)
    art = sc.frame(cv)
    if scene:
        keep = ec.AC
        b = scene_clip.bounds
        ec.AC = ((b[0] + b[2]) / 2, PCY)
        try:
            sc.SCENES[scene](cv, art.intersection(scene_clip))
        finally:
            ec.AC = keep
        cv.paint(INK, box(b[2], Y0, b[2] + ec.RULE, Y1), art)
    if panel_art:
        panel_art(cv, art)
    return ec.finish(cv, card)


def base(ax, regions, title):
    sc.draw_base(ax, M, regions, HX, SHOWN)
    ax.set_title(title, fontsize=11, loc="left")


def note(ax, text):
    ax.text(0.0, 1.0, text, transform=ax.transAxes, va="top", ha="left", fontsize=8.6, linespacing=1.35, wrap=True)


def elevation(ax, y0, stacks, label):
    """Side view at true scale: the block lying on the table (9.2 mm) with what stands on its face.
    stacks = [(x0, x1, height, colour)], heights above the face."""
    T = sc.THICK
    vd.draw(ax, box(0, y0, sc.BLOCK_W, y0 + T), HX[PAPER])
    vd.draw(ax, box(0, y0 + T - 0.4, sc.BLOCK_W, y0 + T), HX[INK])
    vd.draw(ax, box(sc.SIDE_WALL, y0 + sc.BACK_T + 0.25, sc.BLOCK_W - sc.SIDE_WALL, y0 + sc.BACK_T + 0.95), "#1f5fa8")
    for x0, x1, h, colour in stacks:
        vd.draw(ax, box(x0, y0 + T, x1, y0 + T + h), colour)
        ax.plot([x0, x1, x1, x0, x0], [y0 + T, y0 + T, y0 + T + h, y0 + T + h, y0 + T], color="#3a2d25", lw=0.5)
    ax.text(sc.BLOCK_W / 2, y0 - 1.2, label, ha="center", va="top", fontsize=8)


def sheet(ax):
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.set_facecolor("#e9e6e0")
    ax.set_xlim(-4.5, sc.BLOCK_W + 4.5); ax.set_ylim(-6, 72)


# ---- A: flip tiles -----------------------------------------------------------------------------

def tile_bays():
    w = (PW - (TILE_N - 1) * RAIL_W) / TILE_N
    return [box(X0 + i * (w + RAIL_W), Y0, X0 + i * (w + RAIL_W) + w, Y1) for i in range(TILE_N)]


def tile(ax, bay, name, origin=None):
    g = rrect(bay.buffer(-FIT).bounds, 1.0)
    if origin:
        g = affinity.translate(g, origin[0] - g.bounds[0], origin[1] - g.bounds[1])
    c = g.centroid.coords[0]
    if name is None:                                        # plain side up: the tile's body colour
        piece(ax, g, HX[PAPER])
        stamp(ax, [(ec.shade(HX[PAPER], 0.9), Polygon([(c[0] - 1.6, c[1]), (c[0], c[1] + 2.6), (c[0] + 1.6, c[1]),
                                                        (c[0], c[1] - 2.6)]))])
        return
    piece(ax, g)
    stamp(ax, lined(g.buffer(-1.5, join_style="round"), ACC_B, 0.55), g)
    stamp(ax, icon(name, c, 11.5))
    for dy in (-13.2, 13.2):
        stamp(ax, [(INK, Polygon([(c[0] - 1.1, c[1] + dy), (c[0], c[1] + dy + 1.6), (c[0] + 1.1, c[1] + dy),
                                  (c[0], c[1] + dy - 1.6)]))])


def proto_a(ax, ax2):
    bays = tile_bays()
    ribs = [box(b.bounds[2], Y0, b.bounds[2] + RAIL_W, Y1) for b in bays[:-1]]
    base(ax, face(), "A  Flip tiles: one icon per keyword")
    draw_rail(ax, rail_shape(ribs))
    for bay, name in zip(bays, ("flying", "lifelink", None, "haste", None)):
        tile(ax, bay, name)
    sheet(ax2)
    w = bays[0].bounds[2] - bays[0].bounds[0]
    for i, name in enumerate(("deathtouch", "vigilance", "trample", "first strike", "defender")):
        tile(ax2, bays[0], name, origin=(1.0 + i * (w + 1.6), 34.0))
    ax2.text(sc.BLOCK_W / 2, 70.6, "more tiles from the set (each 14.7 x 34.8 x 2.4 mm, plain on the back)", ha="center",
             va="center", fontsize=8)
    elevation(ax2, 6, [(X0 - RAIL_W, X1 + RAIL_W, RAIL_H, HX[INK])] +
              [(b.bounds[0] + FIT, b.bounds[2] - FIT, TILE_T, PIECE) for b in bays],
              f"side view: rail {RAIL_H} mm, tiles {TILE_T} mm (0.8 proud, so a nail can lift one)")


# ---- B: dice dock --------------------------------------------------------------------------------

def proto_b(ax, ax2):
    seats = {"copies": (PCX - 13.0, PCY), "counters": (PCX + 13.0, PCY)}

    def art(cv, clip):
        for name, (x, y) in seats.items():
            side = -1 if name == "copies" else 1
            for k, g in icon(name, (x + side * 19.4, y), 11.0):
                cv.paint(k, g, clip)

    corners = []
    for x, y in seats.values():
        h = DIE / 2 + FIT
        ring = box(x - h - RAIL_W, y - h - RAIL_W, x + h + RAIL_W, y + h + RAIL_W).difference(box(x - h, y - h, x + h, y + h))
        corners.append(ring.difference(unary_union([box(x - h + 4, y - 30, x + h - 4, y + 30),
                                                    box(x - 30, y - h + 4, x + 30, y + h - 4)])))
    base(ax, face(art), "B  Dice dock: copies and +1/+1 counters")
    draw_rail(ax, rail_shape(corners))
    for (x, y), v in zip(seats.values(), (3, 2)):
        g = rrect((x - DIE / 2, y - DIE / 2, x + DIE / 2, y + DIE / 2), 2.2)
        piece(ax, g, lift=1.6)
        stamp(ax, [(INK, numeral(v, (x, y), 14.0))])
    sheet(ax2)
    for i, v in enumerate((1, 2, 3, 4, 5, 6)):
        x, y = 8.5 + i * 13.4, 53.0
        g = rrect((x - 6, y - 6, x + 6, y + 6), 1.4)
        piece(ax2, g, lift=0.5)
        stamp(ax2, [(INK, numeral(v, (x, y), 8.4))])
    ax2.text(sc.BLOCK_W / 2, 66.5, "the six faces of a 20 mm die: 14 mm numerals, the size of the P/T digits",
             ha="center", va="center", fontsize=8)
    ax2.text(sc.BLOCK_W / 2, 41.5, "(drawn at 60 %)", ha="center", va="center", fontsize=7.5, color="#555555")
    elevation(ax2, 6, [(X0 - RAIL_W, X1 + RAIL_W, RAIL_H, HX[INK])] +
              [(x - DIE / 2, x + DIE / 2, DIE, PIECE) for x, _ in seats.values()],
              "side view: the dice stand 20 mm above the face, readable from a low angle")


# ---- C: word strips ------------------------------------------------------------------------------

def strip(ax, y, text, name, x=X0, w=PW):
    h = (PH - RAIL_W) / 2
    g = rrect((x + FIT, y + FIT, x + w - FIT, y + h - FIT), 1.0)
    piece(ax, g)
    c = (x + 9.5, y + h / 2)
    stamp(ax, [(INK, box(x + 18.2, y + 2.4, x + 18.9, y + h - 2.4))])
    if name:
        stamp(ax, icon(name, c, 12.0))
    stamp(ax, [(INK, word(text, (x + 18.9 + (w - 18.9) / 2, y + h / 2), 10.0, max_w=w - 24.5))])


def proto_c(ax, ax2):
    h = (PH - RAIL_W) / 2
    rib = box(X0, Y0 + h, X1, Y0 + h + RAIL_W)
    base(ax, face(), "C  Word strips: keywords in 10 mm capitals")
    draw_rail(ax, rail_shape([rib]))
    strip(ax, Y0 + h + RAIL_W, "FLYING", "flying")
    strip(ax, Y0, "LIFELINK", "lifelink")
    sheet(ax2)
    for i, (text, name) in enumerate((("DEATHTOUCH", "deathtouch"), ("TRAMPLE", "trample"))):
        strip(ax2, 52.0 - i * (h + 1.5), text, name)
    ax2.text(sc.BLOCK_W / 2, 70.6, "more strips (80.0 x 16.6 x 2.4 mm); one full-height plaque also fits the rail",
             ha="center", va="center", fontsize=8)
    elevation(ax2, 6, [(X0 - RAIL_W, X1 + RAIL_W, RAIL_H, HX[INK]), (X0 + FIT, X1 - FIT, STRIP_T, PIECE)],
              f"side view: rail {RAIL_H} mm, strips {STRIP_T} mm")


# ---- D: count chips ------------------------------------------------------------------------------

def chip(ax, c, v, lift=0.7, r=CHIP_R):
    k = r / CHIP_R
    g = scalloped(c, r)
    piece(ax, g, lift=lift)
    stamp(ax, lined(disk(c, r - 2.6 * k, 64), ACC_B, 0.6 * k))
    stamp(ax, [(ACC_A, times((c[0] - 6.8 * k, c[1] - 1.5 * k), 5.0 * k)), (INK, numeral(v, (c[0] + 2.6 * k, c[1]), 14.0 * k))])


def proto_d(ax, ax2):
    cell = box(X1 - CELL_W, Y0, X1, Y1)
    c = ((cell.bounds[0] + X1) / 2, PCY)
    ring = disk(c, CHIP_R + FIT + RAIL_W, 96).difference(disk(c, CHIP_R + FIT, 96))

    def art(cv, clip):
        cv.paint(INK, disk(c, CHIP_R + FIT + RAIL_W, 96), clip)
        cv.paint(PAPER, disk(c, CHIP_R + FIT, 96), clip)
        cv.paint(INK, numeral(1, c, 14.0), clip)                 # no chips on = one copy

    base(ax, face(art, scene="castle", scene_clip=box(X0, Y0, X1 - CELL_W - ec.RULE, Y1)),
         "D  Count chips: the stack is the number of copies")
    draw_rail(ax, ring)
    chip(ax, c, 2, lift=0.5)
    chip(ax, c, 3, lift=1.1)
    sheet(ax2)
    for i, v in enumerate((2, 3, 4, 5, 6)):
        chip(ax2, (9.5 + i * 16.3, 53.0), v, lift=0.5, r=7.6)
    ax2.text(sc.BLOCK_W / 2, 66.5, "chips 2 to 6 (O31 x 2.4 mm, each keyed into the one below); 1 is printed on the face",
             ha="center", va="center", fontsize=8)
    ax2.text(sc.BLOCK_W / 2, 41.5, "(drawn at 49 %)", ha="center", va="center", fontsize=7.5, color="#555555")
    elevation(ax2, 6, [(c[0] - CHIP_R - RAIL_W, c[0] + CHIP_R + RAIL_W, RAIL_H, HX[INK])] +
              [(c[0] - CHIP_R, c[0] + CHIP_R, CHIP_T * n, PIECE) for n in (2, 1)],
              "side view with chips 2 and 3 on: the pile's height shows the count as well")


# ---- E: third wheel ------------------------------------------------------------------------------

def proto_e(ax, ax2):
    cell = box(X1 - CELL_W, Y0, X1, Y1)
    wc = (sc.BLOCK_W - 2.0 - ec.WHEEL_CLR - WHEEL3_R, WHEEL3_R - WHEEL3_PROTRUDE)   # 2 mm of side wall
    gap = Point(*wc).distance(Point(*ec.WHEEL_C[ec.FRONT_WHEEL])) - (ec.R_WHEEL + ec.WHEEL_CLR) - (WHEEL3_R + ec.WHEEL_CLR)
    assert gap >= ec.WELL_WALL, f"the copies wheel's cavity is {gap:.1f} mm from the power cavity"
    r_ring, num_h = 8.4, 8.5
    assert 2 * (r_ring - num_h / 2) * math.tan(math.radians(30)) >= 0.54 * num_h, "the numerals collide at the hub"
    assert r_ring + num_h / 2 <= WHEEL3_R - ec.WHEEL_RIM - 0.3, "the numerals run into the rim"
    win_c = (wc[0], wc[1] + r_ring)
    win = rrect((win_c[0] - 4.2, win_c[1] - 5.2, win_c[0] + 4.2, win_c[1] + 5.2), 1.2)

    def art(cv, clip):
        cv.paint(INK, win.buffer(1.6, join_style="round"), clip)
        cv.paint(PAPER, win.buffer(0.9, join_style="round"), clip)
        cv.paint(ACC_A, times((win_c[0] - 10.2, win_c[1] - 1.0), 6.4).buffer(0.25), clip)
        for k, g in icon("copies", (win_c[0] + 0.5, Y1 - 4.6), 7.5):
            cv.paint(k, g, clip)

    regions = face(art, scene="sun", scene_clip=box(X0, Y0, X1 - CELL_W - ec.RULE, Y1))
    wheel = scalloped(wc, WHEEL3_R, n=20, depth=0.7)
    vd.draw(ax, wheel, ec.shade(HX[PAPER], 0.93))               # under the face: only the rim shows below the edge
    base(ax, regions, "E  Third wheel: copies x1 to x6, nothing loose")
    vd.draw(ax, win, ec.shade(HX[PAPER], 0.93))
    stamp(ax, [(INK, numeral(3, win_c, num_h))])
    ax.set_ylim(-WHEEL3_PROTRUDE - 2.5, ax.get_ylim()[1])
    sheet(ax2)
    # the wheel on its own, at 150 %
    big = lambda g: affinity.translate(affinity.scale(g, 1.5, 1.5, origin=wc), sc.BLOCK_W / 2 - wc[0], 50.0 - wc[1])
    vd.draw(ax2, big(wheel), ec.shade(HX[PAPER], 0.86))
    vd.draw(ax2, big(wheel.buffer(-0.35)), ec.shade(HX[PAPER], 0.95))
    for i in range(6):
        d = affinity.rotate(numeral(i + 1, (wc[0], wc[1] + r_ring), num_h), -60 * i, origin=wc)
        vd.draw(ax2, big(d), HX[INK])
    vd.draw(ax2, big(disk(wc, 1.6, 24)), HX[INK])
    ax2.text(sc.BLOCK_W / 2, 26.0, f"the copies wheel at 150 %: O{2 * WHEEL3_R:.0f} x 1.6 mm, six {num_h} mm numerals, beside the "
             f"power wheel\n({gap:.1f} mm of wall between their cavities; block stays 9.2 mm thick)", ha="center",
             va="center", fontsize=8)
    elevation(ax2, 6, [], "side view: unchanged, flat face")


PROTOS = (("a_flip_tiles", proto_a,
           "Five keyword tiles sit in bays. Icon side up means the card has that\n"
           "keyword; flip it to the plain side to switch it off. Tiles never leave\n"
           "the counter in play. 11.5 mm icons. + rail and 5 tiles per counter."),
          ("b_dice_dock", proto_b,
           "Two custom 20 mm dice in corner-fenced seats, labelled by icons printed\n"
           "on the face: a card fan (copies in the sleeve) and a +1/+1 hexagon.\n"
           "Numerals as large as the P/T digits. The dice are loose when carried."),
          ("c_word_strips", proto_c,
           "Two half-panel strips, each one keyword spelled out with its icon.\n"
           "No symbols to learn; most legible at distance. Two keywords at a time;\n"
           "a full-height plaque (token name, 'x3', a scene) fits the same rail."),
          ("d_count_chips", proto_d,
           "Numbered chips stack in a ring; the top chip reads the number of copies\n"
           "and the pile grows with it. With none on, the face shows 1. A cropped\n"
           "scene keeps the left 44 mm of the panel."),
          ("e_third_wheel", proto_e,
           "A small third wheel under the face, turned by its rim at the bottom\n"
           "edge. Same build style as the P/T wheels, no extra thickness, nothing\n"
           "to lose. Count only (no keywords); 8.5 mm numerals."))


def main():
    global M
    M = ec.mechanism()
    OUT.mkdir(parents=True, exist_ok=True)
    hgt = 6.2 * (sc.FOOT + 95.5) / (sc.BLOCK_W + 2 * ec.PROTRUDE + 4)
    ratios = [hgt, 6.2 * 78 / (sc.BLOCK_W + 9), 1.0]
    fig_, axes = plt.subplots(3, 5, figsize=(31, sum(ratios) + 1.0), gridspec_kw=dict(height_ratios=ratios))
    for col, (name, fn, text) in enumerate(PROTOS):
        fn(axes[0, col], axes[1, col])
        axes[2, col].axis("off")
        note(axes[2, col], text)
        one, (a1, a2) = plt.subplots(2, 1, figsize=(6.4, ratios[0] + ratios[1] + 0.6), gridspec_kw=dict(height_ratios=ratios[:2]))
        fn(a1, a2)
        one.tight_layout()
        one.savefig(OUT / f"{name}.png", dpi=120)
        plt.close(one)
    fig_.tight_layout()
    fig_.savefig(OUT / "info_prototypes.png", dpi=110)
    plt.close(fig_)
    print(f"previews -> {OUT}")


if __name__ == "__main__":
    main()
