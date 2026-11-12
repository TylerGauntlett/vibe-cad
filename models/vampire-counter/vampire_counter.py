#!/usr/bin/env python3
"""
Vampire counter token: a reimagined vampire token built for a 0.4 mm nozzle rather than copied from
card art. It is a 63 x 88 card with a bold vector scene (caped vampire before a blood moon, bats,
castle spires), one big "VAMPIRE" title, and an internal thumbwheel that shows 1/1 ... 9/9 in 8 mm
digits through a window at the bottom.

Spec: see README.md in this folder.

Why it's built like this (lessons from models/vampire-dial, whose print was hard to read):
  * The art is drawn as vector shapes with nothing narrower than ~0.8 mm, not traced from a raster.
  * There's one word of text, set large (Cambria Bold, ~7 mm caps). The type line is gone.
  * 8 mm digits need a digit ring of radius ~21 mm to hide the neighbouring values, so the wheel is
    ~59 mm across: it fills the lower card under the art, and its rim pokes out of the right edge.

Parts (printed side by side on one plate, in their assembled orientation):
  back   base plate + spacer frame with the wheel cavity, an axle pin, 6 alignment pegs and a
         cantilever detent spring that clicks into the wheel's 9 scallops
  wheel  scalloped disc; raised black-topped "N/N" digits in a recessed cream channel
  front  the relief art with the window through it and sockets underneath for the pin and pegs

Colour bands (shared by every part, so each layer is ONE filament, as in models/vampire-token
"relief"): cream 0-1.0, tan 1.0-1.2, red 1.2-1.6, black 1.6+. 3 swaps in total, all light -> dark.

Run (from the repo root):
    .venv\\Scripts\\python.exe models\\vampire-counter\\vampire_counter.py
Outputs (millimetres) go to models\\vampire-counter\\out\\
    parts/<object>_<n>_<colour>.stl   parts; load as ONE object (slice_bambu.py --assemble)
    parts/slice_args.txt              the matching slice_bambu.py arguments
    counter_preview.png               assembled top view at 1/1, 5/5, 9/9 + the window close-up
    parts_preview.png                 back (spacer, detent, pin, pegs) and wheel
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


# Shared helpers: extrusion and palette (vampire-token), text layout and colour slabs (vampire-dial).
vt = _load("vampire_token", HERE.parent / "vampire-token" / "vampire_token.py")
vd = _load("vampire_dial", HERE.parent / "vampire-dial" / "vampire_dial.py")
BLACK, RED, TAN, CREAM = vt.BLACK, vt.RED, vt.TAN, vt.CREAM

# ---- Parameters (mm) -------------------------------------------------------
CARD_W, CARD_H, CORNER_R = 63.0, 88.0, 3.0
CX = CARD_W / 2

# Frames: interiors as (x0, y0, x1, y1), card mm from the bottom-left. Each gets a tan rim.
TITLE_BOX = (4.0, 74.7, 59.0, 84.8)      # black bar holding the title
ART_BOX = (4.0, 18.2, 59.0, 71.4)        # the scene
FRAME_R = 1.6                            # interior corner radius
RIM = 0.8                                # tan rim width (two beads)
MAT = 1.0                                # cream mat between the window and its rim

# Title: cream letters (1 mm-deep slots) in the black bar.
TITLE = "VAMPIRE"
TITLE_FONT = r"C:\Windows\Fonts\cambriab.ttf"   # Cambria Bold (fallback DejaVu Serif Bold)
TITLE_CAP_MAX = 7.2
TITLE_W_MAX = 47.0
TITLE_TRACK = 0.9
TITLE_BOLDEN = 0.10

# Digits: Bahnschrift Bold Condensed; the slash is scaled to the digit height (its natural
# descender/overshoot would make the window taller, and the window height sets the wheel size).
DIGIT_FONT = (r"C:\Windows\Fonts\bahnschrift.ttf", {"wght": 700, "wdth": 75})
DIGIT_H = 8.0                   # digit cap height (the vampire-dial digits were 3.0 mm for all of "N/N")
DIGIT_GAP = 0.7                 # between the digits and the slash
DIGIT_BOLDEN = 0.05
VALUES = range(1, 10)
STEP = 360 / len(VALUES)        # 40 degrees per value
WIN_PAD = (0.8, 0.6)            # window margin around the largest "N/N" (x, y)
WIN_R = 1.5

# Wheel. Centre C; the window sits DIGIT_R from it in direction WIN_ANGLE. Turning the wheel
# counter-clockwise (pushing the rim UP at the card's right edge) counts up.
WIN_ANGLE = -100.0              # a little left of straight down, so the window is near the card's centre
DIGIT_R = 21.0                  # smallest ring radius that hides both neighbours (searched)
PROTRUDE = 2.5                  # rim past the card's right edge
BOTTOM_WALL = 1.0               # spacer between the cavity and the card's bottom edge
CHANNEL_MARGIN = 0.4
WHEEL_RIM = 0.8                 # raised rim between the channel and the notch bottoms
# 9 V notches = the detent seats and the thumb grip. v1 had round scallops (R 6) under a small nub
# (R 1.2): near the bottom the nub rose only s^2/(2*4.8), so the wheel wiggled about a value with
# almost no restoring force. Straight flanks lift the nub linearly (0.7 mm per mm of turn at 35 deg).
NOTCH_DEPTH = 1.3
NOTCH_FLANK = 35.0              # flank angle from the rim's tangent (steeper = firmer centring, harder click)
NOTCH_EDGE_R = 0.6              # rounding of the notch's rim edges
WHEEL_FLOOR = 1.0               # channel floor (top of the cream band)
WHEEL_T = 1.8                   # raised rim/hub/digits: tan 1.0-1.2, red 1.2-1.6, black cap 1.6-1.8
PIN_D, PIN_CLR = 6.0, 0.25      # axle pin; radial clearance in the wheel's hole
WHEEL_CLR = 0.4                 # radial clearance wheel -> cavity wall
AX_CLR = 0.4                    # axial play

# Back
BASE_T = 0.6
CAVITY = WHEEL_T + AX_CLR       # 2.2
BACK_T = BASE_T + CAVITY        # 2.8
PEG_D, PEG_H = 2.0, 0.4
SOCKET_D_CLR = 0.15             # per side
SOCKET_DEPTH = 0.6
PEGS = [(4.5, 83.5), (58.5, 83.5), (4.5, 64.0), (58.5, 64.0), (3.5, 4.0), (59.5, 4.0)]

# Detent: a tapered cantilever in the spacer above the wheel, running left; its round nub seats on
# both flanks of a notch. v1 (15 x 1.0 mm, square root) bent to 1.07 % strain over the rim from a
# sharp corner and held the wheel with 0.13 N. This one: ~0.67 % at the rim, 0.40 N seated, filleted root.
DETENT_ANGLE = 90.0             # top of the wheel
ARM_SIDE = -1                   # the arm runs counter-clockwise (to the left) from the nub
ARM_L = 26.0                    # free length
ARM_T_TIP, ARM_T_ROOT = 1.4, 2.2    # tapered: strain is spread along the arm instead of peaking at the root
ROOT_FILLET = 3.0               # concave fillet where the arm meets the spacer
ARM_TOP_CLR = 0.2
NUB_R = 1.0
PRELOAD = 0.4                   # interference when seated: holds the wheel firmly on a value
ARM_GAP = 0.4
STOP_GAP = 0.2                  # the pocket wall stops the arm this far (+ ARM_GAP) past the deflection it needs
E_PLA = 3500.0                  # MPa, for the strain/force report
MAX_STRAIN = 0.008              # PLA yields around 2-3 %; keep repeated flexing well below

# Front
BANDS = [(0.0, 1.0, CREAM), (1.0, 1.2, TAN), (1.2, 1.6, RED), (1.6, 99.0, BLACK)]
FRONT_T = 2.0

# Printability limits for the art (checked, not just hoped for)
BEAD = 0.45                     # narrower than this prints as a broken single bead
MIN_ISLAND = 1.0                # mm^2

PLATE_GAP = 8.0
SLICER_SET = ["wall_generator=arachne", "wall_transition_angle=30", "wall_transition_filter_deviation=50%",
              "min_bead_width=50%", "wall_transition_length=50%"]
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
        print(f"  warning: {src} not found, digits fall back to DejaVu Sans Bold")
        return FontProperties(family="DejaVu Sans", weight="bold")
    dst = Path(tempfile.gettempdir()) / f"vampire_counter_{Path(src).stem}_{axes['wght']}_{axes['wdth']}.ttf"
    if not dst.exists():
        instantiateVariableFont(TTFont(src), axes).save(dst)
    return FontProperties(fname=str(dst))


DFONT = digit_font()


def nn_text(v, centre):
    """'v/v' with the slash scaled to the digit height, bbox centred on centre."""
    k = (DIGIT_H - 2 * DIGIT_BOLDEN) / vd.glyphs("8", DFONT).bounds[3]
    d = affinity.scale(vd.glyphs(str(v), DFONT), k, k, origin=(0, 0))
    s = vd.glyphs("/", DFONT)
    ks = (DIGIT_H - 2 * DIGIT_BOLDEN) / (s.bounds[3] - s.bounds[1])
    s = affinity.scale(s, ks, ks, origin=(0, 0))
    s = affinity.translate(s, 0, -s.bounds[1])
    parts, x = [], 0.0
    for g in (d, s, d):
        b = g.bounds
        parts.append(affinity.translate(g, x - b[0], 0))
        x += b[2] - b[0] + DIGIT_GAP
    g = unary_union(parts).buffer(DIGIT_BOLDEN, join_style="round")
    b = g.bounds
    return affinity.translate(g, centre[0] - (b[0] + b[2]) / 2, centre[1] - (b[1] + b[3]) / 2)


def title_text():
    if Path(TITLE_FONT).exists():
        fp = FontProperties(fname=TITLE_FONT)
    else:
        print(f"  warning: {TITLE_FONT} not found, title falls back to DejaVu Serif Bold")
        fp = FontProperties(family="DejaVu Serif", weight="bold")
    cap = vd.glyphs("V", fp).bounds[3]
    k = (TITLE_CAP_MAX - 2 * TITLE_BOLDEN) / cap
    for _ in range(4):
        g = vd.lay_out([(TITLE, 1.0)], fp, k, TITLE_TRACK, TITLE_BOLDEN)
        w = g.bounds[2] - g.bounds[0]
        if w <= TITLE_W_MAX + 1e-6:
            break
        k *= TITLE_W_MAX / w
    b = g.bounds
    x0, y0, x1, y1 = TITLE_BOX
    print(f"title: {fp.get_name()}, caps {k * cap + 2 * TITLE_BOLDEN:.1f} mm, {b[2] - b[0]:.1f} mm long")
    return affinity.translate(g, (x0 + x1) / 2 - (b[0] + b[2]) / 2, (y0 + y1) / 2 - (b[1] + b[3]) / 2)


# ---- dial geometry (wheel centre at the origin, then placed) -------------------

def dial_layout():
    a = np.radians(WIN_ANGLE)
    P0 = DIGIT_R * np.array([np.cos(a), np.sin(a)])          # window centre relative to C
    texts = [nn_text(v, P0) for v in VALUES]
    W = max(t.bounds[2] - t.bounds[0] for t in texts) + 2 * WIN_PAD[0]
    H = max(t.bounds[3] - t.bounds[1] for t in texts) + 2 * WIN_PAD[1]
    win0 = vd.rounded_box(*P0, W, H, WIN_R)
    pts = np.array(win0.exterior.coords)
    r_out = np.hypot(*pts.T).max() + CHANNEL_MARGIN
    R = r_out + WHEEL_RIM + NOTCH_DEPTH
    C = np.array([CARD_W + PROTRUDE - R, R + WHEEL_CLR + BOTTOM_WALL])
    return C, R, C + P0, (W, H)


C, R_WHEEL, WIN_C, WIN_WH = dial_layout()


def window():
    return vd.rounded_box(*WIN_C, *WIN_WH, WIN_R)


def wheel_geometry():
    win = window()
    pts = np.array(win.exterior.coords)
    r_out = np.hypot(*(pts - C).T).max() + CHANNEL_MARGIN
    r_in = Point(*C).distance(win) - CHANNEL_MARGIN
    r_valley = r_out + WHEEL_RIM
    R = r_valley + NOTCH_DEPTH
    channel = disk(C, r_out, 256).difference(disk(C, r_in, 256))
    notches = unary_union([notch(R, a) for a in np.radians(DETENT_ANGLE + STEP * np.arange(len(VALUES)))])
    hole = disk(C, PIN_D / 2 + PIN_CLR, 32)
    disc = disk(C, R, 512).difference(notches)
    disc = disc.buffer(-NOTCH_EDGE_R).buffer(NOTCH_EDGE_R).difference(hole)   # round the notch's rim edges
    # value v is laid out upright at the window, then turned back (v-1) steps: turning the wheel
    # (v-1) steps counter-clockwise brings it into the window.
    groups = [affinity.rotate(nn_text(v, WIN_C), -STEP * (v - 1), origin=tuple(C)) for v in VALUES]
    for g in groups:
        assert channel.contains(g), "digits must sit inside the channel"
    for i, g in enumerate(groups):       # every value, one step either side of the window, stays hidden
        for s in (-STEP, STEP):
            nb = affinity.rotate(g, STEP * i + s, origin=tuple(C))
            assert not nb.intersects(win.buffer(0.3)), "a neighbouring value would show in the window"
    raised = disc.difference(channel).union(unary_union(groups))
    return dict(R=R, r_in=r_in, r_out=r_out, r_valley=r_valley, disc=disc, raised=raised, groups=groups)


def notch(R, a):
    """A V notch at angle a: apex NOTCH_DEPTH below the rim, flanks NOTCH_FLANK from the tangent."""
    u = np.array([np.cos(a), np.sin(a)])
    t = np.array([-np.sin(a), np.cos(a)])
    apex = C + (R - NOTCH_DEPTH) * u
    h = NOTCH_DEPTH + 3.0
    w = h / np.tan(np.radians(NOTCH_FLANK))
    return Polygon([apex, apex + h * u + w * t, apex + h * u - w * t])


def nub_radius_free(R):
    """Radial position of the nub centre with the arm unbent: touching both flanks, minus the preload."""
    return R - NOTCH_DEPTH + NUB_R / np.cos(np.radians(NOTCH_FLANK)) - PRELOAD


def arm_width(s):
    """Arm width at distance s from the tip: linear taper, then the root fillet flares into the wall."""
    w = ARM_T_TIP + (ARM_T_ROOT - ARM_T_TIP) * min(s, ARM_L) / ARM_L
    if s > ARM_L:
        d = min(s - ARM_L, ROOT_FILLET)
        w += 2 * (ROOT_FILLET - np.sqrt(ROOT_FILLET ** 2 - d ** 2))
    return w


def arm_mechanics(R):
    """Deflections the arm sees, and its peak strain and nub force at each (tapered cantilever, tip load)."""
    x = np.linspace(1e-6, ARM_L, 4000)
    t = ARM_T_TIP + (ARM_T_ROOT - ARM_T_TIP) * x / ARM_L
    h = BACK_T - ARM_TOP_CLR
    compliance = np.trapezoid(x ** 2 / (h * t ** 3 / 12), x) / E_PLA   # mm per N
    seated = PRELOAD
    land = R + NUB_R - nub_radius_free(R)
    stop = land + STOP_GAP + ARM_GAP
    out = {}
    for name, d in (("seated", seated), ("on the rim", land), ("at the stop", stop)):
        P = d / compliance
        out[name] = (d, P, (6 * P * x / (E_PLA * h * t ** 2)).max())
    return out


def detent(R):
    a = np.radians(DETENT_ANGLE)
    u = np.array([np.cos(a), np.sin(a)])                       # radial, outward
    t = ARM_SIDE * np.array([np.sin(a), -np.cos(a)])           # along the arm, tip -> root
    n = u                                                      # arm normal, away from the wheel
    inner0 = C + (R + ARM_GAP) * u                             # the arm's inner edge at its tip clears the rim
    flare_end = ARM_L + np.sqrt(ROOT_FILLET ** 2 - (ROOT_FILLET - (ARM_GAP + 0.3)) ** 2)   # flare meets the wall
    ss = np.r_[np.linspace(0, ARM_L, 40), np.linspace(ARM_L, flare_end, 30)[1:]]
    taper_w = ARM_T_TIP + (ARM_T_ROOT - ARM_T_TIP) * np.minimum(ss, ARM_L) / ARM_L
    flare = np.array([arm_width(x) for x in ss]) - taper_w     # both sides of the root get half
    inner = [inner0 + x * t - f / 2 * n for x, f in zip(ss, flare)]
    outer = [inner0 + x * t + (w + f / 2) * n for x, w, f in zip(ss, taper_w, flare)]
    beam = Polygon(inner + outer[::-1])
    end = inner0 + flare_end * t
    w_end = ARM_T_ROOT + flare[-1]
    anchor = Polygon([end - flare[-1] / 2 * n, end + 2.0 * t - flare[-1] / 2 * n,
                      end + 2.0 * t + (w_end - flare[-1] / 2) * n, end + (w_end - flare[-1] / 2) * n])
    nub = Point(*(C + nub_radius_free(R) * u)).buffer(NUB_R, quad_segs=24)
    # a radial neck joins the nub to the arm's tip; it narrows to 1.4 mm just above the rim so it stays
    # clear of the notch's edges (a hull toward the arm would clip the notch's rim edge)
    base_c = C + (R - 0.1) * u
    top_c = inner0 + ARM_T_TIP * n
    neck = Polygon([base_c - 0.7 * t, base_c + 0.7 * t, top_c + 0.7 * t, top_c - 0.7 * t])
    head = nub.union(neck).convex_hull
    arm = unary_union([beam, anchor, head]).buffer(0.05).buffer(-0.05)
    # pocket: the arm at rest and swung out (about its root) by the deflection it needs on the rim,
    # plus a stop gap; the pocket wall is the over-travel stop, so the arm can't be bent past it.
    rest = unary_union([Polygon(inner[:40] + outer[:40][::-1]), head])
    land = R + NUB_R - nub_radius_free(R)
    root = inner0 + ARM_L * t
    ang = np.degrees(np.arctan((land + STOP_GAP) / ARM_L))
    sws = [affinity.rotate(rest, sg * ang, origin=tuple(root)) for sg in (1, -1)]
    sw = max(sws, key=lambda g: Point(*C).distance(g.centroid))   # swing away from the wheel
    # along the root the pocket follows the arm WITHOUT its flare, so the fillet curves out to meet the
    # pocket wall (the slots either side end in a smooth ramp, not a square corner on the arm's edge)
    straight = Polygon([inner0 + x * t for x in ss] + [inner0 + x * t + w * n for x, w in zip(ss, taper_w)][::-1])
    pocket = unary_union([unary_union([rest, sw]).convex_hull, straight]).buffer(ARM_GAP, join_style="mitre")
    return arm, pocket, nub


# ---- the art ----------------------------------------------------------------

class Canvas:
    """Painter's algorithm over 4 colour regions that always tile the card exactly."""

    def __init__(self, card):
        self.card = card
        self.r = {BLACK: card, RED: Polygon(), TAN: Polygon(), CREAM: Polygon()}

    def paint(self, colour, g, clip=None):
        g = g.intersection(clip if clip is not None else self.card)
        if g.is_empty:
            return
        for k in self.r:
            if k != colour:
                self.r[k] = self.r[k].difference(g)
        self.r[colour] = self.r[colour].union(g)


def bat(c, span, tilt=0.0):
    """A bat silhouette, wingspan `span` mm, centred on c: smooth leading edge, 3 round scallops
    bitten out of each wing's trailing edge, a round body and two ears."""
    wing = spline([(0.02, 0.06), (0.14, 0.15), (0.30, 0.20), (0.44, 0.19), (0.50, 0.13),
                   (0.47, 0.02), (0.30, -0.05), (0.10, -0.09), (0.02, -0.06)])
    bites = [disk((x, y), r, 24) for x, y, r in ((0.42, -0.045, 0.065), (0.29, -0.10, 0.075), (0.15, -0.135, 0.07))]
    wing = wing.difference(unary_union(bites))
    body = affinity.scale(disk((0, 0), 1, 24), 0.055, 0.12)
    head = disk((0, 0.11), 0.05, 16)
    ear = Polygon([(0.012, 0.13), (0.05, 0.20), (0.055, 0.12)])
    g = unary_union([wing, mirror(wing, 0), body, head, ear, mirror(ear, 0)]).buffer(0.008).buffer(-0.008)
    g = affinity.scale(g, span, span, origin=(0, 0))
    return affinity.translate(affinity.rotate(g, tilt, origin=(0, 0)), *c)


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
# planted point-down before him. Black linework separates touching cream shapes.
HEAD = (CX, 49.0)
LINE = 0.7                       # black outline / strand width (over a bead)


def at(g):
    return affinity.translate(g, *HEAD)


def outlined(cv, colour, g, clip, w=LINE, edge=BLACK):
    cv.paint(edge, at(g.buffer(w, join_style="round")), clip)
    cv.paint(colour, at(g), clip)


def knight(cv, clip):
    S = lambda g: sym(g, 0)
    # red cloak behind everything, flaring to the frame's bottom corners, with black folds
    cloak = spline(sym_pts([(0, -7.0), (-10.0, -8.6), (-18.5, -12.2), (-24.5, -18.5), (-27.5, -26.0),
                            (-29.0, -34.0), (0, -34.0)]), n=400)
    cv.paint(RED, at(cloak), clip)
    for f in ([(-22.0, -17.6), (-24.0, -23.5), (-25.2, -31.5)], [(-19.5, -20.0), (-20.6, -26.0), (-21.0, -32.0)]):
        cv.paint(BLACK, at(S(taper(f, 0.9, 1.4))), clip)
    # breastplate, with tan plate seams (the fauld) either side of the sword
    chest = spline(sym_pts([(0, -11.5), (-7.8, -12.2), (-10.4, -17.0), (-11.6, -25.0), (-12.0, -34.0), (0, -34.0)]))
    outlined(cv, BLACK, chest, clip, edge=TAN)
    for y in (-27.6, -30.6):
        cv.paint(TAN, at(S(taper([(-10.8, y + 0.5), (-6.0, y - 0.2), (-1.5, y - 0.4)], 0.8, 0.8))), clip)
    # pauldrons: three overlapping curved lames each side, tan edges
    cap = spline([(-5.0, -10.8), (-10.0, -9.6), (-16.0, -10.6), (-21.4, -13.8), (-24.6, -18.8),
                  (-23.0, -20.8), (-17.0, -18.4), (-11.0, -16.9), (-5.0, -16.6)])
    for dx, dy in ((-2.2, -5.4), (-1.1, -2.7), (0.0, 0.0)):    # lowest lame first; each peeks out below the next
        outlined(cv, BLACK, S(affinity.translate(cap, dx, dy)), clip, w=0.8, edge=TAN)
    # long white hair falling to the shoulders, outlined, with swept-back black strands
    hair = spline(sym_pts([(0, 10.9), (-4.7, 10.2), (-7.9, 7.4), (-9.3, 2.4), (-9.8, -3.2), (-10.8, -8.4),
                           (-12.4, -12.6), (-7.6, -12.2), (-4.0, -9.8), (0, -9.4)]), n=400)
    outlined(cv, CREAM, hair, clip, w=0.8)
    for st in ([(-3.4, 9.6), (-6.0, 8.0), (-7.4, 5.0)], [(-6.9, 4.4), (-8.0, -1.0), (-9.2, -6.5), (-10.6, -10.6)],
               [(-6.2, -3.6), (-7.4, -7.6), (-8.6, -11.0)]):
        cv.paint(BLACK, at(S(taper(st, 0.75, 0.65))), clip)
    # gorget (neck armour) with two tan lames
    gorget = spline(sym_pts([(0, -9.4), (-4.4, -9.2), (-6.6, -10.8), (-7.2, -14.6), (0, -15.2)]))
    outlined(cv, BLACK, gorget, clip, w=0.8, edge=TAN)
    cv.paint(TAN, at(S(taper([(-6.0, -12.0), (-3.0, -12.6), (0, -12.8)], 0.8, 0.8))), clip)
    # the face: gaunt, stern; black outline makes the hairline and jaw
    face = spline(sym_pts([(0, 8.3), (-2.6, 8.4), (-4.6, 6.8), (-5.6, 3.4), (-5.7, 0.0), (-5.3, -3.6),
                           (-4.3, -6.4), (-2.6, -8.4), (0, -9.0)]))
    outlined(cv, CREAM, face, clip)
    cv.paint(TAN, at(S(taper([(-5.0, -1.4), (-4.6, -3.0), (-3.8, -4.4)], 1.2, 0.9))), clip)   # hollow cheeks
    cv.paint(BLACK, at(S(taper([(-5.0, 3.1), (-3.1, 2.9), (-1.0, 2.2)], 1.3, 1.0))), clip)    # heavy brows
    cv.paint(BLACK, at(taper([(0, 2.4), (0, 4.0)], 0.6, 0.6)), clip)                          # frown line
    eye = affinity.translate(affinity.rotate(affinity.scale(disk((0, 0), 1, 32), 1.4, 0.55), -6), -2.6, 1.05)
    cv.paint(RED, at(S(eye)), clip)
    cv.paint(BLACK, at(taper([(0.6, 1.4), (0.9, -1.4), (1.35, -3.4)], 0.7, 0.8)), clip)          # nose
    cv.paint(BLACK, at(taper([(-1.3, -3.9), (0, -4.3), (1.35, -3.6)], 0.7, 0.7)), clip)
    # moustache and pointed beard (white, outlined), the mouth a black line between them
    beard = Polygon(sym_pts([(0, -7.4), (-2.7, -7.1), (-2.5, -9.4), (-1.2, -11.2), (0, -12.6)])).buffer(0.3).buffer(-0.3)
    outlined(cv, CREAM, beard, clip, w=0.6)
    cv.paint(BLACK, at(taper([(-1.9, -6.7), (0, -7.0), (1.9, -6.7)], 0.7, 0.7)), clip)
    stache = Polygon(sym_pts([(0, -4.9), (-1.7, -5.0), (-3.3, -5.9), (-4.3, -8.0), (-2.7, -6.9),
                              (-1.2, -6.3), (0, -6.3)])).buffer(0.2).buffer(-0.2)
    outlined(cv, CREAM, stache, clip, w=0.6)
    cv.paint(TAN, at(taper([(0, -8.4), (0, -11.0)], 0.7, 0.7)), clip)                          # beard strand
    # the sword, planted point-down: blade, curved crossguard, wrapped grip, red pommel gem
    blade = Polygon([(-1.8, -40), (1.8, -40), (1.8, -26.0), (-1.8, -26.0)])
    outlined(cv, CREAM, blade, clip, w=0.7)
    cv.paint(TAN, at(box(-0.45, -40, 0.45, -26.4)), clip)
    guard = unary_union([box(-6.5, -26.4, 6.5, -24.6), S(taper([(-6.0, -25.5), (-8.2, -25.9), (-9.0, -27.6)], 1.8, 1.0))])
    outlined(cv, BLACK, guard, clip, w=0.7, edge=TAN)
    grip = box(-1.4, -24.6, 1.4, -18.8)                      # leather-wrapped grip with black bands
    outlined(cv, TAN, grip, clip, w=0.7)
    for y in (-21.0, -22.9):
        cv.paint(BLACK, at(box(-1.4, y - 0.35, 1.4, y + 0.35)), clip)
    cv.paint(TAN, at(disk((0, -17.2), 2.1, 32)), clip)
    cv.paint(RED, at(disk((0, -17.2), 1.3, 32)), clip)


def art(card):
    cv = Canvas(card)
    title_in = rrect(TITLE_BOX, FRAME_R)
    art_in = rrect(ART_BOX, FRAME_R)
    win = window()
    pt_in = win.buffer(MAT, join_style="round")
    for g in (title_in, art_in, pt_in):              # tan rims (black stays outside them)
        cv.paint(TAN, g.buffer(RIM, join_style="round"))
    cv.paint(BLACK, title_in)
    cv.paint(CREAM, title_text())
    cv.paint(CREAM, pt_in)

    # ---- scene, clipped to the art box
    clip = art_in
    cv.paint(CREAM, art_in)
    for c in (streak(3.0, 23.0, 66.6, 2.2), streak(3.0, 13.0, 62.8, 1.5, -0.3), streak(41.0, 60.0, 68.2, 2.0, -0.4),
              streak(43.0, 60.0, 48.0, 2.2), streak(47.0, 60.0, 44.4, 1.4, -0.3), streak(3.0, 18.0, 50.6, 2.0, -0.3),
              streak(3.0, 12.5, 47.2, 1.3)):
        cv.paint(TAN, c, clip)
    moon_c, moon_r = (CX, 50.5), 17.0
    cv.paint(RED, disk(moon_c, moon_r, 128), clip)
    cv.paint(TAN, streak(38.5, 55.0, 60.4, 1.7, 0.3), clip)          # one streak across the moon
    castle = unary_union([
        tower(3.0, 8.2, 38.5, 10.0), tower(8.2, 11.6, 33.5, 7.0), tower(11.6, 15.0, 29.5, 5.0),
        tower(54.6, 62.0, 41.0, 11.0), tower(51.0, 54.6, 35.0, 7.5), tower(47.6, 51.0, 30.0, 5.0),
        box(3.0, 18.0, 16.0, 27.0), box(47.0, 18.0, 60.0, 27.5)])
    cv.paint(BLACK, castle, clip)
    for w in (lancet(5.6, 34.0, 1.4, 3.2), lancet(57.2, 36.5, 1.4, 3.4), lancet(52.8, 31.6, 1.3, 2.6)):
        cv.paint(RED, w, clip)
    for c, span, tilt in (((19.5, 63.0), 12.5, 8.0), ((44.5, 65.0), 8.5, -6.0), ((53.0, 57.5), 6.5, 10.0),
                          ((41.0, 57.5), 5.5, -12.0)):
        cv.paint(BLACK, bat(c, span, tilt), clip)
    knight(cv, clip)
    cv.paint(CREAM, pt_in)                           # the window mat stays clean
    regions = {k: g.intersection(card).buffer(0) for k, g in cv.r.items()}
    return absorb_islands(regions)


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


def printability(regions):
    """Per colour: the area thinner than a bead and the islands under MIN_ISLAND mm^2."""
    rep = {}
    for k, g in regions.items():
        thin = g.difference(g.buffer(-BEAD / 2).buffer(BEAD / 2)).area
        small = [p.area for p in vt.polys_of(g) if p.area < MIN_ISLAND]
        rep[vt.PALETTE[k][0]] = (thin, len(vt.polys_of(g)), small)
    return rep


def front_prisms(regions, card, sockets):
    _, bands = vt.LAYOUTS["relief"]
    win = window()
    out = []
    for z0, z1, fill in bands:
        for slot, cols in fill.items():
            if tuple(cols) == vt.ALL:
                g = card
            elif len(cols) == 1:
                g = regions[cols[0]]
            else:
                g = unary_union([regions[c] for c in cols]).buffer(0.01, join_style="mitre") \
                    .buffer(-0.01, join_style="mitre").intersection(card)
            g = g.difference(win)
            if z0 == 0.0:
                out.append([0.0, SOCKET_DEPTH, g.difference(sockets), slot])
                out.append([SOCKET_DEPTH, z1, g, slot])
            else:
                out.append([z0, z1, g, slot])
    return out


# ---- previews -----------------------------------------------------------------

def preview(regions, card, wh, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    hexes = [h for _, h in vt.PALETTE]
    shows = [1, 5, 9]
    fig_, axes = plt.subplots(1, len(shows) + 1, figsize=(4.4 * (len(shows) + 1), 6.4))
    win = window()
    for ax, v in zip(axes, shows + [3]):
        rot = STEP * (v - 1)
        vd.draw(ax, affinity.rotate(wh["disc"], rot, origin=tuple(C)), hexes[CREAM])
        vd.draw(ax, affinity.rotate(wh["raised"], rot, origin=tuple(C)), hexes[BLACK])
        vd.draw(ax, card.difference(win), hexes[CREAM])
        for k in (TAN, RED, BLACK):
            vd.draw(ax, regions[k].difference(win), hexes[k])
        ax.set_aspect("equal")
        ax.set_facecolor("#9aa0a6")
        ax.set_xticks([]); ax.set_yticks([])
        if ax is axes[-1]:
            ax.set_xlim(WIN_C[0] - 14, CARD_W + 4); ax.set_ylim(-1, WIN_C[1] + 16)
            ax.set_title(f"window close-up ({v}/{v})")
        else:
            ax.set_xlim(-2, CARD_W + 5); ax.set_ylim(-2, CARD_H + 2)
            ax.set_title(f"dial at {v}/{v}")
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close(fig_)
    print(f"preview -> {path}")


def parts_preview(card, base, spacer, arm, pegs, wh, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_, axes = plt.subplots(1, 3, figsize=(17, 7), gridspec_kw=dict(width_ratios=[1, 1.15, 1]))
    for ax in axes[:2]:
        vd.draw(ax, card.difference(base), "#ffffff")
        vd.draw(ax, base, "#e8d2a8")
        vd.draw(ax, spacer, "#7a6a58")
        vd.draw(ax, arm, "#b03a2e")
        vd.draw(ax, disk(C, PIN_D / 2), "#3a2d25")
        vd.draw(ax, pegs, "#3a2d25")
        ax.plot(*np.asarray(wh["disc"].exterior.coords).T, color="#1f5fa8", lw=0.8)
    axes[0].set_xlim(-2, CARD_W + 5); axes[0].set_ylim(-2, CARD_H + 2)
    axes[0].set_title("back: base (beige), spacer (brown), detent (red); wheel outline blue")
    b = arm.bounds
    axes[1].set_xlim(b[0] - 2, b[2] + 2); axes[1].set_ylim(b[1] - 3, b[3] + 4)
    axes[1].set_title("detent: tapered arm, filleted root, nub seated in a V notch")
    ax = axes[2]
    vd.draw(ax, wh["disc"], "#e8d2a8")
    vd.draw(ax, wh["raised"], "#241B16")
    ax.set_xlim(C[0] - wh["R"] - 1, C[0] + wh["R"] + 1); ax.set_ylim(C[1] - wh["R"] - 1, C[1] + wh["R"] + 1)
    ax.set_title("wheel (top)")
    for ax in axes:
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close(fig_)
    print(f"preview -> {path}")


# ---- build --------------------------------------------------------------------

def main():
    PARTS.mkdir(parents=True, exist_ok=True)
    for f in PARTS.glob("*.stl"):
        f.unlink()
    card = vt.rounded_rect(CARD_W, CARD_H, CORNER_R)
    wh = wheel_geometry()
    R = wh["R"]
    arm, pocket, nub = detent(R)
    cavity = disk(C, R + WHEEL_CLR, 512).union(pocket)
    spacer = card.difference(cavity)
    base = card.difference(pocket)
    peg_disks = unary_union([disk(p, PEG_D / 2, 24) for p in PEGS])
    sockets = unary_union([disk(p, PEG_D / 2 + SOCKET_D_CLR, 24) for p in PEGS] +
                          [disk(C, PIN_D / 2 + SOCKET_D_CLR, 32)])

    protrude = C[0] + R - CARD_W
    left_wall = C[0] - R - WHEEL_CLR
    assert left_wall >= 1.5, f"wheel cavity is {left_wall:.2f} mm from the left edge"
    assert card.buffer(-0.9).contains(pocket), "detent pocket too close to the card edge"
    for p in PEGS:
        assert spacer.buffer(-0.8).contains(disk(p, PEG_D / 2, 24)), f"peg {p} not on solid spacer"
    assert arm.intersection(spacer).area > 0.5, "detent arm root must be anchored in the spacer"
    # seated, the nub overlaps both notch flanks by the preload (no more, no less) and nothing else touches
    k = PRELOAD * np.cos(np.radians(NOTCH_FLANK))
    assert nub.intersects(wh["disc"]) and not nub.buffer(-k - 0.01).intersects(wh["disc"]), "nub preload is off"
    assert arm.difference(nub.buffer(0.01)).disjoint(wh["disc"]), "only the nub may touch the wheel"
    assert spacer.disjoint(wh["disc"].buffer(WHEEL_CLR - 0.01)), "spacer runs into the wheel"
    mech = arm_mechanics(R)
    for name, (d, P, e) in mech.items():
        print(f"detent {name:11s}: deflection {d:.2f} mm, nub force {P:.2f} N, peak strain {100 * e:.2f} %")
    assert mech["at the stop"][2] < MAX_STRAIN, "the arm would be over-strained at its stop"
    assert rrect(ART_BOX, FRAME_R).buffer(RIM + 0.5).disjoint(window().buffer(MAT + RIM)), \
        "window frame runs into the art frame"

    print(f"card: {CARD_W:.1f} x {CARD_H:.1f} mm, {BACK_T + FRONT_T:.1f} mm thick assembled "
          f"({CARD_W / 25.4:.3f} x {CARD_H / 25.4:.3f} x {(BACK_T + FRONT_T) / 25.4:.3f} in)")
    print(f"wheel: centre ({C[0]:.2f}, {C[1]:.2f}), R {R:.2f} (notch bottoms {wh['r_valley']:.2f}), "
          f"channel {wh['r_in']:.2f}-{wh['r_out']:.2f}, digits at r {DIGIT_R}, rim protrudes {protrude:.2f} mm, "
          f"left wall {left_wall:.2f} mm")
    print(f"window: {WIN_WH[0]:.1f} x {WIN_WH[1]:.1f} mm at ({WIN_C[0]:.2f}, {WIN_C[1]:.2f}); digits {DIGIT_H} mm")

    regions = art(card)
    tiling = sum(g.area for g in regions.values())
    print(f"front colours (tiling {tiling:.2f} of {card.area:.2f} mm^2): " + ", ".join(
        f"{vt.PALETTE[k][0]} {100 * regions[k].area / card.area:.1f}%" for k in range(4)))
    for name, (thin, n, small) in printability(regions).items():
        print(f"  {name:5s}: {n:3d} islands, {thin:.2f} mm^2 thinner than {BEAD} mm"
              + (f", small islands {[round(a, 2) for a in small]}" if small else ""))

    arm_top = BACK_T - ARM_TOP_CLR
    back_prisms = [(0.0, BASE_T, base), (0.0, arm_top, arm), (BASE_T, BACK_T, spacer),
                   (BASE_T, BACK_T + PEG_H, disk(C, PIN_D / 2, 32)), (BACK_T, BACK_T + PEG_H, peg_disks)]
    wheel_prisms = [(0.0, WHEEL_FLOOR, wh["disc"]), (WHEEL_FLOOR, WHEEL_T, wh["raised"])]
    wheel_off = (2 * (CARD_W + PLATE_GAP) + R - C[0], R - C[1] + 2)
    objects = [
        ("front", (0.0, 0.0), front_prisms(regions, card, sockets)),
        ("back", (CARD_W + PLATE_GAP, 0.0), vd.slabs(back_prisms)),
        ("wheel", wheel_off, vd.slabs(wheel_prisms)),
    ]
    files, slots = [], []
    grams = [0.0] * 4
    for name, off, parts in objects:
        for i, (z0, z1, g, slot) in enumerate(parts):
            mesh = vt.extrude(g, z0, z1)
            if mesh is None:
                continue
            mesh.apply_translation([off[0], off[1], 0])
            fn = PARTS / f"{name}_{i}_{vt.PALETTE[slot][0]}.stl"
            mesh.export(fn)
            files.append(fn.name)
            slots.append(slot + 1)
            grams[slot] += g.area * (z1 - z0) / 1000 * 1.24
            print(f"  {fn.name:22s} z {z0:.1f}-{z1:.1f}  {g.area * (z1 - z0) / 1000:.2f} cm^3")
    (PARTS / "slice_args.txt").write_text(
        " ".join(files) + f" --assemble --extruders {','.join(map(str, slots))} "
        f"--colors \"{','.join(h for _, h in vt.PALETTE)}\" " + " ".join("--set " + x for x in SLICER_SET) + "\n")
    print("model grams per slot (PLA 1.24 g/cm^3, solid, before purge): " +
          ", ".join(f"{i + 1} {vt.PALETTE[i][0]} {g:.2f}" for i, g in enumerate(grams)))
    preview(regions, card, wh, OUT / "counter_preview.png")
    parts_preview(card, base, spacer, arm, peg_disks, wh, OUT / "parts_preview.png")


if __name__ == "__main__":
    main()
