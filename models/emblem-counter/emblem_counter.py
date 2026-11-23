#!/usr/bin/env python3
"""
Emblem counter: a generic power/toughness token the size of a card (63 x 88 mm), in the woodcut style of
the vampire cards but with no creature on it. The lower third of the face (where a card's text box is)
is the counter: power and toughness in 12 mm digits, 0-9 each, on two separate wheels. Five faces share
the mechanism: sun, moon, tree, flame, mountain. Each is drawn in four of the six Bambu PLA Matte
tan/brown spools, and all six are used across the set.

Spec: see README.md in this folder.

How two 52 mm wheels fit in a 63 mm card: they overlap, on two levels.
  * power     the FRONT wheel, rim out of the LEFT edge, window upper-left
  * toughness the REAR wheel, rim out of the RIGHT edge, window lower-right, seen down a bevelled well
The toughness window has to miss the power wheel's cavity, so the power wheel sits higher and the
digits read as a diagonal fraction: power high on the left, a slash, toughness low on the right.
Pushing either rim UP counts up. No detent: each wheel's friction holds its value.

Parts (five, all printed flat, no supports; z from the card's back face when assembled):
  back      0.0-0.6 base (art inlaid), 0.6-2.6 spacer round the toughness cavity, axle pin, tongue
  toughness 0.6-2.2 wheel, face-down print, digits inlaid
  divider   2.6-3.4 plate between the wheels (toughness window, slots for the tongue), power axle pin on top
  power     3.4-5.0 wheel, face-down print
  front     3.4-5.4 spacer round the power cavity + 5.4-6.6 face plate; face-down print, art inlaid;
            both windows, the groove and the pin socket
The tongue stands on the back, passes through the divider's slots and ends in the front's groove, so one
ridge locates all three.

Run (from the repo root):
    .venv\\Scripts\\python.exe models\\emblem-counter\\emblem_counter.py
Outputs (millimetres) go to models\\emblem-counter\\out\\
    <design>/<object>_<n>_<slot>.stl   parts laid out as on the plate; load as ONE object (--assemble)
    <design>/slice_args.txt            the matching slice_bambu.py arguments
    designs_preview.png                the five faces, a nozzle simulation and the back
    parts_preview.png                  back, divider, front underside, wheels, and a section through the well
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
CACHE = HERE / "text_cache.json"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Shared helpers: woodcut drawing (vampire-arcana), canvas + clean-up (vampire-counter), extrusion
# (vampire-token), glyphs and the edge tongue (vampire-dial). Nothing here changes those models.
va = _load("vampire_arcana", HERE.parent / "vampire-arcana" / "vampire_arcana.py")
vc = va.vc
vt, vd = vc.vt, vc.vd
filaments = vc.filaments
rrect, disk, spline, taper = vc.rrect, vc.disk, vc.spline, vc.taper

# ---- Parameters (mm) -------------------------------------------------------
CARD_W, CARD_H, CORNER_R = 63.0, 88.0, 3.0      # a standard card
CX = CARD_W / 2

# Art slots. Each design maps them to four of the six Matte spools (tools/filaments.py).
INK, ACC_A, ACC_B, PAPER = range(4)
SLOT_NAMES = ("ink", "accentA", "accentB", "paper")

# Frame: ink card edge and rule, like the vampire cards. No title plate.
EDGE, RULE = 1.8, 1.2
PLATE_R = CORNER_R - EDGE

# Digits: Bahnschrift Bold Condensed (vampire-counter's instance), one per wheel.
DIGIT_H = 12.0
DIGIT_BOLDEN = 0.05
VALUES = range(0, 10)
STEP = 360 / len(VALUES)        # 36 degrees per value
WIN_PAD = (0.8, 0.6)            # window margin round the widest digit (x, y)
WIN_R = 1.5
WIN_TILT = 15.0                 # each window sits this far outward of straight below its wheel's centre

# Wheels: (name, side, level). side -1 = rim out of the left edge. Pushing a rim UP counts up.
WHEELS = (("power", -1), ("toughness", +1))
FRONT_WHEEL, REAR_WHEEL = "power", "toughness"
PROTRUDE = 2.5                  # rim past the card's side edge
CHANNEL_MARGIN = 0.4            # digit ring -> rim band
WHEEL_RIM = 0.8                 # solid band outside the digits
GRIP_DEPTH, GRIP_N = 0.7, 60    # knurled rim: 60 round teeth, 0.7 mm deep
WHEEL_T = 1.6
AX_CLR = 0.4                    # axial play
CAVITY = WHEEL_T + AX_CLR       # 2.0
PIN_D, PIN_CLR = 6.0, 0.4       # axle pin; radial clearance in the wheel's hole
WHEEL_CLR = 0.4                 # radial clearance wheel -> cavity wall
BOTTOM_WALL = 1.0               # least spacer under the rear cavity
WELL_WALL = 1.6                 # least wall between the toughness well and the power cavity

# Stack
INLAY = 0.4                     # two 0.2 mm layers of colour, face-down
BASE_T = 0.6                    # back plate
DIV_T = 0.8                     # divider plate
PLATE_T = 1.2                   # face plate
LAYER = 0.2
FRONT_T = PLATE_T + CAVITY      # 3.2: the front part
THICK = BASE_T + CAVITY + DIV_T + FRONT_T   # 6.6

# Windows. Both openings widen toward the face at 45 degrees, one layer per step.
BEVEL = 0.8                     # every side, within the face plate
BEVEL_DEEP = 2.8                # the toughness well's bottom side, through plate and spacer
WIN_MAT, WIN_RULE = 0.7, 0.7    # paper mat, then an ink rule, round each opening

# Tongue and groove
TONGUE_W, TONGUE_H = 1.2, 0.6   # TONGUE_H is what enters the front; the ridge is DIV_T taller
TONGUE_INSET = 2.0
TONGUE_CLR = 0.15               # per side, in the divider's slots and the front's groove
TONGUE_GAP = 1.2                # tongue edge -> any cavity
TONGUE_MIN_LEN = 6.0
BRIDGE_PITCH, BRIDGE_W = 16.0, 2.6   # the ridge is dashed so the divider's slots leave it in one piece
GROOVE_DEPTH = TONGUE_H + 0.2
SOCKET_CLR = 0.15               # per side, pins in the divider's hole and the front's socket
SOCKET_DEPTH = 0.6              # blind socket in the face plate for the power pin
PIN_ENTRY = 0.4                 # how far a pin enters its socket

# Art rules (0.4 nozzle)
OUTLINE, LINE, PITCH, HALO = 0.7, 0.55, 1.25, 0.7
BEAD, MIN_ISLAND = vc.BEAD, vc.MIN_ISLAND

PLATE_GAP = 6.0
NOZZLE = 0.4
SLICER_PRESETS = ["--machine", "Bambu Lab A1 0.4 nozzle", "--process", "0.20mm Standard @BBL A1",
                  "--filament", "Bambu PLA Matte @BBL A1"]
SLICER_SET = vc.SLICER_SET + ["initial_layer_speed=30", "initial_layer_infill_speed=60"]
# ---------------------------------------------------------------------------


# ---- digits and layout --------------------------------------------------------

def _digit(v):
    k = (DIGIT_H - 2 * DIGIT_BOLDEN) / vd.glyphs("8", vc.DFONT).bounds[3]
    g = affinity.scale(vd.glyphs(str(v), vc.DFONT), k, k, origin=(0, 0)).buffer(DIGIT_BOLDEN, join_style="round")
    b = g.bounds
    return affinity.translate(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)


def digit(v, centre):
    """One digit, DIGIT_H tall, bbox centred on centre. Cached, so a build without the font matches."""
    g = vd.text_cache(CACHE, f"digit_{v}_{DIGIT_H:g}", lambda: _digit(v), vc.DIGIT_FONT[0])
    return affinity.translate(g, *centre)


def win_box(c, grow=(0.0, 0.0, 0.0, 0.0)):
    """A window centred on c, grown by (left, bottom, right, top)."""
    w, h = WIN_WH
    return rrect((c[0] - w / 2 - grow[0], c[1] - h / 2 - grow[1], c[0] + w / 2 + grow[2], c[1] + h / 2 + grow[3]),
                 WIN_R)


def _ring_radius(side):
    """Smallest digit-ring radius that hides both neighbours of every value in a window WIN_TILT outward
    of straight below the centre."""
    a = np.radians(-90 + side * WIN_TILT)
    for r in np.arange(DIGIT_H, 3 * DIGIT_H, 0.05):
        p0 = r * np.array([np.cos(a), np.sin(a)])
        win = win_box(p0).buffer(0.3)
        if all(not affinity.rotate(digit(v, p0), s, origin=(0, 0)).intersects(win)
               for v in VALUES for s in (-STEP, STEP)):
            return float(r)
    raise RuntimeError("no ring radius found")


def layout():
    """Ring radius, wheel radius, wheel centres and window centres.
    The toughness (rear) window sits as low as its bevel allows; the power (front) wheel is then the
    lowest that leaves WELL_WALL between its cavity and the toughness well."""
    r = max(_ring_radius(side) for _, side in WHEELS)
    p0 = {name: r * np.array([np.cos(np.radians(-90 + side * WIN_TILT)), np.sin(np.radians(-90 + side * WIN_TILT))])
          for name, side in WHEELS}
    corner = max(np.hypot(*np.array(win_box(p).exterior.coords).T).max() for p in p0.values())
    R = corner + CHANNEL_MARGIN + WHEEL_RIM + GRIP_DEPTH
    cx = {name: (R - PROTRUDE if side < 0 else CARD_W + PROTRUDE - R) for name, side in WHEELS}
    win_y = EDGE + WIN_MAT + BEVEL_DEEP + WIN_WH[1] / 2
    c = {REAR_WHEEL: np.array([cx[REAR_WHEEL], win_y - p0[REAR_WHEEL][1]])}
    well = win_box(c[REAR_WHEEL] + p0[REAR_WHEEL])
    dy = next(d for d in np.arange(0, 40, 0.1)
              if Point(cx[FRONT_WHEEL], c[REAR_WHEEL][1] + d).distance(well) - (R + WHEEL_CLR) >= WELL_WALL)
    c[FRONT_WHEEL] = np.array([cx[FRONT_WHEEL], c[REAR_WHEEL][1] + dy])
    return r, R, c, {n: c[n] + p0[n] for n in c}


def configure(**overrides):
    """Set parameters, then recompute everything derived from them: window size, wheel layout, plates.
    The module calls it once with its own parameter block. A model that reuses the mechanism at another
    size (models/sleeve-counter) calls it again with overrides."""
    g = globals()
    unknown = [k for k in overrides if k not in g]
    assert not unknown, f"unknown parameters {unknown}"
    g.update(overrides)
    g["CX"] = CARD_W / 2
    g["PLATE_R"] = CORNER_R - EDGE
    g["STEP"] = 360 / len(VALUES)
    g["CAVITY"] = WHEEL_T + AX_CLR
    g["FRONT_T"] = PLATE_T + CAVITY
    g["THICK"] = BASE_T + CAVITY + DIV_T + FRONT_T
    g["GROOVE_DEPTH"] = TONGUE_H + 0.2
    g["WIN_WH"] = (max(digit(v, (0, 0)).bounds[2] - digit(v, (0, 0)).bounds[0] for v in VALUES) + 2 * WIN_PAD[0],
                   DIGIT_H + 2 * WIN_PAD[1])
    g["DIGIT_R"], g["R_WHEEL"], g["WHEEL_C"], g["WIN_C"] = layout()
    g["SPIN"] = {name: side for name, side in WHEELS}   # +1: a counter-clockwise turn counts up (right rim pushed up)
    # Plates (paper interiors). The display plate is the card's "text box"; the art plate is everything above.
    g["DISPLAY"] = (EDGE, EDGE, CARD_W - EDGE, WIN_C[FRONT_WHEEL][1] + WIN_WH[1] / 2 + BEVEL + WIN_MAT)
    g["ART"] = (EDGE, DISPLAY[3] + RULE, CARD_W - EDGE, CARD_H - EDGE)
    g["AC"] = ((ART[0] + ART[2]) / 2, (ART[1] + ART[3]) / 2)     # the scenes are drawn about the art plate's centre
    g["AW"], g["AH"] = (ART[2] - ART[0]) / 2, (ART[3] - ART[1]) / 2   # half width, half height


configure()


def window(name):
    return win_box(WIN_C[name])


def opening(name, d):
    """The hole for `name`'s window at depth d below the face (d = 0 at the face)."""
    s = float(np.clip(PLATE_T - d, 0, BEVEL))
    b = s
    if name == REAR_WHEEL:
        b = max(s, float(np.clip(FRONT_T - d, 0, BEVEL_DEEP)))
    return win_box(WIN_C[name], (s, b, s, s))


def face_opening(name):
    return opening(name, INLAY / 2)


def wheel_geometry(name):
    C, spin = WHEEL_C[name], SPIN[name]
    win = window(name)
    pts = np.array(win.exterior.coords)
    r_out = np.hypot(*(pts - C).T).max() + CHANNEL_MARGIN
    r_in = Point(*C).distance(win) - CHANNEL_MARGIN
    R = r_out + WHEEL_RIM + GRIP_DEPTH
    t = np.linspace(0, 2 * np.pi, GRIP_N * 24, endpoint=False)
    rho = R - GRIP_DEPTH / 2 + GRIP_DEPTH / 2 * np.cos(GRIP_N * t)
    disc = Polygon(np.c_[C[0] + rho * np.cos(t), C[1] + rho * np.sin(t)]).difference(
        disk(C, PIN_D / 2 + PIN_CLR, 32))
    channel = disk(C, r_out, 256).difference(disk(C, r_in, 256))
    # value v is set upright at the window, then turned back v steps against the count-up direction
    groups = [affinity.rotate(digit(v, WIN_C[name]), -spin * STEP * i, origin=tuple(C)) for i, v in enumerate(VALUES)]
    for i, g in enumerate(groups):
        assert channel.contains(g), "digits must sit inside the channel"
        for s in (-STEP, STEP):
            nb = affinity.rotate(g, spin * STEP * i + s, origin=tuple(C))
            assert not nb.intersects(win.buffer(0.3)), "a neighbouring value would show in the window"
    return dict(name=name, C=C, spin=spin, R=R, r_in=r_in, r_out=r_out, disc=disc, groups=groups)


def turned(g, wh, v):
    """g (on wheel wh) turned to show value v."""
    return affinity.rotate(g, wh["spin"] * STEP * list(VALUES).index(v), origin=tuple(wh["C"]))


def clean(g, r=0.3):
    """Drop slivers narrower than 2r (the horns where a cavity meets the card edge)."""
    return g.buffer(-r).buffer(r)


def mechanism():
    """All five parts' 2D shapes in the front-view frame, with the fit checks."""
    card = vt.rounded_rect(CARD_W, CARD_H, CORNER_R)
    whs = {name: wheel_geometry(name) for name, _ in WHEELS}
    R = R_WHEEL
    assert all(abs(w["R"] - R) < 1e-6 for w in whs.values())
    cav = {n: disk(WHEEL_C[n], R + WHEEL_CLR, 512) for n in whs}
    well_max = face_opening(REAR_WHEEL)
    spacer_back = clean(card.difference(cav[REAR_WHEEL]))
    spacer_front = clean(card.difference(cav[FRONT_WHEEL]))

    # the tongue: where back spacer and front spacer are both solid, dashed for the divider's sake
    ridge, _ = vd.edge_tongue(card, unary_union([*cav.values(), well_max]), TONGUE_INSET, TONGUE_W, TONGUE_GAP,
                              TONGUE_MIN_LEN)
    ring = card.buffer(-TONGUE_INSET, quad_segs=16).exterior
    cuts = unary_union([ring.interpolate(s).buffer(BRIDGE_W / 2 + TONGUE_W / 2)
                        for s in np.arange(BRIDGE_PITCH / 2, ring.length, BRIDGE_PITCH)])
    dashes = [p for p in vt.polys_of(ridge.difference(cuts)) if p.area >= TONGUE_MIN_LEN * TONGUE_W]
    ridge = unary_union(dashes)
    slots = ridge.buffer(TONGUE_CLR, quad_segs=12)

    pin = {n: disk(WHEEL_C[n], PIN_D / 2, 32) for n in whs}
    sock = {n: disk(WHEEL_C[n], PIN_D / 2 + SOCKET_CLR, 32) for n in whs}
    divider = card.difference(unary_union([window(REAR_WHEEL), slots, sock[REAR_WHEEL]]))

    # ---- fit checks (design frame) ----
    rear_c, front_c = WHEEL_C[REAR_WHEEL], WHEEL_C[FRONT_WHEEL]
    bottom = rear_c[1] - R - WHEEL_CLR
    assert bottom >= BOTTOM_WALL - 1e-6, f"only {bottom:.2f} mm of spacer under the rear cavity"
    assert front_c[1] + R + WHEEL_CLR <= CARD_H - 2.0, "the front wheel runs off the top"
    for n, side in WHEELS:
        out = (-(WHEEL_C[n][0] - R)) if side < 0 else (WHEEL_C[n][0] + R - CARD_W)
        assert abs(out - PROTRUDE) < 1e-6, f"{n} rim must poke {PROTRUDE} past its edge"
        other = (WHEEL_C[n][0] + R + WHEEL_CLR - CARD_W) if side < 0 else -(WHEEL_C[n][0] - R - WHEEL_CLR)
        assert other < -3.0, f"{n} wheel must stay inside the opposite edge"
    wall = cav[FRONT_WHEEL].distance(opening(REAR_WHEEL, PLATE_T))
    assert wall >= WELL_WALL - 0.05, f"wall between the well and the power cavity is {wall:.2f} mm"
    assert not window(FRONT_WHEEL).intersects(face_opening(REAR_WHEEL).buffer(2 * (WIN_MAT + WIN_RULE)))
    assert spacer_back.buffer(-0.4).contains(ridge) and spacer_front.buffer(-0.4).contains(ridge), \
        "the tongue must stand on, and enter, solid spacer"
    assert card.buffer(-1.0).contains(slots), "the groove needs an outer wall of >= 1 mm"
    assert (PIN_D / 2 + PIN_CLR) < whs[FRONT_WHEEL]["r_in"] - 1.0, "hub hole runs into the digit channel"
    assert PLATE_T - SOCKET_DEPTH >= INLAY + 0.2 - 1e-9, "too little face plate over the pin socket"
    assert cav[FRONT_WHEEL].contains(pin[FRONT_WHEEL]) and cav[REAR_WHEEL].contains(pin[REAR_WHEEL])
    plate = rrect(DISPLAY, PLATE_R)
    for n in whs:
        assert plate.buffer(1e-6).contains(face_opening(n).buffer(WIN_MAT - 1e-3)), f"{n} opening leaves the display plate"
    runs = sorted((p.length - 2 * TONGUE_W) / 2 for p in dashes)

    print(f"card: {CARD_W:.1f} x {CARD_H:.1f} x {THICK:.1f} mm ({CARD_W / 25.4:.3f} x {CARD_H / 25.4:.3f} x "
          f"{THICK / 25.4:.3f} in), plus {PROTRUDE} mm of rim each side")
    print(f"digits {DIGIT_H:g} mm, 0-9; ring r {DIGIT_R:.2f}; wheels dia {2 * R:.1f} (R {R:.2f}), "
          f"{WHEEL_T} thick in {CAVITY} cavities; windows {WIN_WH[0]:.1f} x {WIN_WH[1]:.1f}")
    for n in whs:
        level = "front" if n == FRONT_WHEEL else "rear"
        fo = face_opening(n).bounds
        print(f"  {n:9s} ({level}): centre ({WHEEL_C[n][0]:.2f}, {WHEEL_C[n][1]:.2f}), window centre "
              f"({WIN_C[n][0]:.2f}, {WIN_C[n][1]:.2f}), face opening {fo[2] - fo[0]:.1f} x {fo[3] - fo[1]:.1f}")
    print(f"wall well -> power cavity {wall:.2f}; spacer under the rear cavity {bottom:.2f}; "
          f"display plate {DISPLAY[2] - DISPLAY[0]:.1f} x {DISPLAY[3] - DISPLAY[1]:.1f}, "
          f"art plate {ART[2] - ART[0]:.1f} x {ART[3] - ART[1]:.1f}")
    print(f"tongue: {TONGUE_W} x {DIV_T + TONGUE_H:.1f} mm ridge in {len(dashes)} dashes, {sum(runs):.0f} mm "
          f"({runs[0]:.0f}-{runs[-1]:.0f} mm each); groove {TONGUE_W + 2 * TONGUE_CLR:.1f} x {GROOVE_DEPTH:.1f}")
    return dict(card=card, whs=whs, cav=cav, spacer_back=spacer_back, spacer_front=spacer_front, ridge=ridge,
                slots=slots, pin=pin, sock=sock, divider=divider)


# ---- drawing helpers (scene coordinates: origin at the art plate's centre) ----------

def L(g):
    return affinity.translate(g, *AC)


def outlined(cv, clip, fill, g, w=OUTLINE, halo=0.0):
    """g (scene coordinates) filled, with an ink outline straddling its edge and an optional paper halo."""
    va.outlined(cv, fill, L(g), clip, w=w, halo=halo)


def ink(cv, clip, g, colour=INK):
    cv.paint(colour, L(g), clip)


def seg(p, q, w=LINE):
    return LineString([p, q]).buffer(w / 2, quad_segs=8)


def arc(c, r, a0, a1, w=LINE, n=24):
    t = np.radians(np.linspace(a0, a1, n))
    return LineString(np.c_[c[0] + r * np.cos(t), c[1] + r * np.sin(t)]).buffer(w / 2, quad_segs=8)


def star(c, ro, ri, n=4, rot=90.0):
    a = np.radians(rot + 180.0 * np.arange(2 * n) / n)
    r = np.where(np.arange(2 * n) % 2 == 0, ro, ri)
    return Polygon(np.c_[c[0] + r * np.cos(a), c[1] + r * np.sin(a)])


def hatch(g, angle, pitch=PITCH, w=LINE, phase=0.0, min_len=2.0):
    return va.hatch(g, angle, pitch=pitch, w=w, phase=phase, min_len=min_len)


def sky(cv, clip, y0, y1, pitch=PITCH, full=False, inner=11.0):
    """Engraved sky: horizontal strokes. full: edge to edge; else ragged strokes in from both sides."""
    out = []
    for y in np.arange(y0, y1, pitch):
        if full:
            out.append(seg((-AW - 1, y), (AW + 1, y)))
            continue
        for side, ph in ((-1, 0.0), (1, 1.7)):
            n = inner + 3.5 * np.sin(0.61 * y + ph) + 1.8 * np.sin(1.73 * y + 2 * ph)
            out.append(seg((side * (AW + 1), y), (side * (AW - n), y)))
    ink(cv, clip, unary_union(out))


def cloud(cv, clip, bumps, base_y, fill=PAPER, halo=HALO, curls=True):
    """A woodcut cloud: a row of disks on a flat base, outlined, with a curl in each larger bump."""
    g = unary_union([disk((x, y), r, 32) for x, y, r in bumps]).intersection(box(-60, base_y, 60, 60))
    outlined(cv, clip, fill, g, w=0.6, halo=halo)
    if curls:
        for x, y, r in bumps:
            if r >= 2.4:
                c = arc((x, y + 0.2), r * 0.55, 200, 330).intersection(g.buffer(-0.9))
                if not c.is_empty:
                    ink(cv, clip, c)


def flame_tongue(x, y, w, h, lean):
    """A flame tongue standing on (x, y): w wide, h tall, its tip leaning `lean` mm sideways."""
    return affinity.translate(spline([(-w / 2, 0), (-w * 0.46, h * 0.34), (lean * 0.45 - w * 0.14, h * 0.74),
                                      (lean, h), (lean * 0.55 + w * 0.2, h * 0.66), (w * 0.47, h * 0.3),
                                      (w / 2, 0), (0, -w * 0.3)]), x, y)


# ---- the five scenes ----------------------------------------------------------------

def scene_sun(cv, clip):
    """A sun with sixteen rays (straight and waved, alternating) over rolling hills."""
    c, r0 = (0.0, 3.5), 8.6
    for i in range(16):
        if i % 2 == 0:
            g, fill = Polygon([(-1.7, r0 + 1.5), (1.7, r0 + 1.5), (0, r0 + 13.0)]), ACC_B
        else:
            t = np.linspace(0, 1, 9)
            g = taper(list(zip(1.2 * np.sin(2 * np.pi * t) * (1 - 0.4 * t), r0 + 1.6 + 9.6 * t)), 2.5, 0.8)
            fill = ACC_A
        outlined(cv, clip, fill, affinity.translate(affinity.rotate(g, 22.5 * i, origin=(0, 0)), *c), w=0.6)
    outlined(cv, clip, ACC_B, disk(c, r0, 96), w=0.8)
    ink(cv, clip, disk(c, 5.9, 64).difference(disk(c, 5.3, 64)))
    outlined(cv, clip, ACC_A, disk(c, 3.0, 48), w=0.6)
    cloud(cv, clip, [(-27.5, 19.0, 2.6), (-23.4, 20.6, 3.3), (-18.6, 19.4, 2.5)], 17.4)
    cloud(cv, clip, [(18.4, 17.0, 2.4), (22.8, 18.8, 3.4), (27.4, 17.4, 2.7)], 15.4)
    # hills, back to front
    far = spline([(-34, -32), (-34, -15.5), (-24, -12.6), (-12, -14.6), (0, -18.8), (8, -32)])
    outlined(cv, clip, PAPER, far, halo=HALO)
    ink(cv, clip, hatch(va.inside(far).intersection(box(-34, -32, -6, -15.2)), 12, min_len=2.4))
    mid = spline([(-6, -32), (2, -20.6), (12, -15.4), (22, -14.0), (34, -16.6), (34, -32)])
    outlined(cv, clip, PAPER, mid, halo=HALO)
    ink(cv, clip, hatch(va.inside(mid).intersection(box(8, -32, 34, -16.4)), -12, min_len=2.4))
    near = spline([(-34, -32), (-34, -21.6), (-17, -19.6), (0, -21.4), (16, -20.2), (34, -22.2), (34, -32)])
    ink(cv, clip, near.buffer(OUTLINE / 2 + HALO), PAPER)
    ink(cv, clip, near)
    for dy in (1.9, 3.7):
        ink(cv, clip, taper([(-26, -21.2 - dy), (-12, -20.6 - dy), (2, -22.2 - dy), (16, -21.4 - dy), (27, -22.6 - dy)],
                            0.6, 0.6), PAPER)


def scene_moon(cv, clip):
    """A crescent moon holding a star, smaller stars about it, over a bank of cloud. Light on a dark-lined sky."""
    sky(cv, clip, -AH + 0.6, AH, pitch=1.5, full=True)
    moon = disk((-2.5, 3.5), 13.2, 128).difference(disk((3.6, 5.4), 10.9, 128)).buffer(0.4).buffer(-0.4)
    outlined(cv, clip, ACC_A, moon, w=0.8, halo=0.9)
    big = unary_union([star((6.6, 4.6), 5.8, 1.7), star((6.6, 4.6), 3.6, 1.7, rot=45)])
    outlined(cv, clip, ACC_A, big, w=0.6, halo=0.8)
    for x, y, r in ((-22.5, 16.5, 3.4), (20.5, 17.5, 3.6), (23.5, -3.0, 2.9), (-21.5, -4.5, 2.8), (-9.0, 20.5, 2.5),
                    (10.5, 21.5, 2.4)):
        outlined(cv, clip, ACC_A, star((x, y), r, r * 0.36), w=0.5, halo=0.8)
    cloud(cv, clip, [(-27, -15.4, 4.0), (-20, -13.2, 4.6), (-12.5, -14.8, 3.8), (-5.5, -13.0, 4.4), (2, -14.8, 3.6),
                     (9, -12.8, 4.6), (16.5, -14.6, 3.8), (23, -12.8, 4.4), (29, -15.2, 3.6)], -19.5, halo=0.9)
    cloud(cv, clip, [(-30, -20.6, 3.6), (-23.5, -18.8, 4.4), (-16, -20.4, 3.8), (-8.8, -18.6, 4.6), (-1, -20.4, 3.8),
                     (6, -18.6, 4.4), (13.5, -20.2, 3.8), (20.5, -18.6, 4.6), (28, -20.6, 3.8)], -32, fill=ACC_B,
          halo=0.0)


def scene_tree(cv, clip):
    """A fruiting tree on a mound: a scalloped crown, a rooted trunk, an engraved sky."""
    sky(cv, clip, -9.0, AH, inner=6.5)
    ground = spline([(-34, -32), (-34, -21.5), (-18, -19.8), (0, -17.6), (18, -19.8), (34, -21.5), (34, -32)])
    outlined(cv, clip, PAPER, ground, halo=HALO)
    ink(cv, clip, hatch(va.inside(ground), 0, pitch=1.5, phase=0.4, min_len=3.0))
    half = [(0, 3.0), (-2.3, 3.0), (-2.6, -6.0), (-3.3, -12.0), (-5.4, -16.2), (-10.4, -18.5), (-5.2, -19.3),
            (0, -18.4)]
    trunk = spline(half + [(-x, y) for x, y in reversed(half[1:-1])], n=400)
    outlined(cv, clip, PAPER, trunk, halo=HALO)
    for x in (-0.95, 0.95):
        ink(cv, clip, taper([(x, 0.5), (x * 1.3, -7.0), (x * 2.2, -14.6)], 0.55, 0.55))
    lobes = [(0, 17.0, 8.2), (-10.5, 14.4, 7.6), (10.5, 14.4, 7.6), (-18.4, 8.0, 6.6), (18.4, 8.0, 6.6),
             (-11.0, 3.6, 6.4), (11.0, 3.6, 6.4), (0, 8.5, 9.0)]
    crown = unary_union([disk((x, y), r, 48) for x, y, r in lobes])
    outlined(cv, clip, ACC_B, crown, w=0.8, halo=0.9)
    for x, y, r in lobes[:-1]:
        ink(cv, clip, arc((x, y), r - 2.2, 25, 155).intersection(crown.buffer(-1.4)))
    for x, y in ((0, 15.0), (-11.8, 11.6), (11.8, 11.6), (-6.0, 5.6), (6.0, 5.6), (-18.6, 6.4), (18.6, 6.4)):
        outlined(cv, clip, ACC_A, disk((x, y), 2.2, 32), w=0.6, halo=0.35)


def scene_flame(cv, clip):
    """A three-tongued flame in a footed bowl, sparks rising."""
    for i in range(15):
        a = np.radians(90 + (i - 7) * 13.5)
        u = np.array([np.cos(a), np.sin(a)])
        r1 = 30.5 if i % 2 == 0 else 28.0
        ink(cv, clip, taper([tuple(np.array([0, -6.0]) + 24.5 * u), tuple(np.array([0, -6.0]) + r1 * u)], 0.9, 0.5, n=12))
    base = -13.4
    outer = unary_union([flame_tongue(0, base, 17.0, 36.0, 1.6), flame_tongue(-7.4, base, 9.5, 22.0, -4.2),
                         flame_tongue(7.6, base, 9.5, 25.0, 3.8)])
    outlined(cv, clip, ACC_A, outer, w=0.8, halo=0.9)
    mid = unary_union([flame_tongue(0.2, base, 10.4, 24.5, 1.0), flame_tongue(-4.6, base, 5.6, 13.0, -2.2),
                       flame_tongue(4.8, base, 5.6, 15.0, 2.0)])
    outlined(cv, clip, ACC_B, mid, w=0.6)
    outlined(cv, clip, PAPER, flame_tongue(0.2, base, 4.6, 12.0, 0.4), w=0.55)
    for x, y, s in ((-13.5, 12.0, 1.0), (13.0, 16.5, 1.1), (-9.0, 20.5, 0.85), (9.6, 9.0, 0.8), (-17.5, 3.5, 0.8),
                    (17.6, 5.0, 0.9)):
        ink(cv, clip, Polygon([(x, y - 1.9 * s), (x + 1.1 * s, y), (x, y + 1.9 * s), (x - 1.1 * s, y)]), ACC_A)
    bowl = Polygon([(-14.6, base + 0.4), (14.6, base + 0.4), (13.4, base - 3.0), (9.4, base - 6.6), (3.4, base - 8.4),
                    (-3.4, base - 8.4), (-9.4, base - 6.6), (-13.4, base - 3.0)]).buffer(0.6).buffer(-0.6)
    foot = Polygon([(-2.6, base - 8.0), (2.6, base - 8.0), (3.4, base - 10.6), (8.6, base - 12.6), (8.6, base - 14.0),
                    (-8.6, base - 14.0), (-8.6, base - 12.6), (-3.4, base - 10.6)])
    ink(cv, clip, unary_union([bowl, foot]).buffer(HALO + 0.35), PAPER)
    ink(cv, clip, unary_union([bowl, foot]).buffer(0.35))
    rim = box(-15.6, base - 0.6, 15.6, base + 1.6).buffer(0.5)
    outlined(cv, clip, PAPER, rim, w=0.7)
    for y in (base - 3.4, base - 5.6):
        half = 11.4 if y > base - 4 else 7.4
        ink(cv, clip, taper([(-half, y), (0, y - 0.7), (half, y)], 0.6, 0.6), PAPER)


def scene_mountain(cv, clip):
    """Three snow-capped peaks under a small sun, over rows of waves."""
    sky(cv, clip, 2.0, AH, inner=9.0)
    sun = (17.5, 15.0)
    for i in range(12):
        u = np.array([np.cos(np.radians(30 * i)), np.sin(np.radians(30 * i))])
        ink(cv, clip, seg(tuple(sun + 6.6 * u), tuple(sun + (9.4 if i % 2 == 0 else 8.2) * u), 0.7).buffer(HALO), PAPER)
        ink(cv, clip, seg(tuple(sun + 6.6 * u), tuple(sun + (9.4 if i % 2 == 0 else 8.2) * u), 0.7))
    outlined(cv, clip, ACC_A, disk(sun, 5.2, 64), w=0.8, halo=0.7)

    def peak(apex, left, right, snow, shade=-62):
        ax, ay = apex
        body = Polygon([(left, -12), (ax - 0.9, ay - 0.5), (ax, ay), (ax + 0.9, ay - 0.6), (right, -12)])
        outlined(cv, clip, PAPER, body, halo=HALO)
        ridge_x = ax + 0.6
        flank = va.inside(body).intersection(Polygon([(ridge_x, ay), (right + 2, -13), (ridge_x + (right - ax) * 0.18, -13)]))
        ink(cv, clip, hatch(flank, shade, min_len=2.2))
        ink(cv, clip, taper([(ridge_x, ay - 0.8), (ridge_x + (right - ax) * 0.1, (ay - 12) / 2), (ridge_x + (right - ax) * 0.18, -12)],
                            0.6, 0.6))
        zig = [(left - 2, ay - snow)]
        xs = np.linspace(ax - (ax - left) * snow / (ay + 12) - 0.5, ax + (right - ax) * snow / (ay + 12) + 0.5, 6)
        zig += [(x, ay - snow + (1.5 if i % 2 else -1.0)) for i, x in enumerate(xs)] + [(right + 2, ay - snow)]
        cap = va.inside(body).intersection(Polygon(zig + [(right + 2, ay + 2), (left - 2, ay + 2)]))
        ink(cv, clip, cap.buffer(0.3), INK)
        ink(cv, clip, cap.buffer(-0.3), ACC_B)

    peak((-15.5, 10.5), -33.0, 0.5, 6.0)
    peak((19.0, 4.5), 6.0, 33.0, 4.4)
    peak((2.0, 19.5), -17.5, 23.0, 8.0)
    # waves: rows of round crests, each row overlapping the one behind
    for k, y in enumerate((-11.0, -16.0, -21.0, -26.0)):
        for x in np.arange(-36.4 + (5.2 if k % 2 else 0.0), 37, 10.4):
            outlined(cv, clip, PAPER, disk((x, y), 5.6, 48), w=0.7)
            outlined(cv, clip, ACC_B, disk((x, y), 3.2, 32), w=0.55)


# name -> (spools for ink / accent A / accent B / paper, scene, description)
DESIGNS = {
    "sun": (("Dark Chocolate", "Terracotta", "Caramel", "Ivory White"), scene_sun,
            "sun over hills: chocolate lines on ivory, caramel disc, terracotta rays"),
    "moon": (("Charcoal", "Ivory White", "Caramel", "Desert Tan"), scene_moon,
             "crescent and stars: ivory lights on a charcoal-lined tan sky, caramel cloud"),
    "tree": (("Dark Chocolate", "Terracotta", "Caramel", "Desert Tan"), scene_tree,
             "fruiting tree: chocolate lines on tan, caramel crown, terracotta fruit"),
    "flame": (("Charcoal", "Terracotta", "Caramel", "Ivory White"), scene_flame,
              "flame in a bowl: charcoal on ivory, terracotta and caramel fire"),
    "mountain": (("Charcoal", "Terracotta", "Ivory White", "Desert Tan"), scene_mountain,
                 "peaks and waves: charcoal on tan, ivory snow and foam, terracotta sun"),
}


def hexes(design):
    return [filaments.FILAMENTS[f][1] for f in DESIGNS[design][0]]


# ---- the frame ------------------------------------------------------------------------

def sword(c, h):
    """A sword standing point-up, h tall, centred on c: (blade, hilt furniture, grip)."""
    y0 = c[1] - h / 2
    blade = Polygon([(-1.5, y0 + 6.6), (1.5, y0 + 6.6), (1.5, y0 + h - 3.2), (0, y0 + h), (-1.5, y0 + h - 3.2)])
    guard = box(-4.2, y0 + 5.2, 4.2, y0 + 6.8).buffer(0.3)
    grip = box(-0.85, y0 + 2.2, 0.85, y0 + 5.4)
    pommel = disk((0, y0 + 1.5), 1.5, 24)
    sh = lambda g: affinity.translate(g, c[0], 0)
    return sh(blade), sh(unary_union([guard, pommel])), sh(grip)


def shield(c, w, h):
    """A heater shield centred on c."""
    x, y = c
    half = [(0, h / 2), (-w / 2, h / 2), (-w / 2, h * 0.05), (-w * 0.36, -h * 0.26), (0, -h / 2)]
    pts = half + [(-px, py) for px, py in reversed(half[1:-1])]
    return affinity.translate(Polygon(pts).buffer(0.5).buffer(-0.5), x, y)


def frame(cv):
    """Paint the frame on an all-ink canvas: display plate (the counter) and art plate, the two window
    boxes, the slash between them, a sword by power and a shield by toughness. Returns the art plate."""
    disp, art = rrect(DISPLAY, PLATE_R), rrect(ART, PLATE_R)
    cv.paint(PAPER, disp)
    cv.paint(PAPER, art)
    for n, _ in WHEELS:
        o = face_opening(n)
        cv.paint(INK, o.buffer(WIN_MAT + WIN_RULE, join_style="round"), disp)
        cv.paint(PAPER, o.buffer(WIN_MAT, join_style="round"), disp)
    # the slash: a tapered stroke through the middle of the plate
    p, t = np.array(WIN_C[FRONT_WHEEL]), np.array(WIN_C[REAR_WHEEL])
    mid = (p + t) / 2
    half = np.array([3.4, (DISPLAY[3] - DISPLAY[1]) / 2 - 3.0])
    cv.paint(INK, unary_union([taper([tuple(mid), tuple(mid + s * half)], 2.6, 0.9, n=16) for s in (-1, 1)]), disp)
    # sword (power) at the left end, shield (toughness) at the right end
    po, to = face_opening(FRONT_WHEEL).bounds, face_opening(REAR_WHEEL).bounds
    xs = (DISPLAY[0] + po[0] - WIN_MAT - WIN_RULE) / 2
    blade, hilt, grip = sword((xs, (DISPLAY[1] + DISPLAY[3]) / 2), DISPLAY[3] - DISPLAY[1] - 5.0)
    for g, fill in ((blade, PAPER), (hilt, ACC_B)):
        cv.paint(INK, g.buffer(0.3, join_style="round"), disp)
        cv.paint(fill, g.buffer(-0.3, join_style="round"), disp)
    cv.paint(INK, grip, disp)
    xh = (DISPLAY[2] + to[2] + WIN_MAT + WIN_RULE) / 2
    sh = shield((xh, mid[1]), 8.4, 12.5)
    cv.paint(INK, sh.buffer(0.35, join_style="round"), disp)
    cv.paint(PAPER, sh.buffer(-0.35, join_style="round"), disp)
    cv.paint(ACC_A, sh.buffer(-1.5, join_style="round"), disp)
    cv.paint(INK, unary_union([box(xh - 0.45, mid[1] - 6, xh + 0.45, mid[1] + 6),
                               box(xh - 4, mid[1] + 0.9, xh + 4, mid[1] + 1.8)]).intersection(sh.buffer(-1.5)), disp)
    # a lozenge in each empty corner: under the power box, over the toughness box
    for cx, cy in (((po[0] + po[2]) / 2, (DISPLAY[1] + po[1] - WIN_MAT - WIN_RULE) / 2),
                   ((to[0] + to[2]) / 2, (DISPLAY[3] + to[3] + WIN_MAT + WIN_RULE) / 2)):
        cv.paint(INK, Polygon([(cx - 3.6, cy), (cx, cy + 2.0), (cx + 3.6, cy), (cx, cy - 2.0)]), disp)
        cv.paint(ACC_B, Polygon([(cx - 1.9, cy), (cx, cy + 1.05), (cx + 1.9, cy), (cx, cy - 1.05)]), disp)
    return art


def finish(cv, card):
    regions = {k: g.intersection(card).buffer(0) for k, g in cv.r.items()}
    regions = vc.absorb_islands(vc.fill_slivers(regions))
    return {k: vc.tidy(g) for k, g in regions.items()}


def front_regions(card, design):
    cv = vc.Canvas(card)
    clip = frame(cv)
    DESIGNS[design][1](cv, clip)
    return finish(cv, card)


def back_regions(card):
    """The back: ink edge, paper field, an eight-point star in accent B."""
    cv = vc.Canvas(card)
    cv.paint(PAPER, card.buffer(-EDGE).buffer(-0.3).buffer(0.3))
    c = (CX, CARD_H / 2)
    s = unary_union([star(c, 11.0, 3.2), star(c, 6.8, 3.2, rot=45)])
    cv.paint(INK, s.buffer(0.4, join_style="round"))
    cv.paint(ACC_B, s.buffer(-0.4, join_style="round"))
    cv.paint(INK, disk(c, 2.0, 32))
    regions = {k: g.intersection(card).buffer(0) for k, g in cv.r.items()}
    return {k: vc.tidy(g) for k, g in vc.absorb_islands(regions).items()}


def report(design, card, regions):
    names = DESIGNS[design][0]
    tiling = sum(g.area for g in regions.values())
    print(f"{design}: front tiling {tiling:.2f} of {card.area:.2f} mm^2: " +
          ", ".join(f"{names[k]} {100 * regions[k].area / card.area:.1f}%" for k in range(4)))
    for k, g in regions.items():
        thin = g.difference(g.buffer(-BEAD / 2).buffer(BEAD / 2)).area
        small = [round(p.area, 2) for p in vt.polys_of(g) if p.area < MIN_ISLAND]
        print(f"  {names[k]:14s}: {len(vt.polys_of(g)):4d} islands, {thin:.2f} mm^2 thinner than {BEAD} mm" +
              (f", small islands {small}" if small else ""))


# ---- the plate -------------------------------------------------------------------------

def mirror(g, x=None):
    return affinity.scale(g, -1, 1, origin=(CX if x is None else x, 0))


def layers(z0, z1):
    n = int(round((z1 - z0) / LAYER))
    return [(round(z0 + i * LAYER, 3), round(z0 + (i + 1) * LAYER, 3)) for i in range(n)]


def build_parts(m, regions, back):
    """Every prism of the plate as {object: [(z0, z1, shape, slot)]}, in each part's PRINT frame.
    Front and wheels print face-down (mirrored); back and divider print as they sit (not mirrored; only
    the back's art, drawn as seen from behind, is mirrored)."""
    card = m["card"]
    holes = lambda d: unary_union([opening(n, d) for n, _ in WHEELS])
    well = lambda d: opening(REAR_WHEEL, d)
    front = [(0.0, INLAY, mirror(regions[k].difference(holes(INLAY / 2))), k) for k in range(4)]
    for z0, z1 in layers(INLAY, PLATE_T):
        g = card.difference(holes((z0 + z1) / 2))
        if z0 >= PLATE_T - SOCKET_DEPTH - 1e-9:
            g = g.difference(m["sock"][FRONT_WHEEL])
        front.append((z0, z1, mirror(g), PAPER))
    for z0, z1 in layers(PLATE_T, FRONT_T):
        g = m["spacer_front"].difference(well((z0 + z1) / 2))
        if z0 >= FRONT_T - GROOVE_DEPTH - 1e-9:
            g = g.difference(m["slots"])
        front.append((z0, z1, mirror(g), PAPER))
    z_sp = BASE_T + CAVITY
    back_parts = [(0.0, INLAY, mirror(back[k]), k) for k in range(4)] + [
        (INLAY, BASE_T, card, PAPER),
        (BASE_T, z_sp, m["spacer_back"], PAPER),
        (BASE_T, z_sp + DIV_T - (SOCKET_DEPTH - PIN_ENTRY), m["pin"][REAR_WHEEL], PAPER),
        (z_sp, z_sp + DIV_T + TONGUE_H, m["ridge"], PAPER)]
    divider = [(0.0, DIV_T, m["divider"], PAPER),
               (DIV_T, DIV_T + CAVITY + PIN_ENTRY, m["pin"][FRONT_WHEEL], PAPER)]
    parts = {"front": front, "back": back_parts, "divider": divider}
    for name, wh in m["whs"].items():
        wx = wh["C"][0]
        digits = unary_union(wh["groups"])
        parts[name] = [(0.0, INLAY, mirror(digits, wx), INK),
                       (0.0, INLAY, mirror(wh["disc"].difference(digits), wx), PAPER),
                       (INLAY, WHEEL_T, mirror(wh["disc"], wx), PAPER)]
    return parts


def at_z(prisms, z):
    """The solid of a part (print frame) at height z."""
    return unary_union([g for z0, z1, g, _ in prisms if z0 - 1e-9 <= z < z1 - 1e-9])


def assembly_check(m, parts):
    """Assemble the parts AS PRINTED: turn the face-down ones over, stack them, and check the fits and
    that both wheels show every value centred in the aperture the printed parts actually leave."""
    card = m["card"]
    front = lambda z: mirror(at_z(parts["front"], THICK - z))      # assembled z -> the face-down print's z
    back = lambda z: at_z(parts["back"], z)
    div0 = BASE_T + CAVITY
    div = lambda z: at_z(parts["divider"], z - div0)
    eps = 0.02
    # tongue: on the back, through the divider, into the front
    ridge = back(div0 + DIV_T + TONGUE_H / 2)
    assert abs(ridge.area - m["ridge"].area) < 1e-3
    for label, hole in (("divider slots", card.difference(div(div0 + DIV_T / 2))),
                        ("front groove", card.difference(front(div0 + DIV_T + TONGUE_H / 2)))):
        assert hole.buffer(-(TONGUE_CLR - eps)).contains(ridge), f"the tongue doesn't clear the {label} by {TONGUE_CLR}"
        assert not hole.buffer(-(TONGUE_CLR + eps)).contains(ridge), f"the {label} are looser than {TONGUE_CLR}"
    top = max(z1 for _, z1, _, _ in parts["back"])
    assert top <= div0 + DIV_T + GROOVE_DEPTH - 0.15, "the tongue bottoms out in the groove"
    # pins: rear pin from the back into the divider, front pin from the divider into the face plate
    rear_pin = back(div0 + DIV_T / 2).difference(ridge)
    assert card.difference(div(div0 + DIV_T / 2)).buffer(-(SOCKET_CLR - eps)).contains(rear_pin), "rear pin vs divider hole"
    front_pin = div(div0 + DIV_T + CAVITY / 2)
    sock = card.difference(front(THICK - PLATE_T + SOCKET_DEPTH / 2)).difference(
        unary_union([opening(n, 0) for n, _ in WHEELS]))
    assert sock.buffer(-(SOCKET_CLR - eps)).contains(front_pin), "front pin vs its socket"
    pin_top = div0 + max(z1 for _, z1, _, _ in parts["divider"])
    assert THICK - PLATE_T < pin_top <= THICK - PLATE_T + SOCKET_DEPTH - 0.15, "front pin length"
    # each wheel: flipped over, dropped on its pin; clear of its cavity and the other level
    apertures = {REAR_WHEEL: card.difference(div(div0 + DIV_T / 2)),
                 FRONT_WHEEL: card.difference(front(THICK - PLATE_T + LAYER / 2))}
    spacers = {REAR_WHEEL: back(BASE_T + CAVITY / 2), FRONT_WHEEL: front(div0 + DIV_T + CAVITY - LAYER / 2)}
    pins = {REAR_WHEEL: rear_pin, FRONT_WHEEL: front_pin}
    worst = 0.0
    for name, spin in WHEELS:
        wx = WHEEL_C[name][0]
        inkd, disc = mirror(parts[name][0][2], wx), mirror(parts[name][2][2], wx)
        hole = Polygon(disc.interiors[0])
        pc = np.array(pins[name].centroid.coords[0])
        assert np.allclose(pc, WHEEL_C[name], atol=0.01), f"printed {name} pin at {pc}, design {WHEEL_C[name]}"
        assert np.allclose(hole.centroid.coords[0], pc, atol=0.01), f"{name} hub is off its pin"
        assert abs(hole.exterior.distance(Point(*pc)) - PIN_D / 2 - PIN_CLR) < 0.03, f"{name} hub clearance"
        gap = Polygon(disc.exterior).distance(spacers[name].difference(pins[name].buffer(0.5)))
        assert gap >= WHEEL_CLR - 0.03, f"{name} wheel is {gap:.2f} mm from its cavity wall"
        win = window(name)
        ap = [p for p in vt.polys_of(apertures[name]) if p.intersects(win)]
        assert len(ap) == 1 and ap[0].buffer(0.01).contains(win) and ap[0].area < win.area * 1.12, \
            f"the printed aperture over the {name} wheel isn't its window"
        wc = np.array(win.centroid.coords[0])
        for i, v in enumerate(VALUES):
            shown = affinity.rotate(inkd, spin * STEP * i, origin=tuple(pc)).intersection(ap[0])
            want = digit(v, WIN_C[name])
            assert abs(shown.area - want.area) < 0.01 * want.area, f"{name} {v}: the aperture shows the wrong ink"
            b = np.array(shown.bounds)
            err = np.hypot((b[0] + b[2]) / 2 - wc[0], (b[1] + b[3]) / 2 - wc[1])
            worst = max(worst, err)
            assert err < 0.1, f"{name} {v} is {err:.2f} mm off the window centre"
    # the well passes the power wheel's level inside solid spacer
    lvl = front(div0 + DIV_T + CAVITY / 2)
    well_wall = card.difference(lvl).difference(m["cav"][FRONT_WHEEL].buffer(0.01))
    w = [p for p in vt.polys_of(well_wall) if p.intersects(window(REAR_WHEEL))]
    assert len(w) == 1 and w[0].distance(m["cav"][FRONT_WHEEL]) >= WELL_WALL - 0.05, "the well breaks into the power cavity"
    # stack heights
    assert abs(max(z1 for _, z1, _, _ in parts["front"]) - FRONT_T) < 1e-9
    assert abs(div0 + DIV_T + FRONT_T - THICK) < 1e-9
    print(f"assembly check (parts as printed): tongue {TONGUE_CLR} mm inside the divider's slots and the front's "
          f"groove; pins in their sockets; hubs {PIN_CLR} mm; both wheels show all {len(VALUES)} values centred "
          f"(worst {worst:.3f} mm); the well's wall to the power cavity is {w[0].distance(m['cav'][FRONT_WHEEL]):.2f} mm")


def plate_offsets(m):
    """Where each object sits on the bed: three cards in a row, the wheels behind them."""
    R = R_WHEEL
    off = {"front": (0.0, 0.0), "back": (CARD_W + PLATE_GAP, 0.0), "divider": (2 * (CARD_W + PLATE_GAP), 0.0)}
    for i, (name, _) in enumerate(WHEELS):
        C = m["whs"][name]["C"]
        off[name] = (R + PROTRUDE + i * (2 * R + PLATE_GAP) - C[0], CARD_H + PLATE_GAP + R - C[1])
    return off


def write_plate(m, parts, design, folder):
    folder.mkdir(parents=True, exist_ok=True)
    for f in list(folder.glob("*.stl")) + list(folder.glob("slice_args*.txt")):
        f.unlink()
    off = plate_offsets(m)
    files, slots = [], []
    cm3 = [0.0] * 4
    for name, prisms in parts.items():
        for i, (z0, z1, g, slot) in enumerate(prisms):
            if g.is_empty:
                continue
            mesh = vt.extrude(vc.snappable(g), z0, z1)
            if mesh is None:
                continue
            mesh.apply_translation([off[name][0], off[name][1], 0])
            fn = folder / f"{name}_{i:02d}_{SLOT_NAMES[slot]}.stl"
            mesh.export(fn)
            files.append(fn.name)
            slots.append(slot + 1)
            cm3[slot] += g.area * (z1 - z0) / 1000
    pre = " ".join(f'{a} "{b}"' for a, b in zip(SLICER_PRESETS[::2], SLICER_PRESETS[1::2]))
    (folder / "slice_args.txt").write_text(
        " ".join(files) + f" --assemble --extruders {','.join(map(str, slots))} "
        f"--colors \"{','.join(hexes(design))}\" " + pre + " " + " ".join("--set " + x for x in SLICER_SET) + "\n")
    names = DESIGNS[design][0]
    print(f"  {design}: {len(files)} STLs -> {folder}; solid grams per slot (1.24 g/cm^3): " +
          ", ".join(f"{i + 1} {names[i]} {v * 1.24:.2f}" for i, v in enumerate(cm3)))


# ---- previews -----------------------------------------------------------------------------

def nozzle_sim(g):
    return g.buffer(-0.21).buffer(0.21).buffer(0.15).buffer(-0.15)


def shade(h, k):
    """Hex colour h darkened by factor k (for the well's slopes and the wheel deep in it)."""
    c = [int(h[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{int(v * k):02x}" for v in c)


def draw_face(ax, m, regions, hx, pt, sim=False):
    """The face with the power and toughness wheels turned to pt = (p, t)."""
    card = m["card"]
    for name in (REAR_WHEEL, FRONT_WHEEL):                  # the rear wheel lies under the front one
        wh, v = m["whs"][name], pt[[n for n, _ in WHEELS].index(name)]
        deep = 0.86 if name == REAR_WHEEL else 0.95
        vd.draw(ax, turned(wh["disc"], wh, v), shade(hx[PAPER], deep))
        vd.draw(ax, turned(unary_union(wh["groups"]), wh, v), hx[INK])
    aperture = unary_union([opening(n, PLATE_T if n == FRONT_WHEEL else FRONT_T) for n, _ in WHEELS])
    face_holes = unary_union([face_opening(n) for n, _ in WHEELS])
    vd.draw(ax, face_holes.difference(aperture), shade(hx[PAPER], 0.9))       # the bevels
    vd.draw(ax, regions[PAPER].difference(face_holes), hx[PAPER])
    for k in (INK, ACC_A, ACC_B):
        g = regions[k].difference(face_holes)
        vd.draw(ax, nozzle_sim(g) if sim else g, hx[k])
    ax.set_aspect("equal"); ax.set_facecolor("#9aa0a6"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlim(-PROTRUDE - 1.5, CARD_W + PROTRUDE + 1.5); ax.set_ylim(-1.5, CARD_H + 1.5)


def designs_preview(m, faces, back, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_, axes = plt.subplots(1, 7, figsize=(33, 7.2))
    shown = [(7, 5), (0, 1), (3, 3), (9, 9), (2, 4)]
    for ax, (design, regions), pt in zip(axes, faces.items(), shown):
        draw_face(ax, m, regions, hexes(design), pt)
        ax.set_title(f"{design}  {pt[0]}/{pt[1]}\n" + " / ".join(DESIGNS[design][0]), fontsize=9)
    first = next(iter(faces))
    draw_face(axes[5], m, faces[first], hexes(first), (8, 6), sim=True)
    axes[5].set_title(f"{first}: nozzle simulation (colours opened 0.42 mm)", fontsize=9)
    ax = axes[6]
    for k in range(4):
        vd.draw(ax, back[k], hexes(first)[k])
    ax.set_aspect("equal"); ax.set_facecolor("#9aa0a6"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlim(-PROTRUDE - 1.5, CARD_W + PROTRUDE + 1.5); ax.set_ylim(-1.5, CARD_H + 1.5)
    ax.set_title("back (as seen from behind)", fontsize=9)
    plt.tight_layout()
    plt.savefig(path, dpi=110)
    plt.close(fig_)
    print(f"preview -> {path}")


def design_preview(m, design, regions, path):
    """One design at print scale: the face, and what a 0.4 nozzle keeps of it."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_, axes = plt.subplots(1, 2, figsize=(13, 9.4))
    for ax, sim, pt in zip(axes, (False, True), ((7, 5), (2, 8))):
        draw_face(ax, m, regions, hexes(design), pt, sim)
        ax.set_title(f"{design} {pt[0]}/{pt[1]}" + (" (nozzle simulation)" if sim else "") + "\n" +
                     " / ".join(DESIGNS[design][0]), fontsize=10)
    plt.tight_layout()
    plt.savefig(path, dpi=110)
    plt.close(fig_)


def parts_preview(m, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    card, whs = m["card"], m["whs"]
    fig_, axes = plt.subplots(1, 5, figsize=(30, 7.2), gridspec_kw=dict(width_ratios=[1, 1, 1, 1.25, 1.1]))
    solid, light, red, dark, blue = "#7a6a58", "#e8d2a8", "#b03a2e", "#3a2d25", "#1f5fa8"
    ax = axes[0]
    vd.draw(ax, card, light); vd.draw(ax, m["spacer_back"], solid); vd.draw(ax, m["ridge"], red)
    vd.draw(ax, m["pin"][REAR_WHEEL], dark)
    ax.plot(*np.asarray(whs[REAR_WHEEL]["disc"].exterior.coords).T, color=blue, lw=0.8)
    ax.set_title("back: base, spacer (brown), tongue dashes (red), toughness pin; wheel outline blue", fontsize=9)
    ax = axes[1]
    vd.draw(ax, m["divider"], solid); vd.draw(ax, m["pin"][FRONT_WHEEL], dark)
    ax.plot(*np.asarray(whs[FRONT_WHEEL]["disc"].exterior.coords).T, color=blue, lw=0.8)
    ax.set_title("divider: toughness window, tongue slots, hole for the toughness pin; power pin on top", fontsize=9)
    ax = axes[2]
    vd.draw(ax, card, light)
    vd.draw(ax, m["spacer_front"].difference(opening(REAR_WHEEL, PLATE_T)), solid)
    vd.draw(ax, m["slots"], red); vd.draw(ax, m["sock"][FRONT_WHEEL], dark)
    for n, _ in WHEELS:
        vd.draw(ax, opening(n, PLATE_T), "#ffffff")
    ax.set_title("front underside (front-view frame): spacer, groove (red), pin socket, the two openings", fontsize=9)
    for ax in axes[:3]:
        ax.set_xlim(-PROTRUDE - 1.5, CARD_W + PROTRUDE + 1.5); ax.set_ylim(-1.5, CARD_H + 1.5)
    ax = axes[3]
    R = R_WHEEL
    for i, (name, _) in enumerate(WHEELS):
        wh = whs[name]
        sh = lambda g: affinity.translate(g, (2 * R + 3) * i - wh["C"][0], -wh["C"][1])
        vd.draw(ax, sh(wh["disc"]), "#f4f1ea"); vd.draw(ax, sh(unary_union(wh["groups"])), dark)
    ax.set_xlim(-R - 1, 3 * R + 4); ax.set_ylim(-R - 1, R + 1)
    ax.set_title("power and toughness wheels (faces): they count opposite ways round", fontsize=9)
    # section through the toughness well, looking from the right: y across, z up
    ax = axes[4]
    wy = WIN_C[REAR_WHEEL][1]
    y0, y1 = 0.0, wy + WIN_WH[1] / 2 + 6
    z = [0, BASE_T, BASE_T + CAVITY, BASE_T + CAVITY + DIV_T, THICK - PLATE_T, THICK]
    vd.draw(ax, box(y0, z[0], y1, z[1]), solid)
    rc = WHEEL_C[REAR_WHEEL]
    vd.draw(ax, box(y0, z[1], rc[1] - R_WHEEL - WHEEL_CLR, z[2]), solid)
    vd.draw(ax, box(rc[1] - R_WHEEL, z[1], y1, z[1] + WHEEL_T), "#f4f1ea")
    win = window(REAR_WHEEL).bounds
    vd.draw(ax, unary_union([box(y0, z[2], win[1], z[3]), box(win[3], z[2], y1, z[3])]), "#a08a6c")
    for za, zb in layers(0, FRONT_T):
        o = opening(REAR_WHEEL, (za + zb) / 2).bounds
        vd.draw(ax, unary_union([box(y0, THICK - zb, o[1], THICK - za), box(o[3], THICK - zb, y1, THICK - za)]), light)
    vd.draw(ax, box(win[1] + WIN_PAD[1], z[1] + WHEEL_T - INLAY, win[3] - WIN_PAD[1], z[1] + WHEEL_T), dark)
    ax.plot([win[1], win[1] - 8], [z[3], z[3] + 8], color=blue, lw=0.8, ls="--")
    ax.set_xlim(y0 - 0.5, y1); ax.set_ylim(-0.5, THICK + 3)
    ax.set_title("section through the toughness well (bottom edge at left): back, wheel, divider,\n"
                 "front with the 45-degree bevel; dashed: the 45-degree sight line to the digit's foot", fontsize=9)
    for ax in axes:
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    plt.tight_layout()
    plt.savefig(path, dpi=110)
    plt.close(fig_)
    print(f"preview -> {path}")


# ---- build --------------------------------------------------------------------------------

def main():
    only = sys.argv[1:]
    m = mechanism()
    card = m["card"]
    back = back_regions(card)
    faces = {}
    checked = False
    for design in DESIGNS:
        if only and design not in only:
            continue
        regions = front_regions(card, design)
        report(design, card, regions)
        parts = build_parts(m, regions, back)
        if not checked:
            assembly_check(m, parts)
            checked = True
        write_plate(m, parts, design, OUT / design)
        faces[design] = regions
        design_preview(m, design, regions, OUT / f"{design}_preview.png")
    designs_preview(m, faces, back, OUT / "designs_preview.png")
    parts_preview(m, OUT / "parts_preview.png")


if __name__ == "__main__":
    main()
