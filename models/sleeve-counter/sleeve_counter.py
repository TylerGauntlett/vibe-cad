#!/usr/bin/env python3
"""
Sleeve counter: a power/toughness counter that plugs onto a real, sleeved card. The card slides into a
slot in the back of the block. The block covers the card from its bottom edge up to the art and hangs
below it; the card's name and art stay in view. On its face: power and toughness (0-9 each, on separate
wheels) in a row of five cells along the top (sword, power, slash, toughness, shield), and a woodcut
scene below, in the style and palettes of the emblem counter. Five faces: sun, moon, tree, flame,
mountain.

Spec: see README.md in this folder.

The mechanism is the emblem counter's (models/emblem-counter, imported and re-configured for this
outline): two overlapping wheels on two levels, power in front with its rim out of the left edge,
toughness behind with its rim out of the right edge. Here the windows sit ABOVE the wheels' centres
(`layout_up`), so the digits are over the card's text box and the lower halves of the wheels are behind
the scene. The digit size sets the block: wheels are 4.2 x the digit height across, the block is that
plus 4.4 mm tall, and it must be wide enough for the toughness well to miss the power wheel's cavity
(72 mm for 12 mm digits, 78 for 13, 84 for 14).

Parts (six, printed flat, no supports; z from the back face when assembled):
  back      0.0-1.2 plate (art inlaid), 8 mm taller than the block as a lead-in lip;
            1.2-2.4 a U-shaped rim (two side walls and the foot) that leaves the card slot open at the top
  tray      2.4-3.2 the slot's roof, 3.2-5.2 spacer round the toughness cavity, pin, tongue
  toughness 3.2-4.8 wheel (face-down print)
  divider   5.2-6.0 plate between the wheels, power pin on top
  power     6.0-7.6 wheel (face-down print)
  front     6.0-8.0 spacer + 8.0-9.2 face plate (face-down print, art inlaid)

Run (from the repo root):
    .venv\\Scripts\\python.exe models\\sleeve-counter\\sleeve_counter.py [design ...]
Trial sizes: env SLEEVE_DIGIT_H, SLEEVE_BLOCK_W, SLEEVE_TILT override the parameters; SLEEVE_OUT the folder.
Outputs (millimetres) go to models\\sleeve-counter\\out\\
    <design>/<object>_<n>_<slot>.stl   parts laid out as on the plate; load as ONE object (--assemble)
    <design>/slice_args.txt            the matching slice_bambu.py arguments
    designs_preview.png                the five counters, each on a card
    <design>_preview.png               one face at larger scale, with a nozzle simulation
    parts_preview.png                  back, tray, divider, front underside, and a section through the slot
"""
import importlib.util
import math
import os
import sys
from pathlib import Path

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("SLEEVE_OUT", HERE / "out"))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# The wheels, windows, tongue, drawing helpers, palettes and plate writer come from the emblem counter.
ec = _load("emblem_counter", HERE.parent / "emblem-counter" / "emblem_counter.py")
vc, vt, vd, va = ec.vc, ec.vt, ec.vd, ec.va
rrect, disk, spline, taper = ec.rrect, ec.disk, ec.spline, ec.taper
INK, ACC_A, ACC_B, PAPER = ec.INK, ec.ACC_A, ec.ACC_B, ec.PAPER
FRONT_WHEEL, REAR_WHEEL = ec.FRONT_WHEEL, ec.REAR_WHEEL

# ---- Parameters (mm) -------------------------------------------------------
# The card. A sleeve is 66-67 mm wide and about 0.6 mm thick with a card in it (0.9 double-sleeved).
SLOT_W = 68.0                   # slot width: a 67 mm sleeve with 0.5 mm each side
SLOT_T = 1.2                    # slot depth, front to back
COVER = 40.0                    # how far up the sleeve the block reaches: to the foot of a card's art

# Digit height and the block width it needs (see the docstring). The block is wider than the sleeve by
# BLOCK_W - 67 mm in all.
DIGIT_H = float(os.environ.get("SLEEVE_DIGIT_H", 14.0))
BLOCK_W = float(os.environ.get("SLEEVE_BLOCK_W", 84.0))
WIN_TILT = float(os.environ.get("SLEEVE_TILT", 15.0))   # each window sits this far outward of straight above its wheel's centre
SIDE_WALL = (BLOCK_W - SLOT_W) / 2
TOP_WALL = 2.0                  # spacer over the cavities
BOTTOM_WALL = 2.0               # spacer under them

BACK_T = 1.2                    # plate behind the card
ROOF_T = 0.8                    # the slot's roof = the tray's base
LIP = 8.0                       # the back plate stands this far above the block: lay the card on it and slide down
ENTRY = 0.6                     # 45-degree chamfer on the roof's top edge, so a sleeve doesn't catch
PEG_W, PEG_H, PEG_CLR = 1.2, 0.6, 0.2    # ridges on the foot that locate the tray (groove = the roof's thickness)
PEG_MARGIN = 1.2                # ridge edge -> the toughness cavity above the roof
SCENE_AH = 15.2                 # the scenes are drawn for a panel this tall (half height) and scaled to fit
SCENE_AW = 37.5                 # ... and reach this far either side of its centre
PLATE_GAP = 6.0
BED = 250.0                     # usable bed width for the plate layout
# ---------------------------------------------------------------------------


def layout_up():
    """The emblem counter's layout turned over: each window sits ABOVE its wheel's centre (WIN_TILT outward
    of straight up), so the digit row is at the top of the block, over the card's text box, and the lower
    halves of the wheels fill the block below it. Both wheels sit at the same height."""
    ang = {name: np.radians(90 - side * WIN_TILT) for name, side in ec.WHEELS}

    def ring(a):
        for r in np.arange(DIGIT_H, 3 * DIGIT_H, 0.05):
            p0 = r * np.array([np.cos(a), np.sin(a)])
            win = ec.win_box(p0).buffer(0.3)
            if all(not affinity.rotate(ec.digit(v, p0), s, origin=(0, 0)).intersects(win)
                   for v in ec.VALUES for s in (-ec.STEP, ec.STEP)):
                return float(r)
        raise RuntimeError("no ring radius found")

    r = max(ring(a) for a in ang.values())
    p0 = {n: r * np.array([np.cos(a), np.sin(a)]) for n, a in ang.items()}
    corner = max(np.hypot(*np.array(ec.win_box(p).exterior.coords).T).max() for p in p0.values())
    R = corner + ec.CHANNEL_MARGIN + ec.WHEEL_RIM + ec.GRIP_DEPTH
    cy = R + ec.WHEEL_CLR + BOTTOM_WALL
    c = {name: np.array([R - ec.PROTRUDE if side < 0 else BLOCK_W + ec.PROTRUDE - R, cy]) for name, side in ec.WHEELS}
    wall = Point(*c[FRONT_WHEEL]).distance(ec.win_box(c[REAR_WHEEL] + p0[REAR_WHEEL])) - (R + ec.WHEEL_CLR)
    assert wall >= ec.WELL_WALL, f"the toughness well is {wall:.2f} mm from the power cavity: widen the block"
    return r, R, c, {n: c[n] + p0[n] for n in c}


ec.layout = layout_up
ec.configure(CARD_W=BLOCK_W, CARD_H=200.0, DIGIT_H=DIGIT_H, WIN_TILT=WIN_TILT, BASE_T=ROOF_T,
             CACHE=HERE / "text_cache.json")
BLOCK_H = math.ceil(max(ec.WHEEL_C[FRONT_WHEEL][1] + ec.R_WHEEL + ec.WHEEL_CLR + TOP_WALL,
                        ec.WIN_C[FRONT_WHEEL][1] + ec.WIN_WH[1] / 2 + ec.BEVEL + ec.WIN_MAT + ec.EDGE) * 10) / 10
ec.configure(CARD_H=BLOCK_H)
# Plates: the display (the digit row) along the top, down to the foot of the toughness well's bevel; the art
# panel below it. The scenes are drawn in their own units about the panel's centre and scaled by K to fit.
ec.DISPLAY = (ec.EDGE, ec.face_opening(REAR_WHEEL).bounds[1] - ec.WIN_MAT, BLOCK_W - ec.EDGE, BLOCK_H - ec.EDGE)
ec.ART = (ec.EDGE, ec.EDGE, BLOCK_W - ec.EDGE, ec.DISPLAY[1] - ec.RULE)
ec.AC = ((ec.ART[0] + ec.ART[2]) / 2, (ec.ART[1] + ec.ART[3]) / 2)
K = (ec.ART[3] - ec.ART[1]) / 2 / SCENE_AH
ec.AW, ec.AH = (ec.ART[2] - ec.ART[0]) / 2 / K, SCENE_AH
assert ec.AW <= SCENE_AW, f"the scenes are too narrow for this panel ({ec.AW:.1f} > {SCENE_AW} scene units)"
ec.L = lambda g: affinity.translate(affinity.scale(g, K, K, origin=(0, 0)), *ec.AC)
FOOT = BLOCK_H - COVER          # the part of the block below the card
BODY_Z = BACK_T + SLOT_T        # where the tray starts
THICK = BODY_Z + ec.THICK
CX = BLOCK_W / 2
AW, AH = ec.AW, ec.AH           # the art panel's half width and half height, in scene units
outlined, ink, hatch = ec.outlined, ec.ink, ec.hatch


# ---- the five panels (scene units: origin at the art panel's centre, +-AW by +-15.2) ------------

def scene_sun(cv, clip):
    """A sun rising between hills, nine rays."""
    c, r0 = (0.0, -8.6), 8.4
    for i in range(-4, 5):
        if i % 2 == 0:
            g, fill = Polygon([(-1.7, r0 + 1.5), (1.7, r0 + 1.5), (0, r0 + 15.0)]), ACC_B
        else:
            t = np.linspace(0, 1, 9)
            g = taper(list(zip(1.2 * np.sin(2 * np.pi * t) * (1 - 0.4 * t), r0 + 1.6 + 10.5 * t)), 2.5, 0.8)
            fill = ACC_A
        outlined(cv, clip, fill, affinity.translate(affinity.rotate(g, 20.0 * i, origin=(0, 0)), *c), w=0.6)
    outlined(cv, clip, ACC_B, disk(c, r0, 96), w=0.8)
    ink(cv, clip, disk(c, 5.8, 64).difference(disk(c, 5.2, 64)))
    ec.cloud(cv, clip, [(-29.5, 8.4, 2.5), (-25.6, 9.9, 3.2), (-21.0, 8.7, 2.4)], 6.9)
    ec.cloud(cv, clip, [(21.4, 6.0, 2.4), (25.6, 7.7, 3.3), (30.0, 6.4, 2.6)], 4.5)
    far = spline([(-40, -22), (-40, -8.6), (-28, -6.2), (-16, -8.4), (-5, -12.4), (2, -22)])
    outlined(cv, clip, PAPER, far, halo=ec.HALO)
    ink(cv, clip, hatch(va.inside(far).intersection(box(-40, -22, -9, -8.8)), 12, min_len=2.4))
    mid = spline([(-2, -22), (5, -12.6), (16, -8.2), (27, -6.6), (40, -9.0), (40, -22)])
    outlined(cv, clip, PAPER, mid, halo=ec.HALO)
    ink(cv, clip, hatch(va.inside(mid).intersection(box(11, -22, 40, -9.0)), -12, min_len=2.4))
    near = spline([(-40, -22), (-40, -13.4), (-19, -12.0), (0, -13.6), (19, -12.4), (40, -14.0), (40, -22)])
    ink(cv, clip, near.buffer(ec.OUTLINE / 2 + ec.HALO), PAPER)
    ink(cv, clip, near)
    ink(cv, clip, taper([(-28, -14.6), (-13, -13.9), (2, -15.4), (17, -14.5), (29, -15.6)], 0.6, 0.6), PAPER)


def scene_moon(cv, clip):
    """A crescent holding a star, stars to either side, over a bank of cloud."""
    ec.sky(cv, clip, -AH + 0.6, AH, pitch=1.5, full=True)
    moon = disk((-4.6, 2.2), 10.2, 128).difference(disk((0.2, 3.7), 8.4, 128)).buffer(0.4).buffer(-0.4)
    outlined(cv, clip, ACC_A, moon, w=0.8, halo=0.9)
    big = unary_union([ec.star((2.6, 3.1), 4.6, 1.4), ec.star((2.6, 3.1), 2.9, 1.4, rot=45)])
    outlined(cv, clip, ACC_A, big, w=0.6, halo=0.8)
    for x, y, r in ((-25.5, 8.5, 3.3), (-17.0, -1.5, 2.6), (-29.5, -2.5, 2.5), (17.5, 9.5, 3.2), (27.5, 4.0, 3.5),
                    (15.5, -1.0, 2.6), (-13.5, 11.5, 2.4)):
        outlined(cv, clip, ACC_A, ec.star((x, y), r, r * 0.36), w=0.5, halo=0.8)
    ec.cloud(cv, clip, [(x, -6.5 - 1.7 * (i % 2 == 0), 4.2 - 0.6 * (i % 2 == 0)) for i, x in enumerate(np.arange(-38, 39, 7.0))],
             -12.4, halo=0.9)
    ec.cloud(cv, clip, [(x, -11.5 - 1.8 * (i % 2 == 0), 4.2 - 0.6 * (i % 2 == 0)) for i, x in enumerate(np.arange(-41, 42, 7.0))],
             -25, fill=ACC_B, halo=0.0)


def scene_tree(cv, clip):
    """A fruiting tree on a mound, a bush either side, an engraved sky."""
    ec.sky(cv, clip, -5.0, AH, inner=9.5)
    ground = spline([(-40, -22), (-40, -12.4), (-19, -11.4), (0, -9.8), (19, -11.4), (40, -12.4), (40, -22)])
    outlined(cv, clip, PAPER, ground, halo=ec.HALO)
    ink(cv, clip, hatch(va.inside(ground), 0, pitch=1.5, phase=0.5, min_len=3.0))
    for s in (-1, 1):
        ec.cloud(cv, clip, [(s * 27.4, -8.6, 2.7), (s * 23.8, -7.4, 3.2), (s * 20.4, -8.8, 2.5)], -11.5, fill=ACC_B)
    half = [(0, -0.5), (-1.9, -0.5), (-2.1, -5.2), (-2.7, -8.0), (-6.4, -10.3), (-3.2, -10.9), (0, -10.3)]
    trunk = spline(half + [(-x, y) for x, y in reversed(half[1:-1])], n=400)
    outlined(cv, clip, PAPER, trunk, halo=ec.HALO)
    for x in (-0.8, 0.8):
        ink(cv, clip, taper([(x, -1.6), (x * 1.3, -5.0), (x * 1.9, -8.4)], 0.55, 0.55))
    lobes = [(0, 8.0, 5.6), (-7.4, 6.4, 5.4), (7.4, 6.4, 5.4), (-13.4, 2.4, 4.8), (13.4, 2.4, 4.8),
             (-7.2, 0.0, 4.6), (7.2, 0.0, 4.6), (0, 3.0, 6.6)]
    crown = unary_union([disk((x, y), r, 48) for x, y, r in lobes])
    outlined(cv, clip, ACC_B, crown, w=0.8, halo=0.9)
    for x, y, r in lobes[:-1]:
        ink(cv, clip, ec.arc((x, y), r - 1.9, 30, 150).intersection(crown.buffer(-1.3)))
    for x, y in ((0, 6.4), (-8.4, 4.6), (8.4, 4.6), (-4.2, 0.4), (4.2, 0.4), (-13.6, 1.4), (13.6, 1.4)):
        outlined(cv, clip, ACC_A, disk((x, y), 1.9, 32), w=0.6, halo=0.3)


def scene_flame(cv, clip):
    """A three-tongued flame in a footed bowl, sparks to either side."""
    o = np.array([0.0, -5.0])
    for i in range(13):
        a = np.radians(90 + (i - 6) * 14.0)
        u = np.array([np.cos(a), np.sin(a)])
        ink(cv, clip, taper([tuple(o + 19.5 * u), tuple(o + (25.5 if i % 2 == 0 else 23.0) * u)], 0.9, 0.5, n=12))
    base = -6.2
    outer = unary_union([ec.flame_tongue(0, base, 12.6, 19.8, 1.2), ec.flame_tongue(-5.6, base, 7.2, 13.4, -3.2),
                         ec.flame_tongue(5.8, base, 7.2, 15.4, 3.0)])
    outlined(cv, clip, ACC_A, outer, w=0.8, halo=0.9)
    mid = unary_union([ec.flame_tongue(0.2, base, 7.8, 13.6, 0.8), ec.flame_tongue(-3.5, base, 4.4, 8.0, -1.6),
                       ec.flame_tongue(3.7, base, 4.4, 9.4, 1.5)])
    outlined(cv, clip, ACC_B, mid, w=0.6)
    outlined(cv, clip, PAPER, ec.flame_tongue(0.2, base, 3.6, 7.6, 0.3), w=0.55)
    for x, y, s in ((-25.5, 7.5, 1.1), (25.0, 9.0, 1.1), (-29.5, -4.0, 0.9), (29.5, -3.0, 0.95), (-21.0, -9.5, 0.85),
                    (21.5, -8.5, 0.85), (-31.0, 12.0, 0.8), (31.5, 2.5, 0.8)):
        ink(cv, clip, Polygon([(x, y - 1.9 * s), (x + 1.1 * s, y), (x, y + 1.9 * s), (x - 1.1 * s, y)]), ACC_A)
    bowl = Polygon([(-11.8, base + 0.4), (11.8, base + 0.4), (10.8, base - 2.4), (7.6, base - 5.0), (2.8, base - 6.2),
                    (-2.8, base - 6.2), (-7.6, base - 5.0), (-10.8, base - 2.4)]).buffer(0.5).buffer(-0.5)
    foot = Polygon([(-2.2, base - 5.8), (2.2, base - 5.8), (2.9, base - 7.6), (7.2, base - 8.8), (7.2, base - 12),
                    (-7.2, base - 12), (-7.2, base - 8.8), (-2.9, base - 7.6)])
    ink(cv, clip, unary_union([bowl, foot]).buffer(ec.HALO + 0.35), PAPER)
    ink(cv, clip, unary_union([bowl, foot]).buffer(0.35))
    outlined(cv, clip, PAPER, box(-12.8, base - 0.6, 12.8, base + 1.5).buffer(0.5), w=0.7)
    ink(cv, clip, taper([(-8.8, base - 2.9), (0, base - 3.6), (8.8, base - 2.9)], 0.6, 0.6), PAPER)


def peak(cv, clip, apex, left, right, snow, base, shade=-62):
    """A snow-capped peak: outlined, its right flank hatched, a zig-zag snow line `snow` below the apex."""
    ax, ay = apex
    body = Polygon([(left, base), (ax - 0.9, ay - 0.5), (ax, ay), (ax + 0.9, ay - 0.6), (right, base)])
    outlined(cv, clip, PAPER, body, halo=ec.HALO)
    rx, k = ax + 0.6, (right - ax) * 0.18
    flank = va.inside(body).intersection(Polygon([(rx, ay), (right + 2, base - 1), (rx + k, base - 1)]))
    ink(cv, clip, hatch(flank, shade, min_len=2.2))
    ink(cv, clip, taper([(rx, ay - 0.8), (rx + k * 0.55, (ay + base) / 2), (rx + k, base)], 0.6, 0.6))
    f = snow / (ay - base)
    xs = np.linspace(ax - (ax - left) * f - 0.5, ax + (right - ax) * f + 0.5, 6)
    zig = [(left - 2, ay - snow)] + [(x, ay - snow + (1.3 if i % 2 else -0.9)) for i, x in enumerate(xs)] + \
          [(right + 2, ay - snow)]
    cap = va.inside(body).intersection(Polygon(zig + [(right + 2, ay + 2), (left - 2, ay + 2)]))
    ink(cv, clip, cap.buffer(0.3))
    ink(cv, clip, cap.buffer(-0.3), ACC_B)


def scene_mountain(cv, clip):
    """A range of snow-capped peaks under a small sun, over two rows of waves."""
    ec.sky(cv, clip, 0.5, AH, inner=8.0)
    sun = np.array([25.0, 8.6])
    for i in range(12):
        u = np.array([np.cos(np.radians(30 * i)), np.sin(np.radians(30 * i))])
        ray = ec.seg(tuple(sun + 6.0 * u), tuple(sun + (8.6 if i % 2 == 0 else 7.5) * u), 0.7)
        ink(cv, clip, ray.buffer(ec.HALO), PAPER)
        ink(cv, clip, ray)
    outlined(cv, clip, ACC_A, disk(sun, 4.6, 64), w=0.8, halo=0.7)
    base = -5.5
    peak(cv, clip, (-22.5, 7.0), -40.0, -8.0, 4.6, base)
    peak(cv, clip, (13.5, 3.4), 2.0, 26.0, 3.6, base)
    peak(cv, clip, (31.0, -0.4), 22.0, 41.0, 2.6, base)
    peak(cv, clip, (-4.5, 13.0), -18.5, 10.0, 6.4, base)
    for k, y in enumerate((-7.2, -11.8, -16.4)):
        for x in np.arange(-47.0 + (4.7 if k % 2 else 0.0), 48, 9.4):
            outlined(cv, clip, PAPER, disk((x, y), 5.1, 48), w=0.7)
            outlined(cv, clip, ACC_B, disk((x, y), 2.9, 32), w=0.55)


SCENES = {"sun": scene_sun, "moon": scene_moon, "tree": scene_tree, "flame": scene_flame, "mountain": scene_mountain}
assert set(SCENES) == set(ec.DESIGNS)       # the palettes are the emblem counter's


# ---- the face and the back ---------------------------------------------------------------

def frame(cv):
    """The block's face on an all-ink canvas: the display plate along the top, split into five cells
    (sword, power, slash, toughness, shield) by rules, and the art panel below. Returns the art panel."""
    D = ec.DISPLAY
    disp, art = rrect(D, ec.PLATE_R), rrect(ec.ART, ec.PLATE_R)
    cv.paint(PAPER, disp)
    cv.paint(PAPER, art)
    mat, rule = ec.WIN_MAT, ec.WIN_RULE
    cols = {}
    for n, _ in ec.WHEELS:
        o = ec.face_opening(n).bounds
        cols[n] = (o[0] - mat - rule, o[2] + mat + rule)
        cv.paint(INK, box(cols[n][0], D[1] - 1, cols[n][1], D[3] + 1), disp)
        cv.paint(PAPER, box(o[0] - mat, D[1] - 1, o[2] + mat, D[3] + 1), disp)
    ym, h = (D[1] + D[3]) / 2, D[3] - D[1]
    s_ = h / 20.3                                          # the cell ornaments grow with the row
    # the slash, with a lozenge either side
    xm = (cols[FRONT_WHEEL][1] + cols[REAR_WHEEL][0]) / 2
    half = np.array([2.6 * s_, h / 2 - 2.4])
    cv.paint(INK, unary_union([taper([(xm, ym), tuple(np.array([xm, ym]) + s * half)], 2.6 * s_, 0.9, n=16)
                               for s in (-1, 1)]), disp)
    for s in (-1, 1):
        cx = xm + s * 7.4 * s_
        cv.paint(INK, Polygon([(cx - 2.0 * s_, ym), (cx, ym + 3.4 * s_), (cx + 2.0 * s_, ym), (cx, ym - 3.4 * s_)]), disp)
        cv.paint(ACC_B, Polygon([(cx - 1.05 * s_, ym), (cx, ym + 1.8 * s_), (cx + 1.05 * s_, ym), (cx, ym - 1.8 * s_)]),
                 disp)
    # sword (power) in the left cell, shield (toughness) in the right
    xs = (D[0] + cols[FRONT_WHEEL][0]) / 2
    wide = min(1.0, (cols[FRONT_WHEEL][0] - D[0] - 1.6) / 9.0)        # the sword's guard is 9 mm wide as drawn
    blade, hilt, grip = (affinity.scale(g, wide, 1.0, origin=(xs, ym)) for g in ec.sword((xs, ym), h - 3.6))
    for g, fill in ((blade, PAPER), (hilt, ACC_B)):
        cv.paint(INK, g.buffer(0.3, join_style="round"), disp)
        cv.paint(fill, g.buffer(-0.3, join_style="round"), disp)
    cv.paint(INK, grip, disp)
    xh = (D[2] + cols[REAR_WHEEL][1]) / 2
    sw = min(7.6 * s_, D[2] - cols[REAR_WHEEL][1] - 2.0)
    sh = ec.shield((xh, ym), sw, sw * 1.5)
    cv.paint(INK, sh.buffer(0.35, join_style="round"), disp)
    cv.paint(PAPER, sh.buffer(-0.35, join_style="round"), disp)
    cv.paint(ACC_A, sh.buffer(-1.5, join_style="round"), disp)
    cv.paint(INK, unary_union([box(xh - 0.45, ym - 9, xh + 0.45, ym + 9),
                               box(xh - 6, ym + sw * 0.12, xh + 6, ym + sw * 0.12 + 0.9)]).intersection(sh.buffer(-1.5)),
             disp)
    return art


def front_regions(card, design):
    cv = vc.Canvas(card)
    clip = frame(cv)
    SCENES[design](cv, clip)
    return ec.finish(cv, card)


def back_outline():
    """The back plate: the block's outline plus the lead-in lip above it."""
    return rrect((0, 0, BLOCK_W, BLOCK_H + LIP), ec.CORNER_R)


def back_regions():
    """The back: ink edge, paper field, an eight-point star in accent B."""
    plate = back_outline()
    cv = vc.Canvas(plate)
    cv.paint(PAPER, plate.buffer(-ec.EDGE).buffer(-0.3).buffer(0.3))
    c = (CX, (BLOCK_H + LIP) / 2)
    s = unary_union([ec.star(c, 10.0, 2.9), ec.star(c, 6.2, 2.9, rot=45)])
    cv.paint(INK, s.buffer(0.4, join_style="round"))
    cv.paint(ACC_B, s.buffer(-0.4, join_style="round"))
    cv.paint(INK, disk(c, 1.8, 32))
    regions = {k: g.intersection(plate).buffer(0) for k, g in cv.r.items()}
    return {k: vc.tidy(g) for k, g in vc.absorb_islands(regions).items()}


# ---- the pocket ------------------------------------------------------------------------------

def pocket(m):
    """The back's rim (side walls and foot, open at the top for the card) and the ridges on the foot
    that locate the tray. The ridges sit only where the tray is solid above its roof, so their grooves
    (cut through the roof) never open into the toughness cavity."""
    card = m["card"]
    slot = box(SIDE_WALL, FOOT, BLOCK_W - SIDE_WALL, BLOCK_H + LIP + 1)
    rim = card.difference(slot)
    ok = m["spacer_back"].buffer(-(PEG_W / 2 + PEG_MARGIN)).intersection(
        box(3.4, 1.6 + PEG_W / 2, BLOCK_W - 3.4, FOOT - 1.6 - PEG_W / 2))
    runs = []
    for y in ((3.5, FOOT - 3.5) if FOOT >= 10.0 else (FOOT / 2,)):
        ln = LineString([(0, y), (BLOCK_W, y)]).intersection(ok)
        runs += [s for s in va.lines_of(ln) if s.length >= 5.0]
    ridges = unary_union([s.buffer(PEG_W / 2, quad_segs=12) for s in runs])
    grooves = ridges.buffer(PEG_CLR, quad_segs=12)
    assert len(runs) >= 2, "the tray needs at least two locating ridges"
    assert rim.buffer(-0.5).contains(ridges), "ridges must stand on the foot"
    assert m["spacer_back"].buffer(-1.0).contains(grooves), "a groove would open into the toughness cavity"
    assert FOOT >= 6.0 and SLOT_T >= 1.0 and SIDE_WALL >= 2.0
    print(f"pocket: slot {SLOT_W:.1f} wide x {SLOT_T} deep x {COVER:.1f} tall (to the art's foot); side walls "
          f"{SIDE_WALL:.1f}, foot {FOOT:.1f}; back plate {BLOCK_W:.1f} x {BLOCK_H + LIP:.1f} x {BACK_T} (lip {LIP}); "
          f"{len(runs)} locating ridges, " + ", ".join(f"{s.length:.0f}" for s in runs) + " mm")
    return dict(slot=slot, rim=rim, ridges=ridges, grooves=grooves)


def build_parts(m, pk, regions, back_art):
    """Every prism as {object: [(z0, z1, shape, slot)]} in each part's print frame."""
    card = m["card"]
    blank = {k: (card if k == PAPER else Polygon()) for k in range(4)}
    parts = ec.build_parts(m, regions, blank)
    body = parts.pop("back")                               # the emblem counter's back = this model's tray
    roof = []
    for z0, z1 in ec.layers(0.0, ROOF_T):
        g = card.difference(pk["grooves"])
        cut = ENTRY - z0                                   # the lead-in chamfer along the slot's mouth
        if cut > 1e-9:
            g = g.difference(box(SIDE_WALL, BLOCK_H - cut, BLOCK_W - SIDE_WALL, BLOCK_H + 1))
        roof.append((z0, z1, g, PAPER))
    tray = roof + [p for p in body if p[0] >= ROOF_T - 1e-9]
    back = [(0.0, ec.INLAY, ec.mirror(back_art[k]), k) for k in range(4)] + [
        (ec.INLAY, BACK_T, back_outline(), PAPER),
        (BACK_T, BODY_Z, pk["rim"], PAPER),
        (BODY_Z, BODY_Z + PEG_H, pk["ridges"], PAPER)]
    return {"front": parts["front"], "tray": tray, "divider": parts["divider"], "back": back,
            **{n: parts[n] for n, _ in ec.WHEELS}}


def assembly_check(m, pk, parts):
    """The emblem counter's check on the body (tray, wheels, divider, front as printed), then the pocket
    and where the digits land on a card."""
    ec.assembly_check(m, {**{k: v for k, v in parts.items() if k != "back"}, "back": parts["tray"]})
    card = m["card"]
    roof = ec.at_z(parts["tray"], ROOF_T - ec.LAYER / 2)
    ridges = ec.at_z(parts["back"], BODY_Z + PEG_H / 2)
    holes = card.difference(roof)
    assert holes.buffer(-(PEG_CLR - 0.02)).contains(ridges), "a ridge doesn't clear its groove"
    assert not holes.buffer(-(PEG_CLR + 0.02)).contains(ridges), "the grooves are looser than PEG_CLR"
    assert PEG_H <= ROOF_T - 0.15, "the ridges bottom out"
    solid_above = ec.at_z(parts["tray"], ROOF_T + ec.LAYER / 2)
    assert solid_above.buffer(-0.9).contains(holes), "a groove isn't roofed by the tray's spacer"
    rim = ec.at_z(parts["back"], BACK_T + SLOT_T / 2)
    slot = card.difference(rim)
    b = slot.bounds
    assert abs((b[2] - b[0]) - SLOT_W) < 1e-6 and abs(b[1] - FOOT) < 1e-6, "slot size"
    side = (SLOT_W - 67) / 2
    sleeve = box(CX - 33.5, FOOT + side, CX + 33.5, FOOT + 92)        # standing `side` off the floor
    assert rim.distance(sleeve) >= side - 0.02, "a 67 x 92 sleeve doesn't fit"
    assert roof.contains(slot.buffer(-1.0).intersection(box(0, 0, BLOCK_W, BLOCK_H - ENTRY - 0.2))), "hole in the slot's roof"
    # the digits over the card: heights above the card's own bottom edge (the card sits ~1 mm up in its sleeve)
    w = ec.window(FRONT_WHEEL).bounds
    lo, hi = w[1] + ec.WIN_PAD[1] - FOOT - 1.0, w[3] - ec.WIN_PAD[1] - FOOT - 1.0
    assert lo >= 5.0 and hi <= COVER - 3.0, f"the digits ({lo:.1f}-{hi:.1f} mm up the card) are not over the covered part"
    print(f"pocket check: ridges {PEG_CLR} mm inside grooves that the tray roofs; a 67 x 92 mm sleeve fits the slot "
          f"with {side:.1f} mm each side; the digits sit {lo:.1f}-{hi:.1f} mm up the card; assembled "
          f"{BLOCK_W:.1f} x {BLOCK_H:.1f} x {THICK:.1f} mm ({BLOCK_W / 25.4:.3f} x {BLOCK_H / 25.4:.3f} x "
          f"{THICK / 25.4:.3f} in), back plate to {BLOCK_H + LIP:.1f}")


def plate_offsets(m):
    """Front, tray, divider in a row with the back and wheels behind; or, when three blocks are wider
    than the bed, two columns: front and tray, divider and back, then the wheels."""
    R, g = ec.R_WHEEL, PLATE_GAP
    if 3 * BLOCK_W + 2 * g <= BED:
        off = {"front": (0.0, 0.0), "tray": (BLOCK_W + g, 0.0), "divider": (2 * (BLOCK_W + g), 0.0),
               "back": (0.0, BLOCK_H + g)}
        wx, wy = BLOCK_W + g, BLOCK_H + g
    else:
        off = {"front": (0.0, 0.0), "tray": (BLOCK_W + g, 0.0), "divider": (0.0, BLOCK_H + g),
               "back": (BLOCK_W + g, BLOCK_H + g)}
        wx, wy = 0.0, 2 * BLOCK_H + LIP + 2 * g
    for i, (name, _) in enumerate(ec.WHEELS):
        C = m["whs"][name]["C"]
        off[name] = (wx + R + ec.PROTRUDE + i * (2 * R + g) - C[0], wy + R - C[1])
    return off


ec.plate_offsets = plate_offsets          # ec.write_plate lays the objects out with this


# ---- previews -----------------------------------------------------------------------------

def draw_card(ax):
    """A sleeved card standing in the slot (a grey stand-in, to show what the block covers)."""
    sx = CX - 33.0
    vd.draw(ax, rrect((sx, FOOT + 0.2, sx + 66.0, FOOT + 91.2), 1.0), "#d9dde2")
    cx0, cy0 = CX - 31.5, FOOT + 1.2
    vd.draw(ax, rrect((cx0, cy0, cx0 + 63, cy0 + 88), 3.0), "#2b2b2e")
    vd.draw(ax, rrect((cx0 + 3.2, cy0 + 78.6, cx0 + 59.8, cy0 + 84.6), 1.0), "#c9c2b4")     # name bar
    vd.draw(ax, box(cx0 + 4.4, cy0 + 39.4, cx0 + 58.6, cy0 + 77.6), "#7d8a96")              # art
    ax.text(CX, cy0 + 58.5, "card art", ha="center", va="center", fontsize=9, color="#e8ecef")


def draw_base(ax, m, regions, hx, pt, sim=False):
    vd.draw(ax, back_outline(), ec.shade(hx[PAPER], 0.93))
    draw_card(ax)
    ec.draw_face(ax, m, regions, hx, pt, sim)
    ax.set_xlim(-ec.PROTRUDE - 2, BLOCK_W + ec.PROTRUDE + 2); ax.set_ylim(-2, FOOT + 93.5)


def designs_preview(m, faces, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    hgt = 6.2 * (FOOT + 95.5) / (BLOCK_W + 2 * ec.PROTRUDE + 4)
    fig_, axes = plt.subplots(1, len(faces), figsize=(6.2 * len(faces), hgt + 0.5), squeeze=False)
    shown = [(7, 5), (0, 1), (3, 3), (9, 9), (2, 4)]
    for ax, (design, regions), pt in zip(axes[0], faces.items(), shown):
        draw_base(ax, m, regions, ec.hexes(design), pt)
        ax.set_title(f"{design}  {pt[0]}/{pt[1]}\n" + " / ".join(ec.DESIGNS[design][0]), fontsize=9)
    plt.tight_layout()
    plt.savefig(path, dpi=110)
    plt.close(fig_)
    print(f"preview -> {path}")


def design_preview(m, design, regions, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_, axes = plt.subplots(1, 2, figsize=(15, 6.2))
    for ax, sim, pt in zip(axes, (False, True), ((7, 5), (2, 8))):
        ec.draw_face(ax, m, regions, ec.hexes(design), pt, sim)
        ax.set_ylim(-1.5, BLOCK_H + 1.5)
        ax.set_title(f"{design} {pt[0]}/{pt[1]}" + (" (nozzle simulation)" if sim else ""), fontsize=10)
    plt.tight_layout()
    plt.savefig(path, dpi=110)
    plt.close(fig_)


def parts_preview(m, pk, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    card, whs = m["card"], m["whs"]
    fig_, axes = plt.subplots(1, 5, figsize=(31, 6.4), gridspec_kw=dict(width_ratios=[1, 1, 1, 1, 0.9]))
    solid, light, red, dark, blue = "#7a6a58", "#e8d2a8", "#b03a2e", "#3a2d25", "#1f5fa8"
    ax = axes[0]
    vd.draw(ax, back_outline(), light); vd.draw(ax, pk["rim"], solid); vd.draw(ax, pk["ridges"], red)
    ax.plot(*np.asarray(box(CX - 33.5, FOOT, CX + 33.5, BLOCK_H + LIP).exterior.coords).T, color=blue, lw=0.8)
    ax.set_title("back: plate with lip, rim (side walls + foot, brown), locating ridges (red); sleeve outline blue",
                 fontsize=9)
    ax = axes[1]
    vd.draw(ax, card, light); vd.draw(ax, m["spacer_back"], solid); vd.draw(ax, m["ridge"], red)
    vd.draw(ax, pk["grooves"], "#ffffff"); vd.draw(ax, m["pin"][REAR_WHEEL], dark)
    ax.plot(*np.asarray(whs[REAR_WHEEL]["disc"].exterior.coords).T, color=blue, lw=0.8)
    ax.set_title("tray: roof (grooves white), spacer, tongue dashes (red), toughness pin and wheel", fontsize=9)
    ax = axes[2]
    vd.draw(ax, m["divider"], solid); vd.draw(ax, m["pin"][FRONT_WHEEL], dark)
    ax.plot(*np.asarray(whs[FRONT_WHEEL]["disc"].exterior.coords).T, color=blue, lw=0.8)
    ax.set_title("divider: toughness window, tongue slots, pin hole; power pin and wheel", fontsize=9)
    ax = axes[3]
    vd.draw(ax, card, light)
    vd.draw(ax, m["spacer_front"].difference(ec.opening(REAR_WHEEL, ec.PLATE_T)), solid)
    vd.draw(ax, m["slots"], red); vd.draw(ax, m["sock"][FRONT_WHEEL], dark)
    for n, _ in ec.WHEELS:
        vd.draw(ax, ec.opening(n, ec.PLATE_T), "#ffffff")
    ax.set_title("front underside (front-view frame): spacer, groove (red), socket, openings", fontsize=9)
    for ax in axes[:4]:
        ax.set_xlim(-ec.PROTRUDE - 1.5, BLOCK_W + ec.PROTRUDE + 1.5); ax.set_ylim(-1.5, BLOCK_H + LIP + 1.5)
    # section on the centre line: y across, z up
    ax = axes[4]
    z = [0, BACK_T, BODY_Z, BODY_Z + ROOF_T, BODY_Z + ROOF_T + ec.CAVITY, BODY_Z + ROOF_T + ec.CAVITY + ec.DIV_T,
         THICK - ec.PLATE_T, THICK]
    vd.draw(ax, box(0, z[0], BLOCK_H + LIP, z[1]), solid)
    vd.draw(ax, box(0, z[1], FOOT, z[2]), solid)
    vd.draw(ax, box(FOOT + 0.2, z[1] + 0.25, BLOCK_H + LIP + 6, z[1] + 0.95), blue)
    for za, zb, colour in ((z[2], z[3], "#a08a6c"), (z[4], z[5], "#a08a6c"), (z[6], z[7], light)):
        vd.draw(ax, box(0, za, BLOCK_H, zb), colour)
    for za, zb in ((z[3], z[4]), (z[5], z[6])):
        vd.draw(ax, unary_union([box(0, za, BOTTOM_WALL, zb), box(BLOCK_H - TOP_WALL, za, BLOCK_H, zb)]), solid)
        vd.draw(ax, box(BOTTOM_WALL + 1.0, za, BLOCK_H - TOP_WALL - 1.0, za + ec.WHEEL_T), "#f4f1ea")
    ax.set_xlim(-1, BLOCK_H + LIP + 7); ax.set_ylim(-1, THICK + 2)
    ax.set_title("section on the centre line (bottom edge at left): back plate and foot, the card (blue)\n"
                 "in its slot, tray roof, toughness wheel, divider, power wheel, face plate", fontsize=9)
    for ax in axes:
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    plt.tight_layout()
    plt.savefig(path, dpi=110)
    plt.close(fig_)
    print(f"preview -> {path}")


# ---- build --------------------------------------------------------------------------------

def main():
    only = sys.argv[1:]
    m = ec.mechanism()
    pk = pocket(m)
    card = m["card"]
    back_art = back_regions()
    faces, checked = {}, False
    for design in SCENES:
        if only and design not in only:
            continue
        regions = front_regions(card, design)
        ec.report(design, card, regions)
        parts = build_parts(m, pk, regions, back_art)
        if not checked:
            assembly_check(m, pk, parts)
            checked = True
        ec.write_plate(m, parts, design, OUT / design)
        faces[design] = regions
        design_preview(m, design, regions, OUT / f"{design}_preview.png")
    designs_preview(m, faces, OUT / "designs_preview.png")
    parts_preview(m, pk, OUT / "parts_preview.png")


if __name__ == "__main__":
    main()
