#!/usr/bin/env python3
"""
Vampire counter token: the colour-fill alt art of the vampire-arcana card. Same 70.5 x 88 card, same
tarot frame (black card edge and rules, "VAMPIRE" in Georgia caps on a white title plate, power and
toughness on two wheels, 1-9 each, in ruled windows in the footer's corners with a bat-shaped "/"
between them), same face-down flat inlay
and same back. Only the art plate differs: here it is flat colour (an elder vampire knight in a red
cloak before a blood moon, copper cloud streaks, a black castle), where arcana is a woodcut.

Spec: see README.md in this folder.

This module also HOSTS everything the two cards share, and models/vampire-arcana imports it:
  * the card frame: `frame()` paints the plates, title, window boxes and the bat slash; `finish()` clears
    the window mats and cleans the regions (slivers, islands, grid snap); `back_regions()` is the back;
  * the mechanism: power and toughness wheels (V-notch grip), hubs on axle pins, tongue-and-groove
    joint (v3: no detent; v4: two wheels, rims out of the left and right edges);
  * the scene helpers for the widened card: `xr()` / `xc()` re-anchor x, `cloak_widen()`;
  * the face-down build `write_plate()` and the `preview()` sheet.
A card is then just a painter's-algorithm scene in the art plate (see `front_regions()` here).

Parts (printed side by side on one plate):
  front  face-down: a 0.4 mm colour inlay (4 layers at 0.10 mm), white above, groove + pin socket
         underneath, window through
  back   base plate + spacer frame with the two wheel cavities, two axle pins and a tongue round the
         edge; its face has the black edge and gold crescent inlaid in the same layers
  power, toughness   face-down wheels: black digits 1-9 inlaid flat in white

Every colour change is in the inlay layers (0-0.4 mm), however much ink the art has.
Printed with a 0.2 mm nozzle at 0.10 mm layers (v3).

Run (from the repo root):
    .venv\\Scripts\\python.exe models\\vampire-counter\\vampire_counter.py
Outputs (millimetres) go to models\\vampire-counter\\out\\
    parts/<object>_<n>_<colour>.stl   parts laid out as on the plate; load as ONE object (--assemble)
    parts/slice_args.txt              the matching slice_bambu.py arguments
    counter_preview.png               the face at 1/1, 3/5, 9/9, a nozzle simulation, and the back
    parts_preview.png                 back (spacer, tongue, pins), front underside, joint section, wheels
    text_cache.json                   the Windows-font text as outlines, for builds without the fonts
"""
import importlib.util
import tempfile
from pathlib import Path

import numpy as np
from matplotlib.font_manager import FontProperties
from scipy.interpolate import splev, splprep
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


# Shared helpers: extrusion (vampire-token), text layout and drawing (vampire-dial).
vt = _load("vampire_token", HERE.parent / "vampire-token" / "vampire_token.py")
vd = _load("vampire_dial", HERE.parent / "vampire-dial" / "vampire_dial.py")

# ---- Parameters (mm) -------------------------------------------------------
# Palette: AMS slots 1-4, shared with vampire-arcana (the same spools: black, red, copper, white).
PALETTE = [("ink", "#1E1A18"), ("blood", "#9B1B1E"), ("gold", "#B87333"), ("paper", "#F4F1EA")]
INK, BLOOD, GOLD, PAPER = range(4)

# v4: 70.5 mm wide (was 63, standard token size), so two side-by-side wheels with 8 mm digits fit.
CARD_W, CARD_H, CORNER_R = 70.5, 88.0, 3.0
CX = CARD_W / 2
# The scenes were drawn on the 63 mm card. Widening it: left-anchored x stays, centred x moves by DX,
# right-anchored x by 2 DX (see xr()); the knight and moon follow CX.
W0 = 63.0
DX = (CARD_W - W0) / 2

# ---- the card frame (shared with vampire-arcana) ----
# Plates (white interiors) as (x0, y0, x1, y1). The black between them is the whole border:
# 1.8 mm card edge, 1.2 mm rules. The footer is sized to frame the dial windows, which the wheels fix.
EDGE, RULE = 1.8, 1.2
FOOTER = (EDGE, EDGE, CARD_W - EDGE, 18.0)
ART = (EDGE, FOOTER[3] + RULE, CARD_W - EDGE, 72.6)
TITLE_BOX = (EDGE, ART[3] + RULE, CARD_W - EDGE, CARD_H - EDGE)
PLATE_R = CORNER_R - EDGE        # concentric with the card's corners
CLOAK_K = (CARD_W / 2 - EDGE) / (W0 / 2 - EDGE)   # cloaks widen with the art plate to keep filling its corners

# Title: black roman caps on the white plate, with generous margins (Georgia: of the installed romans
# it keeps the most ink, 99.8 %, through a 0.42 mm open / 0.3 mm close).
TITLE = "VAMPIRE"
TITLE_FONT = r"C:\Windows\Fonts\georgia.ttf"
TITLE_CAP = 6.0
TITLE_TRACK = 1.1
TITLE_BOLDEN = 0.06

# Dial window frames: white mat, then a black rule, like the tarot numeral box. Between the power and
# toughness windows, a bat diving along a "/" diagonal is the P/T slash.
WIN_MAT = 0.7
WIN_RULE = 0.7
SLASH_BAT_LEN = 15.0             # wing tip to wing tip, along the diagonal
SLASH_BAT_ANGLE = 62.0           # degrees from horizontal: the wings run up to the right, like "/"
SLASH_BAT_W = 3.0                # wing depth

# Face-down inlay
INLAY = 0.4                      # two 0.2 mm layers: opaque enough for ink, red and gold over white
BACK_ART = True                  # border + crescent inlaid on the card's back (no extra swaps)

# Digits: Bahnschrift Bold Condensed, one digit per wheel (v4: power and toughness are separate).
DIGIT_FONT = (r"C:\Windows\Fonts\bahnschrift.ttf", {"wght": 700, "wdth": 75})
DIGIT_H = 8.0                   # digit cap height, as v3's "N/N" digits
DIGIT_BOLDEN = 0.05
VALUES = range(1, 10)
STEP = 360 / len(VALUES)        # 40 degrees per value
WIN_PAD = (0.8, 0.6)            # window margin around the widest digit (x, y)
WIN_R = 1.5

# Wheels: (name, side). Power is bottom-left with its rim out of the left edge, toughness bottom-right
# out of the right edge. Each window sits DIGIT_R straight below its wheel's centre. Pushing either
# rim UP counts up (so the power wheel turns clockwise, the toughness wheel counter-clockwise).
WHEELS = (("power", -1), ("toughness", +1))
WIN_ANGLE = -90.0
DIGIT_R = 11.2                  # smallest ring radius that hides both neighbours of a single 8 mm digit (searched)
PROTRUDE = 2.5                  # rim past the card's side edge
BOTTOM_WALL = 1.0               # spacer between a cavity and the card's bottom edge
MID_WALL = 1.0                  # spacer between the two cavities (sets the narrowest card, MIN_CARD_W)
CHANNEL_MARGIN = 0.4
WHEEL_RIM = 0.8                 # rim between the digit channel and the notch bottoms
# 9 V notches: the thumb grip (the "gear" teeth). v3 dropped the spring detent that seated in them:
# a wheel's own friction in the case holds its value, and the arm was a part that could fail.
GRIP_ANGLE = 90.0               # a notch sits at the top of each wheel
NOTCH_DEPTH = 1.3
NOTCH_FLANK = 35.0              # flank angle from the rim's tangent
NOTCH_EDGE_R = 0.6              # rounding of the notch's rim edges
WHEEL_T = 1.8                   # disc thickness (digits inlaid in its face, which prints on the plate)
PIN_D, PIN_CLR = 6.0, 0.4       # axle pin; radial clearance in the wheel's hole (v3: 0.25 was too snug)
WHEEL_CLR = 0.4                 # radial clearance wheel -> cavity wall
AX_CLR = 0.4                    # axial play

# Back
BASE_T = 0.6
CAVITY = WHEEL_T + AX_CLR       # 2.2
BACK_T = BASE_T + CAVITY        # 2.8
# Tongue and groove (v3, replaces 6 Ø2 pegs): a ridge on the spacer's top face runs round the card
# edge wherever the wheel cavities leave room (v4: the top and both sides down to the wheels, and the
# bottom edge between them); the front's underside has the matching groove. It locates the front in X and Y
# along most of the edge and gives the glue a long line instead of 6 dots.
TONGUE_W, TONGUE_H = 1.2, 0.6   # ~5 lines wide at a 0.2 nozzle, 6 layers tall at 0.10 mm
TONGUE_INSET = 2.0              # card edge -> tongue centreline (front groove keeps a 1.25 mm outer wall)
TONGUE_CLR = 0.15               # per side, in the groove
TONGUE_GAP = 1.2                # tongue edge -> wheel cavity, minimum
TONGUE_MIN_LEN = 8.0            # shorter runs are dropped
GROOVE_DEPTH = TONGUE_H + 0.2   # 0.2 mm of glue room above the tongue (and the pin)
SOCKET_D_CLR = 0.15             # per side, the pin's socket in the front

# Front
FRONT_T = 2.0

# Printability limits for the art (checked, not just hoped for). The art was designed for a 0.4
# nozzle; these limits still hold (conservatively) on the 0.2 nozzle used from v3.
BEAD = 0.45                     # narrower than this read as a broken bead on a 0.4 nozzle
MIN_ISLAND = 1.0                # mm^2

PLATE_GAP = 8.0
# v3: 0.2 mm nozzle, 0.10 mm layers (the 0.4 nozzle settings are in git history). Every height
# above is a multiple of 0.1 mm. The 0.2 nozzle preset's first layer is already slow (16 / 28 mm/s),
# so the old initial-layer overrides (30 / 60, meant to SLOW the 0.4 preset) are gone. The Arachne
# transition settings were tuned on the 0.4 nozzle; they're in % of the nozzle, so they carry over.
NOZZLE = 0.2
SLICER_PRESETS = ["--machine", "Bambu Lab A1 0.2 nozzle", "--process", "0.10mm Standard @BBL A1 0.2 nozzle",
                  "--filament", "Bambu PLA Basic @BBL A1 0.2 nozzle"]
SLICER_SET = ["wall_generator=arachne", "wall_transition_angle=30", "wall_transition_filter_deviation=50%",
              "min_bead_width=50%", "wall_transition_length=50%"]

# ---- this card's scene (the colour-fill alt art) ----
HEAD = (CX, 50.2)                # the knight's face centre; his local frame is 1 unit = 1 mm
MOON_C, MOON_R = (CX, 51.7), 17.0
LINE = 0.7                       # black outline / strand width (over a bead)
# ---------------------------------------------------------------------------


# ---- small geometry helpers -------------------------------------------------

def rrect(b, r):
    x0, y0, x1, y1 = b
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=16)


def disk(c, r, n=64):
    return Point(*c).buffer(r, quad_segs=n)


def spline(pts, closed=True, n=300):
    """Smooth closed shape (or open LineString) through the points."""
    p = np.asarray(pts, float)
    if closed:
        p = np.vstack([p, p[:1]])
    tck, _ = splprep(p.T, s=0, per=closed, k=3 if len(pts) > 3 else len(pts) - 1)
    x, y = splev(np.linspace(0, 1, n), tck)
    return Polygon(np.c_[x, y]).buffer(0) if closed else LineString(np.c_[x, y])


def taper(pts, w0, w1, n=60):
    """A brush stroke along a smooth curve, width w0 -> w1 (round ends)."""
    line = spline(pts, closed=False, n=n)
    cs = np.asarray(line.coords)
    ws = np.linspace(w0, w1, len(cs))
    circles = [Point(*c).buffer(w / 2, quad_segs=12) for c, w in zip(cs, ws)]
    return unary_union([a.union(b).convex_hull for a, b in zip(circles, circles[1:])])


def xr(x):
    """A right-anchored x of the 63 mm scenes on the widened card."""
    return x + 2 * DX


def xc(x):
    """A centred x of the 63 mm scenes on the widened card."""
    return x + DX


def cloak_widen(g, y0=-17.0, y1=-31.0):
    """Widen a cloak shape (knight's local frame) with the art plate: unchanged at the shoulders (y0,
    under the pauldrons, so no sliver peeks out above them), CLOAK_K times wider from y1 down."""
    from shapely.ops import transform

    def f(x, y):
        t = np.clip((y0 - np.asarray(y)) / (y0 - y1), 0, 1)
        return np.asarray(x) * (1 + (CLOAK_K - 1) * t), y
    return transform(f, g)


def mirror(g, x=CX):
    return affinity.scale(g, -1, 1, origin=(x, 0))


def sym(g, x=CX):
    return unary_union([g, mirror(g, x)])


def sym_pts(half):
    """Left half outline from top-centre to bottom-centre -> the full symmetric closed outline."""
    right = [(-x, y) for x, y in reversed(half[1:-1])]
    return list(half) + right


# ---- fonts and text ---------------------------------------------------------

def digit_font():
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    src, axes = DIGIT_FONT
    if not Path(src).exists():
        print(f"  note: {src} not found; digits come from text_cache.json (else DejaVu Sans Bold)")
        return FontProperties(family="DejaVu Sans", weight="bold")
    dst = Path(tempfile.gettempdir()) / f"vampire_counter_{Path(src).stem}_{axes['wght']}_{axes['wdth']}.ttf"
    if not dst.exists():
        instantiateVariableFont(TTFont(src), axes).save(dst)
    return FontProperties(fname=str(dst))


DFONT = digit_font()


def digit_text(v, centre):
    """One digit, DIGIT_H tall, bbox centred on centre."""
    g = vd.text_cache(HERE / "text_cache.json", f"digit_{v}", lambda: _digit_text(v), DIGIT_FONT[0])
    return affinity.translate(g, *centre)


def _digit_text(v):
    k = (DIGIT_H - 2 * DIGIT_BOLDEN) / vd.glyphs("8", DFONT).bounds[3]
    g = affinity.scale(vd.glyphs(str(v), DFONT), k, k, origin=(0, 0)).buffer(DIGIT_BOLDEN, join_style="round")
    b = g.bounds
    return affinity.translate(g, -(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2)


def title_text():
    return vd.text_cache(HERE / "text_cache.json", "title", _title_text, TITLE_FONT)


def _title_text():
    if Path(TITLE_FONT).exists():
        fp = FontProperties(fname=TITLE_FONT)
    else:
        print(f"  warning: {TITLE_FONT} not found and not cached, title falls back to DejaVu Serif")
        fp = FontProperties(family="DejaVu Serif")
    cap = vd.glyphs("V", fp).bounds[3]
    k = (TITLE_CAP - 2 * TITLE_BOLDEN) / cap
    g = vd.lay_out([(TITLE, 1.0)], fp, k, TITLE_TRACK, TITLE_BOLDEN)
    b = g.bounds
    x0, y0, x1, y1 = TITLE_BOX
    print(f"title: {fp.get_name()}, caps {TITLE_CAP:.1f} mm, {b[2] - b[0]:.1f} mm long in a "
          f"{x1 - x0:.1f} x {y1 - y0:.1f} mm plate")
    return affinity.translate(g, (x0 + x1) / 2 - (b[0] + b[2]) / 2, (y0 + y1) / 2 - (b[1] + b[3]) / 2)


# ---- dial geometry (wheel centre at the origin, then placed) -------------------

def dial_layout():
    """Wheel radius, centres and window size. Both wheels are the same: digit ring DIGIT_R, window
    straight below the centre (WIN_ANGLE), centres PROTRUDE past their side edges."""
    a = np.radians(WIN_ANGLE)
    P0 = DIGIT_R * np.array([np.cos(a), np.sin(a)])          # window centre relative to a wheel centre
    texts = [digit_text(v, P0) for v in VALUES]
    W = max(t.bounds[2] - t.bounds[0] for t in texts) + 2 * WIN_PAD[0]
    H = max(t.bounds[3] - t.bounds[1] for t in texts) + 2 * WIN_PAD[1]
    win0 = vd.rounded_box(*P0, W, H, WIN_R)
    pts = np.array(win0.exterior.coords)
    r_out = np.hypot(*pts.T).max() + CHANNEL_MARGIN
    R = r_out + WHEEL_RIM + NOTCH_DEPTH
    cy = R + WHEEL_CLR + BOTTOM_WALL
    centres = {name: np.array([R - PROTRUDE if side < 0 else CARD_W + PROTRUDE - R, cy])
               for name, side in WHEELS}
    return centres, R, P0, (W, H)


WHEEL_C, R_WHEEL, WIN_P0, WIN_WH = dial_layout()
SPIN = {name: side for name, side in WHEELS}   # +1: a counter-clockwise turn counts up (rim pushed UP at the
                                                # right edge); -1: clockwise (rim pushed UP at the left edge)
# Narrowest card that holds both wheels side by side with MID_WALL of spacer between their cavities
MIN_CARD_W = 4 * R_WHEEL + 2 * WHEEL_CLR + MID_WALL - 2 * PROTRUDE


def win_centre(name):
    return WHEEL_C[name] + WIN_P0


def window(name=None):
    """One wheel's window, or (no name) both."""
    if name is None:
        return unary_union([window(n) for n, _ in WHEELS])
    return vd.rounded_box(*win_centre(name), *WIN_WH, WIN_R)


def wheel_geometry(name):
    C = WHEEL_C[name]
    win = window(name)
    pts = np.array(win.exterior.coords)
    r_out = np.hypot(*(pts - C).T).max() + CHANNEL_MARGIN
    r_in = Point(*C).distance(win) - CHANNEL_MARGIN
    r_valley = r_out + WHEEL_RIM
    R = r_valley + NOTCH_DEPTH
    channel = disk(C, r_out, 256).difference(disk(C, r_in, 256))
    notches = unary_union([notch(C, R, a) for a in np.radians(GRIP_ANGLE + STEP * np.arange(len(VALUES)))])
    hole = disk(C, PIN_D / 2 + PIN_CLR, 32)
    disc = disk(C, R, 512).difference(notches)
    disc = disc.buffer(-NOTCH_EDGE_R).buffer(NOTCH_EDGE_R).difference(hole)   # round the notch's rim edges
    # value v is laid out upright at the window, then turned back (v-1) steps against the wheel's
    # count-up direction: turning the wheel (v-1) steps the count-up way brings it into the window.
    spin = SPIN[name]
    groups = [affinity.rotate(digit_text(v, win_centre(name)), -spin * STEP * (v - 1), origin=tuple(C))
              for v in VALUES]
    for g in groups:
        assert channel.contains(g), "digits must sit inside the channel"
    for i, g in enumerate(groups):       # every value, one step either side of the window, stays hidden
        for s in (-STEP, STEP):
            nb = affinity.rotate(g, spin * STEP * i + s, origin=tuple(C))
            assert not nb.intersects(win.buffer(0.3)), "a neighbouring value would show in the window"
    return dict(name=name, C=C, spin=spin, R=R, r_in=r_in, r_out=r_out, r_valley=r_valley, disc=disc,
                groups=groups)


def turned(g, wh, v):
    """g (on wheel wh) turned to show value v in the window."""
    return affinity.rotate(g, wh["spin"] * STEP * (v - 1), origin=tuple(wh["C"]))


def notch(C, R, a):
    """A V notch at angle a: apex NOTCH_DEPTH below the rim, flanks NOTCH_FLANK from the tangent."""
    u = np.array([np.cos(a), np.sin(a)])
    t = np.array([-np.sin(a), np.cos(a)])
    apex = C + (R - NOTCH_DEPTH) * u
    h = NOTCH_DEPTH + 3.0
    w = h / np.tan(np.radians(NOTCH_FLANK))
    return Polygon([apex, apex + h * u + w * t, apex + h * u - w * t])


def tongue(card, cavity):
    """The tongue's footprint (vd.edge_tongue, shared with vampire-dial) and its run lengths."""
    return vd.edge_tongue(card, cavity, TONGUE_INSET, TONGUE_W, TONGUE_GAP, TONGUE_MIN_LEN)


def mechanism():
    """The back, both wheels and the tongue-and-groove joint, with every fit check. Shared by both cards.
    v4: two wheels, power bottom-left (rim out of the left edge) and toughness bottom-right (right edge).
    No detent: each wheel's friction in the case holds its value."""
    card = vt.rounded_rect(CARD_W, CARD_H, CORNER_R)
    whs = [wheel_geometry(name) for name, _ in WHEELS]
    R = whs[0]["R"]
    assert all(abs(w["R"] - R) < 1e-6 for w in whs)
    cavities = [disk(w["C"], R + WHEEL_CLR, 512) for w in whs]
    cavity = unary_union(cavities)
    spacer = card.difference(cavity)
    ridge, runs = tongue(card, cavity)
    pins = unary_union([disk(w["C"], PIN_D / 2, 32) for w in whs])
    sockets = unary_union([ridge.buffer(TONGUE_CLR, quad_segs=12)] +
                          [disk(w["C"], PIN_D / 2 + SOCKET_D_CLR, 32) for w in whs])

    mid = cavities[0].distance(cavities[1])
    protrude = [min(w["C"][0] - R, CARD_W - (w["C"][0] + R)) for w in whs]
    assert mid >= MID_WALL - 1e-6, f"only {mid:.2f} mm between the wheel cavities (card {CARD_W}, need {MIN_CARD_W:.1f})"
    assert all(abs(p + PROTRUDE) < 1e-6 for p in protrude), "each rim pokes PROTRUDE past its edge"
    assert spacer.buffer(-0.5).contains(ridge), "tongue must stand on solid spacer"
    assert card.buffer(-1.0).contains(sockets), "the front's groove needs an outer wall of >= 1 mm"
    assert sockets.disjoint(window().buffer(WIN_MAT + WIN_RULE)), "groove under a window box"
    assert FRONT_T - GROOVE_DEPTH >= INLAY + 0.4, "too little front above the groove"
    assert sum(runs) > 0.5 * card.buffer(-TONGUE_INSET).length, "tongue covers too little of the edge"
    assert (PIN_D / 2 + PIN_CLR) < whs[0]["r_in"] - 1.0, "hub hole runs into the digit channel"
    foot = rrect(FOOTER, PLATE_R).buffer(-0.6)
    for name, _ in WHEELS:
        assert foot.contains(window(name).buffer(WIN_MAT + WIN_RULE)), \
            f"the {name} window's ruled box must sit inside the footer plate"

    print(f"card: {CARD_W:.1f} x {CARD_H:.1f} mm (narrowest that fits: {MIN_CARD_W:.1f}), {BACK_T + FRONT_T:.1f} mm "
          f"thick assembled ({CARD_W / 25.4:.3f} x {CARD_H / 25.4:.3f} x {(BACK_T + FRONT_T) / 25.4:.3f} in)")
    for w in whs:
        print(f"{w['name']:9s} wheel: centre ({w['C'][0]:.2f}, {w['C'][1]:.2f}), R {R:.2f} "
              f"(dia {2 * R:.1f}, notch bottoms {w['r_valley']:.2f}), channel {w['r_in']:.2f}-{w['r_out']:.2f}, "
              f"digits at r {DIGIT_R}, window at ({win_centre(w['name'])[0]:.2f}, {win_centre(w['name'])[1]:.2f})")
    print(f"rims protrude {PROTRUDE} mm each side; {mid:.2f} mm of spacer between the cavities; "
          f"hub hole {PIN_D + 2 * PIN_CLR:.1f} on a {PIN_D:.1f} pin")
    print(f"tongue: {TONGUE_W} x {TONGUE_H} mm, {len(runs)} runs " + ", ".join(f"{x:.1f}" for x in runs) +
          f" mm ({sum(runs):.0f} mm); groove {TONGUE_W + 2 * TONGUE_CLR:.1f} x {GROOVE_DEPTH:.1f} mm")
    print(f"plates: title {TITLE_BOX[3] - TITLE_BOX[1]:.1f}, art {ART[2] - ART[0]:.1f} x {ART[3] - ART[1]:.1f}, "
          f"footer {FOOTER[3] - FOOTER[1]:.1f} mm tall; windows {WIN_WH[0]:.1f} x {WIN_WH[1]:.1f}; digits {DIGIT_H} mm")
    return dict(card=card, whs=whs, spacer=spacer, base=card, tongue=ridge, pins=pins, sockets=sockets)


# ---- the card frame (shared with vampire-arcana) -------------------------------

class Canvas:
    """Painter's algorithm over 4 colour regions that always tile the card exactly (it starts all ink)."""

    def __init__(self, card):
        self.card = card
        self.r = {INK: card, BLOOD: Polygon(), GOLD: Polygon(), PAPER: Polygon()}

    def paint(self, colour, g, clip=None):
        g = g.intersection(clip if clip is not None else self.card)
        if g.is_empty:
            return
        for k in self.r:
            if k != colour:
                self.r[k] = self.r[k].difference(g)
        self.r[colour] = self.r[colour].union(g)


def bat(c, span, tilt=0.0, bank=0.0):
    """A bat silhouette, wingspan `span` mm, centred on c: smooth leading edge, 3 round scallops
    bitten out of each wing's trailing edge, a round body and two ears. `bank` turns the wings (not
    the body, head and ears) by that many degrees: a bat banking, its wing line a diagonal."""
    wing = spline([(0.02, 0.06), (0.14, 0.15), (0.30, 0.20), (0.44, 0.19), (0.50, 0.13),
                   (0.47, 0.02), (0.30, -0.05), (0.10, -0.09), (0.02, -0.06)])
    bites = [disk((x, y), r, 24) for x, y, r in ((0.42, -0.045, 0.065), (0.29, -0.10, 0.075), (0.15, -0.135, 0.07))]
    wing = wing.difference(unary_union(bites))
    body = affinity.scale(disk((0, 0), 1, 24), 0.055, 0.12)
    head = disk((0, 0.11), 0.05, 16)
    ear = Polygon([(0.012, 0.13), (0.05, 0.20), (0.055, 0.12)])
    wings = affinity.rotate(unary_union([wing, mirror(wing, 0)]), bank, origin=(0, 0))
    g = unary_union([wings, body, head, ear, mirror(ear, 0)]).buffer(0.008).buffer(-0.008)
    g = affinity.scale(g, span, span, origin=(0, 0))
    return affinity.translate(affinity.rotate(g, tilt, origin=(0, 0)), *c)


def slash_bat_shape(c, length, angle, width=2.4):
    """A bat whose spread wings ARE a "/": drawn level (wings along x, head up), then turned `angle`
    degrees, so the wing line is the slash and the head points up-left, square to it. `length` is tip to
    tip, `width` the wing's depth. Each wing: a straight leading edge hooking up at the tip, and three
    pointed fingers with round scallops between them along the trailing edge."""
    L, w = length / 2, width
    fx = [0.30 * L, 0.56 * L, 0.80 * L]                      # finger tips on the trailing edge
    wing = Polygon([(0.0, 0.45 * w), (0.70 * L, 0.55 * w), (L, 0.95 * w), (fx[2], -0.55 * w),
                    (fx[1], -0.55 * w), (fx[0], -0.50 * w), (0.0, -0.40 * w)])
    bites = []
    for a, b in ((0.0, fx[0]), (fx[0], fx[1]), (fx[1], fx[2])):
        r = (b - a) * 0.60
        bites.append(Point((a + b) / 2, -0.55 * w - r * 0.40).buffer(r, quad_segs=24))
    wing = wing.difference(unary_union(bites))
    body = affinity.scale(Point(0, -0.15 * w).buffer(1, quad_segs=24), 0.42 * w, 0.75 * w)
    head = Point(0, 0.72 * w).buffer(0.36 * w, quad_segs=16)
    ears = unary_union([Polygon([(dx * 0.10 * w, 0.85 * w), (dx * 0.36 * w, 1.40 * w), (dx * 0.38 * w, 0.70 * w)])
                        for dx in (-1, 1)])
    g = unary_union([wing, mirror(wing, 0), body, head, ears]).buffer(0.06).buffer(-0.06)
    return affinity.translate(affinity.rotate(g, angle, origin=(0, 0)), *c)


def slash_bat():
    """The P/T slash between the two windows: a bat whose spread wings form the "/"."""
    a, b = window("power").bounds, window("toughness").bounds
    c = ((a[2] + b[0]) / 2, (a[1] + a[3]) / 2)
    return slash_bat_shape(c, SLASH_BAT_LEN, SLASH_BAT_ANGLE, SLASH_BAT_W)


def frame(cv):
    """Paint the card's frame: black edge and rules (the canvas starts black), white title, art and
    footer plates, the title, the two dial windows' ruled boxes (power bottom-left, toughness
    bottom-right) and the bat-shaped slash between them. Returns the art plate, which the scene is clipped to."""
    title_in, art_in, foot_in = rrect(TITLE_BOX, PLATE_R), rrect(ART, PLATE_R), rrect(FOOTER, PLATE_R)
    for g in (title_in, art_in, foot_in):
        cv.paint(PAPER, g)
    cv.paint(INK, title_text())
    for name, _ in WHEELS:
        win = window(name)
        cv.paint(INK, win.buffer(WIN_MAT + WIN_RULE, join_style="round"))
        cv.paint(PAPER, win.buffer(WIN_MAT, join_style="round"))
    cv.paint(INK, slash_bat(), foot_in)
    return art_in


def finish(cv, card):
    """After the scene: clear the window mats again, then make every region printable and snappable."""
    cv.paint(PAPER, window().buffer(WIN_MAT, join_style="round"))
    regions = {k: g.intersection(card).buffer(0) for k, g in cv.r.items()}
    regions = absorb_islands(fill_slivers(regions))
    return {k: tidy(g) for k, g in regions.items()}


def back_regions(card):
    """The card's back face (both cards share it): black edge, white field, a gold crescent with a bat."""
    cv = Canvas(card)
    cv.paint(PAPER, card.buffer(-EDGE).buffer(-0.3).buffer(0.3))
    c = (CX, 38.0)
    crescent = disk(c, 10.0, 96).difference(disk((c[0] + 4.2, c[1] + 2.0), 8.4, 96)).buffer(0.35).buffer(-0.35)
    cv.paint(INK, crescent.buffer(0.4, join_style="round"))
    cv.paint(GOLD, crescent.buffer(-0.4, join_style="round"))
    cv.paint(INK, bat((c[0] + 3.0, c[1] + 0.8), 9.0, -8.0))
    regions = {k: g.intersection(card).buffer(0) for k, g in cv.r.items()}
    return {k: tidy(g) for k, g in absorb_islands(regions).items()}


def fill_slivers(regions, colour=PAPER, min_area=0.02):
    """White narrower than a bead (e.g. where a stroke meets an outline at a shallow angle) can't
    print; give each such sliver to the neighbour it borders most, as woodcut lines run together."""
    g = regions[colour]
    thin = g.difference(g.buffer(-BEAD / 2).buffer(BEAD / 2))
    moved = 0.0
    for p in vt.polys_of(thin):
        if p.area < min_area:
            continue
        ring = p.buffer(0.05)
        best = max((j for j in regions if j != colour), key=lambda j: ring.intersection(regions[j]).area)
        regions[colour] = regions[colour].difference(p)
        regions[best] = regions[best].union(p)
        moved += p.area
    print(f"slivers: {moved:.2f} mm^2 of {PALETTE[colour][0]} thinner than {BEAD} mm merged into neighbours")
    return regions


def absorb_islands(regions):
    """Safety net: an island under MIN_ISLAND mm^2 (a sliver where shapes meet a frame) takes the colour
    it shares the longest border with."""
    for k in list(regions):
        for p in vt.polys_of(regions[k]):
            if p.area >= MIN_ISLAND:
                continue
            ring = p.buffer(0.05)
            best = max((j for j in regions if j != k), key=lambda j: ring.intersection(regions[j]).area)
            regions[k] = regions[k].difference(p.buffer(1e-4))
            regions[best] = regions[best].union(p.buffer(1e-4))
    return regions


def snappable(g):
    """vt.extrude snaps to a 1 micron grid; a hole that nearly touches its shell (where a merged sliver
    met a stroke) can make that snap throw. A sub-micron close/open removes the near-contact."""
    from shapely import set_precision
    from shapely.errors import GEOSException
    for eps in (0.0, 2e-4, 6e-4, 1.5e-3):
        h = g.buffer(eps, join_style="mitre").buffer(-eps, join_style="mitre") if eps else g
        try:
            set_precision(h, 0.001)
            return h
        except GEOSException:
            continue
    raise RuntimeError("geometry could not be snapped for extrusion")


def tidy(g):
    """Snap a final colour region onto a shared 0.5 micron grid (then drop the grid, see vt.extrude), so
    later booleans don't trip over the near-coincident edges that many layers of painting leave. Every
    region snaps identically, so they still tile."""
    from shapely import set_precision
    return set_precision(set_precision(snappable(g.buffer(0)), 0.0005), 0)


def printability(regions):
    """Per colour: the area thinner than a bead and the islands under MIN_ISLAND mm^2."""
    rep = {}
    for k, g in regions.items():
        thin = g.difference(g.buffer(-BEAD / 2).buffer(BEAD / 2)).area
        small = [p.area for p in vt.polys_of(g) if p.area < MIN_ISLAND]
        rep[PALETTE[k][0]] = (thin, len(vt.polys_of(g)), small)
    return rep


def report(card, regions, back):
    for name, reg in (("front", regions), ("back", back)):
        tiling = sum(g.area for g in reg.values())
        print(f"{name} colours (tiling {tiling:.2f} of {card.area:.2f} mm^2): " + ", ".join(
            f"{PALETTE[k][0]} {100 * reg[k].area / card.area:.1f}%" for k in range(4)))
        for cname, (thin, n, small) in printability(reg).items():
            print(f"  {cname:5s}: {n:4d} islands, {thin:.2f} mm^2 thinner than {BEAD} mm"
                  + (f", small islands {[round(a, 2) for a in small]}" if small else ""))


def assembly_check(front, back_parts, wheels):
    """Assemble the parts AS PRINTED (not the design shapes): flip the face-down front and wheels over,
    drop each wheel on its pin on the back, and check the fits (tongue in groove, pins in their sockets,
    hubs on the pins) and that every value of each wheel sits centred in its own window. This catches a
    print transform that is wrong (the v2 back was mirrored, which the design-frame asserts could not see)."""
    card = vt.rounded_rect(CARD_W, CARD_H, CORNER_R)
    wins = card.difference(mirror(front[4][2], CX))             # front flipped over about the card's axis
    grooves = card.difference(wins).difference(mirror(front[5][2], CX))
    pins, ridge = back_parts[6][2], back_parts[7][2]            # the back as printed, cavity up
    assert grooves.buffer(-(TONGUE_CLR - 0.02)).contains(ridge), f"the tongue doesn't clear its groove by {TONGUE_CLR}"
    assert not grooves.buffer(-(TONGUE_CLR + 0.02)).contains(ridge), f"the groove is looser than {TONGUE_CLR}"
    assert grooves.buffer(-(SOCKET_D_CLR - 0.02)).contains(pins), "a pin doesn't clear its socket"
    worst, hubs = 0.0, []
    for (name, spin), (wx, ink, disc) in zip(WHEELS, wheels):
        ink, disc = mirror(ink, wx), mirror(disc, wx)          # wheel flipped over, face toward the window
        hole = Polygon(disc.interiors[0])
        hc = np.array(hole.centroid.coords[0])
        pin = min(pins.geoms, key=lambda p: np.hypot(*(np.array(p.centroid.coords[0]) - WHEEL_C[name])))
        pc = np.array(pin.centroid.coords[0])
        assert np.allclose(pc, WHEEL_C[name], atol=0.01), f"printed {name} pin at {pc}, design {WHEEL_C[name]}"
        ink, disc, hole = (affinity.translate(g, *(pc - hc)) for g in (ink, disc, hole))
        hubs.append(hole.exterior.distance(pin.centroid) - PIN_D / 2)
        assert abs(hubs[-1] - PIN_CLR) < 0.02, f"{name} hub clearance {hubs[-1]:.2f} mm"
        win = window(name)
        wc = np.array(win.centroid.coords[0])
        assert wins.buffer(-0.01).contains(win.buffer(-0.02)), f"no window cut over the {name} wheel"
        for v in VALUES:
            shown = affinity.rotate(ink, spin * STEP * (v - 1), origin=tuple(pc)).intersection(win)
            want = digit_text(v, win_centre(name))
            assert abs(shown.area - want.area) < 0.01 * want.area, f"{name} {v}: window shows the wrong ink"
            b = np.array(shown.bounds)
            err = np.hypot((b[0] + b[2]) / 2 - wc[0], (b[1] + b[3]) / 2 - wc[1])   # ink box centre vs window
            worst = max(worst, err)
            assert err < 0.1, f"{name} {v} is {err:.2f} mm off the window centre"
    print(f"assembly check (parts as printed): pins on the wheel centres with {min(hubs):.2f} mm hub clearance, "
          f"tongue and pins {TONGUE_CLR} mm inside their grooves; both wheels show all {len(VALUES)} values "
          f"centred in their windows (worst {worst:.3f} mm), counting up with the rim pushed up")


def slicer_args():
    """The preset and --set arguments for tools/slice_bambu.py (preset names quoted)."""
    pre = " ".join(f'{a} "{b}"' for a, b in zip(SLICER_PRESETS[::2], SLICER_PRESETS[1::2]))
    return pre + " " + " ".join("--set " + x for x in SLICER_SET)


def write_plate(m, regions, back, parts_dir):
    """Write the face-down plate (front, back, two wheels) as colour-part STLs + slice args.
    Front and wheels lie face-down, so their 2D shapes are mirrored. The back lies on its back face with
    the cavity up, so seen from above it is already in the front-view frame: its mechanism is NOT
    mirrored (v2 mirrored it, so the wheel sat on the wrong side). Only its art is mirrored, as it is
    drawn as seen from behind."""
    parts_dir.mkdir(parents=True, exist_ok=True)
    for f in parts_dir.glob("*.stl"):
        f.unlink()
    card, win = m["card"], window()
    mx = CX
    front = [(0.0, INLAY, mirror(regions[k].difference(win), mx), k) for k in range(4)] + [
        (INLAY, FRONT_T - GROOVE_DEPTH, mirror(card.difference(win), mx), PAPER),
        (FRONT_T - GROOVE_DEPTH, FRONT_T, mirror(card.difference(win).difference(m["sockets"]), mx), PAPER)]
    back_parts = [(0.0, INLAY, mirror(back[k], mx).intersection(m["base"]), k) for k in range(4)] + [
        (INLAY, BASE_T, m["base"], PAPER),
        (BASE_T, BACK_T, m["spacer"], PAPER),
        (BASE_T, BACK_T + TONGUE_H, m["pins"], PAPER),
        (BACK_T, BACK_T + TONGUE_H, m["tongue"], PAPER)]
    wheels, checks = [], []
    R = m["whs"][0]["R"]
    for i, wh in enumerate(m["whs"]):
        wx = wh["C"][0]
        digits = unary_union(wh["groups"])
        parts = [(0.0, INLAY, mirror(digits, wx), INK),
                 (0.0, INLAY, mirror(wh["disc"].difference(digits), wx), PAPER),
                 (INLAY, WHEEL_T, mirror(wh["disc"], wx), PAPER)]
        checks.append((wx, parts[0][2], parts[2][2]))
        off = (2 * (CARD_W + PLATE_GAP) + R - wx, R - wh["C"][1] + 2 + i * (2 * R + PLATE_GAP))
        wheels.append((wh["name"], off, parts))
    assembly_check(front, back_parts, checks)
    objects = [("front", (0.0, 0.0), front), ("back", (CARD_W + PLATE_GAP, 0.0), back_parts)] + wheels
    files, slots = [], []
    grams = [0.0] * 4
    for name, off, parts in objects:
        for i, (z0, z1, g, slot) in enumerate(parts):
            if g.is_empty:
                continue
            mesh = vt.extrude(snappable(g), z0, z1)
            if mesh is None:
                continue
            mesh.apply_translation([off[0], off[1], 0])
            fn = parts_dir / f"{name}_{i}_{PALETTE[slot][0]}.stl"
            mesh.export(fn)
            files.append(fn.name)
            slots.append(slot + 1)
            grams[slot] += g.area * (z1 - z0) / 1000 * 1.24
            print(f"  {fn.name:24s} z {z0:.1f}-{z1:.1f}  {g.area * (z1 - z0) / 1000:.2f} cm^3")
    (parts_dir / "slice_args.txt").write_text(
        " ".join(files) + f" --assemble --extruders {','.join(map(str, slots))} "
        f"--colors \"{','.join(h for _, h in PALETTE)}\" " + slicer_args() + "\n")
    print("model grams per slot (PLA 1.24 g/cm^3, solid, before purge): " +
          ", ".join(f"{i + 1} {PALETTE[i][0]} {g:.2f}" for i, g in enumerate(grams)))


# ---- this card's scene: flat colour --------------------------------------------

def streak(x0, x1, y, w, bend=0.4, wend=0.8):
    """A cloud streak: thick in the middle, tapering to a bead at both ends."""
    xs = np.linspace(x0, x1, 40)
    ys = y + bend * np.sin(np.linspace(0, np.pi, 40))
    ws = wend + (w - wend) * np.sin(np.linspace(0, np.pi, 40)) ** 0.7
    circles = [Point(a, b).buffer(c / 2, quad_segs=12) for a, b, c in zip(xs, ys, ws)]
    return unary_union([p.union(q).convex_hull for p, q in zip(circles, circles[1:])])


def tower(x0, x1, top, spire, base=18.0):
    body = box(x0, base, x1, top)
    roof = Polygon([(x0 - 0.5, top), (x1 + 0.5, top), ((x0 + x1) / 2, top + spire)])
    return body.union(roof).buffer(-0.3).buffer(0.3)


def lancet(cx, y0, w, h):
    """Pointed (gothic) window."""
    return box(cx - w / 2, y0, cx + w / 2, y0 + h - w / 2).union(
        Polygon([(cx - w / 2, y0 + h - w / 2 - 0.01), (cx + w / 2, y0 + h - w / 2 - 0.01), (cx, y0 + h)]))


# The vampire knight, drawn in a local frame: face centre at HEAD, 1 unit = 1 mm. An original
# elder vampire lord in plate armour (the archetype, not any card's art): long white hair, stern
# gaunt face with a moustache and pointed beard, layered pauldrons, gorget, red cloak, and a sword
# planted point-down before him. Black linework separates touching white shapes.

def at(g):
    return affinity.translate(g, *HEAD)


def outlined(cv, colour, g, clip, w=LINE, edge=INK):
    cv.paint(edge, at(g.buffer(w, join_style="round")), clip)
    cv.paint(colour, at(g), clip)


def knight(cv, clip):
    S = lambda g: sym(g, 0)
    # red cloak behind everything, flaring past the art plate's bottom corners, with black folds
    cloak = spline(sym_pts([(0, -7.0), (-10.0, -8.6), (-18.5, -12.2), (-24.5, -18.5), (-28.0, -26.0),
                            (-31.5, -36.0), (0, -36.0)]), n=400)
    cv.paint(BLOOD, at(cloak_widen(cloak)), clip)          # v4: widened with the art plate
    for f in ([(-22.0, -17.6), (-24.2, -23.5), (-25.8, -33.5)], [(-19.5, -20.0), (-20.6, -26.0), (-21.2, -33.5)]):
        cv.paint(INK, at(S(cloak_widen(taper(f, 0.9, 1.4)))), clip)
    # breastplate, with a gold plate seam (the fauld) either side of the sword. The art plate ends at
    # local y -31, so there is room for one seam: low enough to clear the quillon tips by over a bead.
    chest = spline(sym_pts([(0, -11.5), (-7.8, -12.2), (-10.4, -17.0), (-11.6, -25.0), (-12.0, -36.0), (0, -36.0)]))
    outlined(cv, INK, chest, clip, edge=GOLD)
    y = -30.0
    cv.paint(GOLD, at(S(taper([(-10.8, y + 0.5), (-6.0, y - 0.2), (-1.5, y - 0.4)], 0.8, 0.8))), clip)
    # pauldrons: three overlapping curved lames each side, gold edges
    cap = spline([(-5.0, -10.8), (-10.0, -9.6), (-16.0, -10.6), (-21.4, -13.8), (-24.6, -18.8),
                  (-23.0, -20.8), (-17.0, -18.4), (-11.0, -16.9), (-5.0, -16.6)])
    for dx, dy in ((-2.2, -5.4), (-1.1, -2.7), (0.0, 0.0)):    # lowest lame first; each peeks out below the next
        outlined(cv, INK, S(affinity.translate(cap, dx, dy)), clip, w=0.8, edge=GOLD)
    # long white hair falling to the shoulders, outlined, with swept-back black strands
    hair = spline(sym_pts([(0, 10.9), (-4.7, 10.2), (-7.9, 7.4), (-9.3, 2.4), (-9.8, -3.2), (-10.8, -8.4),
                           (-12.4, -12.6), (-7.6, -12.2), (-4.0, -9.8), (0, -9.4)]), n=400)
    outlined(cv, PAPER, hair, clip, w=0.8)
    for st in ([(-3.4, 9.6), (-6.0, 8.0), (-7.4, 5.0)], [(-6.9, 4.4), (-8.0, -1.0), (-9.2, -6.5), (-10.6, -10.6)],
               [(-6.2, -3.6), (-7.4, -7.6), (-8.6, -11.0)]):
        cv.paint(INK, at(S(taper(st, 0.75, 0.65))), clip)
    # gorget (neck armour) with two gold lames
    gorget = spline(sym_pts([(0, -9.4), (-4.4, -9.2), (-6.6, -10.8), (-7.2, -14.6), (0, -15.2)]))
    outlined(cv, INK, gorget, clip, w=0.8, edge=GOLD)
    cv.paint(GOLD, at(S(taper([(-6.0, -12.0), (-3.0, -12.6), (0, -12.8)], 0.8, 0.8))), clip)
    # the face: gaunt, stern; black outline makes the hairline and jaw
    face = spline(sym_pts([(0, 8.3), (-2.6, 8.4), (-4.6, 6.8), (-5.6, 3.4), (-5.7, 0.0), (-5.3, -3.6),
                           (-4.3, -6.4), (-2.6, -8.4), (0, -9.0)]))
    outlined(cv, PAPER, face, clip)
    cv.paint(GOLD, at(S(taper([(-5.0, -1.4), (-4.6, -3.0), (-3.8, -4.4)], 1.2, 0.9))), clip)   # hollow cheeks
    cv.paint(INK, at(S(taper([(-5.0, 3.1), (-3.1, 2.9), (-1.0, 2.2)], 1.3, 1.0))), clip)      # heavy brows
    cv.paint(INK, at(taper([(0, 2.4), (0, 4.0)], 0.6, 0.6)), clip)                            # frown line
    eye = affinity.translate(affinity.rotate(affinity.scale(disk((0, 0), 1, 32), 1.4, 0.55), -6), -2.6, 1.05)
    cv.paint(BLOOD, at(S(eye)), clip)
    cv.paint(INK, at(taper([(0.6, 1.4), (0.9, -1.4), (1.35, -3.4)], 0.7, 0.8)), clip)            # nose
    cv.paint(INK, at(taper([(-1.3, -3.9), (0, -4.3), (1.35, -3.6)], 0.7, 0.7)), clip)
    # moustache and pointed beard (white, outlined), the mouth a black line between them
    beard = Polygon(sym_pts([(0, -7.4), (-2.7, -7.1), (-2.5, -9.4), (-1.2, -11.2), (0, -12.6)])).buffer(0.3).buffer(-0.3)
    outlined(cv, PAPER, beard, clip, w=0.6)
    cv.paint(INK, at(taper([(-1.9, -6.7), (0, -7.0), (1.9, -6.7)], 0.7, 0.7)), clip)
    stache = Polygon(sym_pts([(0, -4.9), (-1.7, -5.0), (-3.3, -5.9), (-4.3, -8.0), (-2.7, -6.9),
                              (-1.2, -6.3), (0, -6.3)])).buffer(0.2).buffer(-0.2)
    outlined(cv, PAPER, stache, clip, w=0.6)
    cv.paint(GOLD, at(taper([(0, -8.4), (0, -11.0)], 0.7, 0.7)), clip)                         # beard strand
    # the sword, planted point-down: blade, curved crossguard, wrapped grip, red pommel gem
    blade = Polygon([(-1.8, -40), (1.8, -40), (1.8, -26.0), (-1.8, -26.0)])
    outlined(cv, PAPER, blade, clip, w=0.7)
    cv.paint(GOLD, at(box(-0.45, -40, 0.45, -26.4)), clip)
    guard = unary_union([box(-6.5, -26.4, 6.5, -24.6), S(taper([(-6.0, -25.5), (-8.2, -25.9), (-9.0, -27.6)], 1.8, 1.0))])
    outlined(cv, INK, guard, clip, w=0.7, edge=GOLD)
    grip = box(-1.4, -24.6, 1.4, -18.8)                      # leather-wrapped grip with black bands
    outlined(cv, GOLD, grip, clip, w=0.7)
    for y in (-21.0, -22.9):
        cv.paint(INK, at(box(-1.4, y - 0.35, 1.4, y + 0.35)), clip)
    cv.paint(GOLD, at(disk((0, -17.2), 2.1, 32)), clip)
    cv.paint(BLOOD, at(disk((0, -17.2), 1.3, 32)), clip)


def front_regions(card):
    """The shared frame, with the colour-fill scene in its art plate, painted back to front."""
    cv = Canvas(card)
    clip = frame(cv)
    x0, _, x1, _ = ART
    # v4 (wider card): left-side elements stay anchored to the left edge, right-side ones to the right
    # edge (xr), and the ones grouped round the moon follow the centre (xc)
    for c in (streak(x0 - 1, 23.0, 67.8, 2.2), streak(x0 - 1, 13.0, 64.0, 1.5, -0.3),
              streak(xr(41.0), x1 + 1, 69.4, 2.0, -0.4), streak(xr(43.0), x1 + 1, 49.2, 2.2),
              streak(xr(47.0), x1 + 1, 45.6, 1.4, -0.3), streak(x0 - 1, 18.0, 51.8, 2.0, -0.3),
              streak(x0 - 1, 12.5, 48.4, 1.3)):
        cv.paint(GOLD, c, clip)
    cv.paint(BLOOD, disk(MOON_C, MOON_R, 128), clip)
    cv.paint(GOLD, streak(xc(38.5), xc(55.0), 61.6, 1.7, 0.3), clip)    # one streak across the moon
    castle = unary_union([
        tower(x0 - 1, 8.2, 39.7, 10.0), tower(8.2, 11.6, 34.7, 7.0), tower(11.6, 15.0, 30.7, 5.0),
        tower(xr(54.6), x1 + 1, 42.2, 11.0), tower(xr(51.0), xr(54.6), 36.2, 7.5), tower(xr(47.6), xr(51.0), 31.2, 5.0),
        box(x0 - 1, 18.0, 16.0, 28.2), box(xr(47.0), 18.0, x1 + 1, 28.7)])
    cv.paint(INK, castle, clip)
    for w in (lancet(5.0, 35.2, 1.4, 3.2), lancet(xr(57.6), 37.7, 1.4, 3.4), lancet(xr(52.8), 32.8, 1.3, 2.6)):
        cv.paint(BLOOD, w, clip)
    for c, span, tilt in (((xc(19.5), 64.2), 12.5, 8.0), ((xc(44.5), 66.2), 8.5, -6.0),
                          ((xc(53.0), 58.7), 6.5, 10.0), ((xc(41.0), 58.7), 5.5, -12.0)):
        cv.paint(INK, bat(c, span, tilt), clip)
    knight(cv, clip)
    return finish(cv, card)


# ---- previews -----------------------------------------------------------------

def nozzle_sim(g):
    """Roughly what a 0.4 nozzle keeps: open with a bead, close a little."""
    return g.buffer(-0.21).buffer(0.21).buffer(0.15).buffer(-0.15)


def draw_face(ax, regions, whs, pt, sim=False):
    """The card's face with the power and toughness wheels turned to pt = (p, t)."""
    hexes = [h for _, h in PALETTE]
    win = window()
    for wh, v in zip(whs, pt):
        vd.draw(ax, turned(wh["disc"], wh, v), hexes[PAPER])
        vd.draw(ax, turned(unary_union(wh["groups"]), wh, v), hexes[INK])
    vd.draw(ax, regions[PAPER].difference(win), hexes[PAPER])
    for k in (INK, BLOOD, GOLD):
        g = regions[k].difference(win)
        vd.draw(ax, nozzle_sim(g) if sim else g, hexes[k])
    ax.set_aspect("equal"); ax.set_facecolor("#9aa0a6"); ax.set_xticks([]); ax.set_yticks([])


def preview(regions, back, whs, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_, axes = plt.subplots(1, 5, figsize=(24, 6.6))
    xl = (-PROTRUDE - 1, CARD_W + PROTRUDE + 1)
    for ax, (pt, sim, t) in zip(axes, [((1, 1), False, "1/1"), ((3, 5), False, "3/5"), ((9, 9), False, "9/9"),
                                       ((2, 2), True, "nozzle simulation (ink, red, gold opened 0.42 mm)")]):
        draw_face(ax, regions, whs, pt, sim)
        ax.set_xlim(*xl); ax.set_ylim(-1, CARD_H + 1); ax.set_title(t, fontsize=9)
    ax = axes[4]
    hexes = [h for _, h in PALETTE]
    for k in range(4):
        vd.draw(ax, back[k], hexes[k])
    ax.set_aspect("equal"); ax.set_facecolor("#9aa0a6"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlim(*xl); ax.set_ylim(-1, CARD_H + 1); ax.set_title("back (as seen from behind)", fontsize=9)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig_)
    print(f"preview -> {path}")


def joint_section(ax, x_edge=0.0):
    """Cross-section through the card edge: back (base + spacer + tongue) under the front (groove)."""
    t0, t1 = TONGUE_INSET - TONGUE_W / 2, TONGUE_INSET + TONGUE_W / 2
    g0, g1 = t0 - TONGUE_CLR, t1 + TONGUE_CLR
    w = 6.0
    back = unary_union([box(0, 0, w, BACK_T), box(t0, BACK_T, t1, BACK_T + TONGUE_H)])
    front = box(0, BACK_T, w, BACK_T + FRONT_T).difference(box(g0, BACK_T, g1, BACK_T + GROOVE_DEPTH))
    vd.draw(ax, back, "#7a6a58")
    vd.draw(ax, front, "#e8d2a8")
    vd.draw(ax, box(0, BACK_T + FRONT_T - INLAY, w, BACK_T + FRONT_T), PALETTE[INK][1])
    ax.set_xlim(-0.5, w); ax.set_ylim(-0.5, BACK_T + FRONT_T + 0.5)
    ax.set_title(f"joint section at the edge: tongue {TONGUE_W} x {TONGUE_H}, groove "
                 f"{TONGUE_W + 2 * TONGUE_CLR:.1f} x {GROOVE_DEPTH:.1f} mm", fontsize=9)


def parts_preview(m, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    card, whs = m["card"], m["whs"]
    fig_, axes = plt.subplots(1, 4, figsize=(24, 7), gridspec_kw=dict(width_ratios=[1, 1, 0.7, 1.4]))
    xl = (-PROTRUDE - 1, CARD_W + PROTRUDE + 1)
    ax = axes[0]
    vd.draw(ax, m["spacer"], "#7a6a58")
    vd.draw(ax, card.difference(m["spacer"]), "#e8d2a8")
    vd.draw(ax, m["tongue"], "#b03a2e")
    vd.draw(ax, m["pins"], "#3a2d25")
    for wh in whs:
        ax.plot(*np.asarray(wh["disc"].exterior.coords).T, color="#1f5fa8", lw=0.8)
    ax.set_title("back: base (beige), spacer (brown), tongue (red), pins; wheel outlines blue", fontsize=9)
    ax = axes[1]
    vd.draw(ax, card.difference(window()), "#e8d2a8")
    vd.draw(ax, m["sockets"], "#7a6a58")
    ax.set_title("front underside, in the front-view frame: groove + pin sockets", fontsize=9)
    for ax in axes[:2]:
        ax.set_xlim(*xl); ax.set_ylim(-2, CARD_H + 2)
    joint_section(axes[2])
    ax = axes[3]
    R = whs[0]["R"]
    for i, wh in enumerate(whs):
        dx = (2 * R + 3) * i - wh["C"][0]
        sh = lambda g: affinity.translate(g, dx, -wh["C"][1])
        vd.draw(ax, sh(wh["disc"]), PALETTE[PAPER][1])
        vd.draw(ax, sh(unary_union(wh["groups"])), PALETTE[INK][1])
    ax.set_xlim(-R - 1, 3 * R + 4); ax.set_ylim(-R - 1, R + 1)
    ax.set_title(f"power and toughness wheels (faces, digits inlaid; the power wheel counts the other way "
                 f"round); hub {PIN_D + 2 * PIN_CLR:.1f} mm on a {PIN_D:.0f} mm pin", fontsize=9)
    for ax in axes:
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close(fig_)
    print(f"preview -> {path}")


# ---- build --------------------------------------------------------------------

def main():
    m = mechanism()
    card = m["card"]
    regions = front_regions(card)
    back = back_regions(card) if BACK_ART else {PAPER: card, INK: Polygon(), BLOOD: Polygon(), GOLD: Polygon()}
    report(card, regions, back)
    write_plate(m, regions, back, PARTS)
    preview(regions, back, m["whs"], OUT / "counter_preview.png")
    parts_preview(m, OUT / "parts_preview.png")


if __name__ == "__main__":
    main()
