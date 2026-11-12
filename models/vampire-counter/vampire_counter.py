#!/usr/bin/env python3
"""
Vampire counter token: the colour-fill alt art of the vampire-arcana card. Same 63 x 88 card, same
tarot frame (black card edge and rules, "VAMPIRE" in Georgia caps on a white title plate, the
1/1 ... 9/9 dial window standing on the bottom edge of a footer plate, a bat either side), same face-down flat inlay
and same back. Only the art plate differs: here it is flat colour (an elder vampire knight in a red
cloak before a blood moon, copper cloud streaks, a black castle), where arcana is a woodcut.

Spec: see README.md in this folder.

This module also HOSTS everything the cards share. models/vampire-arcana imports it, and
models/vampire-cathedral and models/token-dock use it through arcana:
  * the card frame: `frame()` paints the plates, title, window box and footer bats; `finish()` clears
    the window mat and cleans the regions (slivers, islands, grid snap); `back_regions()` is the back;
  * the dial mechanism: a wheel centred in the card with its thumb rim at the BOTTOM edge, V notches,
    a reeded rim, a tapered filleted cantilever detent, a bevelled window, sockets, pegs;
  * the face-down build `write_plate()` with its as-printed `assembly_check()`, the `preview()` sheet
    and the side `section_preview()`.
A card is then just a painter's-algorithm scene in the art plate (see `front_regions()` here).

Parts (printed side by side on one plate):
  front  face-down: a 0.4 mm colour inlay (2 layers), white above, sockets underneath, the window
         bevelled through
  back   base plate + spacer frame with the wheel cavity, an axle pin, 6 alignment pegs and the detent
         arm; its face has the black edge and gold crescent inlaid in the same 2 layers
  wheel  face-down: black "N/N" digits inlaid flat in white

Every colour change is in layers 1-2, so the whole plate needs ~6 swaps however much ink the art has.

Run (from the repo root):
    .venv\\Scripts\\python.exe models\\vampire-counter\\vampire_counter.py
Outputs (millimetres) go to models\\vampire-counter\\out\\
    parts/<object>_<n>_<colour>.stl   parts laid out as on the plate; load as ONE object (--assemble)
    parts/slice_args.txt              the matching slice_bambu.py arguments
    counter_preview.png               the face at 1/1, 5/5, 9/9, a nozzle simulation, and the back
    parts_preview.png                 back (spacer, detent, pin, pegs) and wheel
    section_preview.png               side section of the printed parts, re-assembled
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

CARD_W, CARD_H, CORNER_R = 63.0, 88.0, 3.0
CX = CARD_W / 2

# ---- the card frame (shared with vampire-arcana) ----
# Plates (white interiors) as (x0, y0, x1, y1). The black between them is the whole border:
# 1.8 mm card edge, 1.2 mm rules. The footer is sized to frame the dial window, which the wheel fixes.
EDGE, RULE = 1.8, 1.2
FOOTER = (EDGE, EDGE, CARD_W - EDGE, 18.0)
ART = (EDGE, FOOTER[3] + RULE, CARD_W - EDGE, 72.6)
TITLE_BOX = (EDGE, ART[3] + RULE, CARD_W - EDGE, CARD_H - EDGE)
PLATE_R = CORNER_R - EDGE        # concentric with the card's corners

# Title: black roman caps on the white plate, with generous margins (Georgia: of the installed romans
# it keeps the most ink, 99.8 %, through a 0.42 mm open / 0.3 mm close).
TITLE = "VAMPIRE"
TITLE_FONT = r"C:\Windows\Fonts\georgia.ttf"
TITLE_CAP = 6.0
TITLE_TRACK = 1.1
TITLE_BOLDEN = 0.06

# Dial window: bevelled out from the wheel to the face (one layer per step, 45 deg), so the digits stay
# whole when read at an angle; the straight 2 mm hole of v2 hid 1.8 mm of their bottoms at 45 deg.
# A black rule frames the bevel's mouth and runs into the card's bottom edge; a bat either side.
LAYER = 0.2
WIN_BEVEL = (1.0, 1.0)           # bevel run in x and y
BEVEL_STEPS = 5                  # layers the bevel takes, below the inlay
MOUTH_R = 2.2                    # corner radius of the bevel's mouth
WIN_RULE = 0.7
FOOTER_BAT = 11.0                # wingspan

# Face-down inlay
INLAY = 0.4                      # two 0.2 mm layers: opaque enough for ink, red and gold over white
BACK_ART = True                  # border + crescent inlaid on the card's back (no extra swaps)

# Digits: Bahnschrift Bold Condensed; the slash is scaled to the digit height (its natural
# descender/overshoot would make the window taller, and the window height sets the wheel size).
DIGIT_FONT = (r"C:\Windows\Fonts\bahnschrift.ttf", {"wght": 700, "wdth": 75})
DIGIT_H = 7.5                   # digit cap height (8.0 in v2, see DIGIT_R; the vampire-dial digits were 3.0 mm)
DIGIT_GAP = 0.7                 # between the digits and the slash
DIGIT_BOLDEN = 0.05
VALUES = range(1, 10)
STEP = 360 / len(VALUES)        # 40 degrees per value
WIN_PAD = (0.8, 0.6)            # window margin around the largest "N/N" (x, y)
WIN_R = 1.5

# Wheel: centred in the card and as large as the side walls allow, with the window straight below the
# axle and the rim poking out of the card's BOTTOM edge. Turning it counter-clockwise (pushing the rim
# to the RIGHT) counts up. In v2 the wheel sat to the right and its rim poked out of the right edge.
# The rim must clear the window by the bevel, a frame strip (3 beads) and the protrusion: 8 mm digits
# (ring r 21) leave 2.5 mm for bevel + protrusion, 7.5 mm digits (ring r 19.75) leave 4.0 mm.
WIN_ANGLE = -90.0               # straight down: the value sits on the card's centre line
DIGIT_R = 19.75                 # smallest ring radius that hides both neighbours (searched in 0.25 steps)
PROTRUDE = 2.0                  # rim past the card's bottom edge
SIDE_WALL = 1.6                 # spacer left beside the wheel at its widest; this sets the wheel's radius
CHANNEL_MARGIN = 0.4
MIN_RIM = 0.8                   # least rim between the digit channel and the notch bottoms (WHEEL_RIM is derived)
# 9 V notches = the detent seats and the thumb grip. v1 had round scallops (R 6) under a small nub
# (R 1.2): near the bottom the nub rose only s^2/(2*4.8), so the wheel wiggled about a value with
# almost no restoring force. Straight flanks lift the nub linearly (0.7 mm per mm of turn at 35 deg).
NOTCH_DEPTH = 1.3
NOTCH_FLANK = 35.0              # flank angle from the rim's tangent (steeper = firmer centring, harder click)
NOTCH_EDGE_R = 0.6              # rounding of the notch's rim edges
# Reeded rim between the notches, for grip: only PROTRUDE of rim shows, and at rest one notch. The slits
# are too narrow for the nub to drop into (0.06 mm), so they are not detents. GRIP_W = 0: smooth rim.
GRIP_W, GRIP_DEPTH, GRIP_PITCH, GRIP_SKIP = 0.7, 0.7, 4.0, 2    # mm, mm, deg, pitches kept clear of a notch
WHEEL_T = 1.8                   # disc thickness (digits inlaid in its face, which prints on the plate)
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

# Detent: a tapered cantilever in the spacer above the wheel, running up to the right; its round nub seats on
# both flanks of a notch. v1 (15 x 1.0 mm, square root) bent to 1.07 % strain over the rim from a
# sharp corner and held the wheel with 0.13 N. This one: ~0.52 % at the rim, 0.40 N seated, filleted root.
# 9 notches are 40 deg apart, so a notch rests at the bottom of the rim (under the thumb) only if the
# detent sits 160 deg from it.
DETENT_ANGLE = 110.0
ARM_SIDE = 1                    # the arm runs clockwise (up to the right) from the nub
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
FRONT_T = 2.0

# Printability limits for the art (checked, not just hoped for)
BEAD = 0.45                     # narrower than this prints as a broken single bead
MIN_ISLAND = 1.0                # mm^2

PLATE_GAP = 8.0
# Arachne tuned for 1-3 bead strokes (vampire-dial), plus a slow first layer: face-down, the art IS
# the first layer (the Token Arcana author's advice for a 0.4 nozzle).
SLICER_SET = ["wall_generator=arachne", "wall_transition_angle=30", "wall_transition_filter_deviation=50%",
              "min_bead_width=50%", "wall_transition_length=50%",
              "initial_layer_speed=30", "initial_layer_infill_speed=60"]

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
        print(f"  warning: {TITLE_FONT} not found, title falls back to DejaVu Serif")
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
    a = np.radians(WIN_ANGLE)
    P0 = DIGIT_R * np.array([np.cos(a), np.sin(a)])          # window centre relative to C
    texts = [nn_text(v, P0) for v in VALUES]
    W = max(t.bounds[2] - t.bounds[0] for t in texts) + 2 * WIN_PAD[0]
    H = max(t.bounds[3] - t.bounds[1] for t in texts) + 2 * WIN_PAD[1]
    win0 = vd.rounded_box(*P0, W, H, WIN_R)
    pts = np.array(win0.exterior.coords)
    r_out = np.hypot(*pts.T).max() + CHANNEL_MARGIN
    R = CARD_W / 2 - SIDE_WALL - WHEEL_CLR
    rim = R - r_out - NOTCH_DEPTH                            # between the digit channel and the notch bottoms
    assert rim >= MIN_RIM, f"only {rim:.2f} mm of rim outside the digit channel"
    C = np.array([CARD_W / 2, R - PROTRUDE])
    return C, R, C + P0, (W, H), rim


C, R_WHEEL, WIN_C, WIN_WH, WHEEL_RIM = dial_layout()


def opening(f):
    """The window's opening: f = 0 at the wheel (the window itself) ... 1 at the face (the bevel's mouth)."""
    return vd.rounded_box(*WIN_C, WIN_WH[0] + 2 * WIN_BEVEL[0] * f, WIN_WH[1] + 2 * WIN_BEVEL[1] * f,
                          WIN_R + (MOUTH_R - WIN_R) * f)


def window():
    return opening(0.0)


def mouth():
    return opening(1.0)


def grip_slits(R):
    out = []
    for a0 in DETENT_ANGLE + STEP * np.arange(len(VALUES)):
        for k in range(GRIP_SKIP, int(round(STEP / GRIP_PITCH)) - GRIP_SKIP + 1):
            s = box(R - GRIP_DEPTH, -GRIP_W / 2, R + 1, GRIP_W / 2)
            out.append(affinity.translate(affinity.rotate(s, a0 + k * GRIP_PITCH, origin=(0, 0)), *C))
    return unary_union(out)


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
    if GRIP_W:
        disc = disc.difference(grip_slits(R))
    # value v is laid out upright at the window, then turned back (v-1) steps: turning the wheel
    # (v-1) steps counter-clockwise brings it into the window.
    groups = [affinity.rotate(nn_text(v, WIN_C), -STEP * (v - 1), origin=tuple(C)) for v in VALUES]
    for g in groups:
        assert channel.contains(g), "digits must sit inside the channel"
    for i, g in enumerate(groups):       # every value, one step either side of the window, stays hidden
        for s in (-STEP, STEP):
            nb = affinity.rotate(g, STEP * i + s, origin=tuple(C))
            assert not nb.intersects(win.buffer(0.3)), "a neighbouring value would show in the window"
    return dict(R=R, r_in=r_in, r_out=r_out, r_valley=r_valley, disc=disc, groups=groups)


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


def mechanism():
    """The back, wheel and detent, with every fit and strain check. Shared by both cards."""
    card = vt.rounded_rect(CARD_W, CARD_H, CORNER_R)
    wh = wheel_geometry()
    R = wh["R"]
    arm, pocket, nub = detent(R)
    cavity = disk(C, R + WHEEL_CLR, 512).union(pocket)
    spacer = card.difference(cavity)
    base = card.difference(pocket)
    pegs = unary_union([disk(p, PEG_D / 2, 24) for p in PEGS])
    sockets = unary_union([disk(p, PEG_D / 2 + SOCKET_D_CLR, 24) for p in PEGS] +
                          [disk(C, PIN_D / 2 + SOCKET_D_CLR, 32)])

    side_wall = C[0] - R - WHEEL_CLR
    assert side_wall >= 1.5, f"wheel cavity is {side_wall:.2f} mm from the card's side edges"
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
    mo = mouth()
    fr = mo.buffer(WIN_RULE).bounds
    assert mo.bounds[1] >= 3 * BEAD, "under three beads of frame left below the window's mouth"
    assert FOOTER[0] + 0.6 <= fr[0] and fr[2] <= FOOTER[2] - 0.6 and fr[3] <= FOOTER[3] - 0.6, \
        "the window's ruled mouth must sit inside the footer plate"
    assert FRONT_T - INLAY - BEVEL_STEPS * LAYER >= SOCKET_DEPTH - 1e-9, "the bevel runs into the socket layers"

    print(f"card: {CARD_W:.1f} x {CARD_H:.1f} mm, {BACK_T + FRONT_T:.1f} mm thick assembled "
          f"({CARD_W / 25.4:.3f} x {CARD_H / 25.4:.3f} x {(BACK_T + FRONT_T) / 25.4:.3f} in)")
    print(f"wheel: centre ({C[0]:.2f}, {C[1]:.2f}), R {R:.2f} (notch bottoms {wh['r_valley']:.2f}), "
          f"channel {wh['r_in']:.2f}-{wh['r_out']:.2f}, digits at r {DIGIT_R}, rim band {WHEEL_RIM:.2f} mm; the rim "
          f"protrudes {PROTRUDE:.2f} mm from the bottom edge over {2 * np.sqrt(R ** 2 - (R - PROTRUDE) ** 2):.1f} mm, "
          f"side walls {side_wall:.2f} mm")
    print(f"plates: title {TITLE_BOX[3] - TITLE_BOX[1]:.1f}, art {ART[3] - ART[1]:.1f}, footer "
          f"{FOOTER[3] - FOOTER[1]:.1f} mm tall; window {WIN_WH[0]:.1f} x {WIN_WH[1]:.1f} at "
          f"({WIN_C[0]:.2f}, {WIN_C[1]:.2f}), mouth {mo.bounds[2] - mo.bounds[0]:.1f} x "
          f"{mo.bounds[3] - mo.bounds[1]:.1f}; digits {DIGIT_H} mm")
    return dict(card=card, wh=wh, arm=arm, spacer=spacer, base=base, pegs=pegs, sockets=sockets)


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


def frame(cv):
    """Paint the card's frame: black edge and rules (the canvas starts black), white title, art and
    footer plates, the title, and the dial window's ruled box with a bat either side.
    Returns the art plate, which the scene is clipped to."""
    title_in, art_in, foot_in = rrect(TITLE_BOX, PLATE_R), rrect(ART, PLATE_R), rrect(FOOTER, PLATE_R)
    for g in (title_in, art_in, foot_in):
        cv.paint(PAPER, g)
    cv.paint(INK, title_text())
    mo = mouth()
    cv.paint(INK, mo.buffer(WIN_RULE, join_style="round"))       # its bottom runs into the card's edge
    cv.paint(PAPER, mo)
    fr = mo.buffer(WIN_RULE).bounds
    lx, rx = (FOOTER[0] + fr[0]) / 2, (fr[2] + FOOTER[2]) / 2
    fy = (FOOTER[1] + fr[3]) / 2                                 # level with the window's box
    for x in (lx, rx):
        cv.paint(INK, bat((x, fy), FOOTER_BAT, 0.0), foot_in)
    return art_in


def finish(cv, card):
    """After the scene: clear the window's mouth again, then make every region printable and snappable."""
    cv.paint(PAPER, mouth())
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


def overlap(a, b):
    """Largest area two parts' bands (z0, z1, shape, slot) share in any common z range."""
    worst = 0.0
    for z0, z1, g, _ in a:
        for y0, y1, h, _ in b:
            if min(z1, y1) - max(z0, y0) < 1e-6 or g.is_empty or h.is_empty:
                continue
            gb, hb = g.bounds, h.bounds
            if gb[2] < hb[0] or hb[2] < gb[0] or gb[3] < hb[1] or hb[3] < gb[1]:
                continue
            worst = max(worst, g.intersection(h).area)
    return worst


def merge_slices(slices):
    """Join consecutive depth slices (d0, d1, key, shape) that share a key."""
    out = []
    for d0, d1, key, g in slices:
        if out and out[-1][2] == key and abs(out[-1][1] - d0) < 1e-9:
            out[-1] = (out[-1][0], d1, key, out[-1][3])
        else:
            out.append((d0, d1, key, g))
    return out


def front_bands(card, regions, sockets):
    """The front as it prints (face-down, mirrored), sliced by depth below the face, one slice per
    layer: the colour inlay round the bevel's mouth, the bevel stepping in to the window, then the
    straight window with the peg and pin sockets."""
    n_inlay = int(round(INLAY / LAYER))
    slices = []
    for i in range(int(round(FRONT_T / LAYER))):
        d0, d1 = i * LAYER, (i + 1) * LAYER
        f = max(0.0, 1.0 - max(0, i + 1 - n_inlay) / BEVEL_STEPS)
        socketed = d0 >= FRONT_T - SOCKET_DEPTH - 1e-9
        g = card.difference(opening(f))
        slices.append((d0, d1, (round(f, 4), socketed), g.difference(sockets) if socketed else g))
    bands = []
    for d0, d1, _, g in merge_slices(slices):
        if d1 <= INLAY + 1e-9:
            bands += [(d0, d1, mirror(regions[k].difference(mouth()), CX), k) for k in range(4)]
        else:
            bands.append((d0, d1, mirror(g, CX), PAPER))
    return bands


def assembly_check(front, back_parts, wheel, wx):
    """Assemble the parts AS PRINTED (not the design shapes): turn the face-down front and wheel over,
    drop the wheel on the back's pin, and check that no two parts share any volume, that every value
    sits centred in the front's window with the detent nub seated symmetrically in a notch, and that
    a notch rests at the bottom of the rim. This catches a print transform that is wrong (the v2 back
    was mirrored, which the design-frame asserts in mechanism() could not see).
    Returns the assembly as {part: bands}."""
    turn = lambda bands, axis, z_face: [(z_face - z1, z_face - z0, mirror(g, axis), s)
                                        for z0, z1, g, s in bands if not g.is_empty]
    at = lambda b, z0, z1: abs(b[0] - z0) < 1e-6 and abs(b[1] - z1) < 1e-6
    arm = next(b for b in back_parts if at(b, 0.0, BACK_T - ARM_TOP_CLR))
    pin = next(b for b in back_parts if at(b, BASE_T, BACK_T + PEG_H))[2]
    body = [b for b in back_parts if b is not arm and not b[2].is_empty]      # the back as printed, cavity up
    front_a = turn(front, CX, BACK_T + FRONT_T)
    wheel_a = turn(wheel, wx, BASE_T + WHEEL_T)                              # face toward the window
    disc = max((b[2] for b in wheel_a), key=lambda g: g.area)
    pc, hc = np.array(pin.centroid.coords[0]), np.array(Polygon(disc.interiors[0]).centroid.coords[0])
    assert np.allclose(pc, C, atol=0.01), f"printed pin at {pc}, design wheel centre {C}"
    wheel_a = [(z0, z1, affinity.translate(g, *(pc - hc)), s) for z0, z1, g, s in wheel_a]
    disc = max((b[2] for b in wheel_a), key=lambda g: g.area)
    ink = next(g for _, _, g, s in wheel_a if s == INK)
    for a, b, what in ((front_a, body, "front and back"), (front_a, wheel_a, "front and wheel"),
                       (body, wheel_a, "back and wheel")):                  # the arm preloads the wheel: below
        ov = overlap(a, b)
        assert ov < 0.01, f"{what} collide ({ov:.3f} mm^2): a peg without a socket, or a part mirrored wrongly"
    # nub seated: turning the wheel a hair either way must load it equally (a centred V notch)
    ov = [arm[2].intersection(affinity.rotate(disc, d, origin=tuple(pc))).area for d in (-0.5, 0.0, 0.5)]
    assert ov[1] > 0 and abs(ov[0] - ov[2]) < 0.02 * max(ov), f"nub not centred in a notch: {ov}"
    # the window as built: the largest hole in the front's deepest band
    deep = min(front_a, key=lambda b: b[0])[2]
    win = max((Polygon(r) for r in deep.interiors), key=lambda g: g.area)
    wc = np.array(win.centroid.coords[0])
    worst = 0.0
    for v in VALUES:
        shown = affinity.rotate(ink, STEP * (v - 1), origin=tuple(pc)).intersection(win)
        want = nn_text(v, WIN_C)
        assert abs(shown.area - want.area) < 0.01 * want.area, f"{v}/{v}: window shows the wrong ink"
        b = np.array(shown.bounds)
        err = np.hypot((b[0] + b[2]) / 2 - wc[0], (b[1] + b[3]) / 2 - wc[1])   # ink box centre vs window
        worst = max(worst, err)
        assert err < 0.1, f"{v}/{v} is {err:.2f} mm off the window centre"
    R = np.hypot(*(np.array(disc.exterior.coords) - pc).T).max()
    low = disc.intersection(box(pc[0] - 0.3, pc[1] - R - 1, pc[0] + 0.3, pc[1] - R + 3))
    assert low.bounds[1] > pc[1] - R + 0.5 * NOTCH_DEPTH, "no notch at the bottom of the rim at rest"
    print(f"assembly check (parts as printed): no collisions; pin on the wheel centre; nub centred in a notch; "
          f"all {len(VALUES)} values centred in the window (worst {worst:.3f} mm); a notch rests at the bottom "
          f"of the rim")
    return dict(back=[arm] + body, wheel=wheel_a, front=front_a)


def write_plate(m, regions, back, parts_dir):
    """Write the face-down plate (front, back, wheel side by side) as colour-part STLs + slice args.
    Front and wheel lie face-down, so their 2D shapes are mirrored. The back lies on its back face with
    the cavity up, so seen from above it is already in the front-view frame: its mechanism is NOT
    mirrored (v2 mirrored it, so the wheel sat on the wrong side and the window saw the ring ~22 deg
    off a detent position, half a value). Only its art is mirrored, as it is drawn as seen from behind."""
    parts_dir.mkdir(parents=True, exist_ok=True)
    for f in parts_dir.glob("*.stl"):
        f.unlink()
    card, wh = m["card"], m["wh"]
    mx = CX
    digits = unary_union(wh["groups"])
    front = front_bands(card, regions, m["sockets"])
    arm_top = BACK_T - ARM_TOP_CLR
    back_parts = [(0.0, INLAY, mirror(back[k], mx).intersection(m["base"]), k) for k in range(4)] + [
        (INLAY, BASE_T, m["base"], PAPER),
        (0.0, arm_top, m["arm"], PAPER),                  # stands free in a slot through the plate
        (BASE_T, BACK_T, m["spacer"], PAPER),
        (BASE_T, BACK_T + PEG_H, disk(C, PIN_D / 2, 32), PAPER),
        (BACK_T, BACK_T + PEG_H, m["pegs"], PAPER)]
    wx = C[0]
    wheel = [(0.0, INLAY, mirror(digits, wx), INK),
             (0.0, INLAY, mirror(wh["disc"].difference(digits), wx), PAPER),
             (INLAY, WHEEL_T, mirror(wh["disc"], wx), PAPER)]
    asm = assembly_check(front, back_parts, wheel, wx)
    section_preview(asm, [(C[0], (-PROTRUDE - 1, CARD_H + 1), 4.0, f"through the window and axle (x = {C[0]:.1f}), z x4"),
                          (C[0], (-PROTRUDE - 1, 24.0), 1.0, "window and bevel, true scale")],
                    parts_dir.parent / "section_preview.png")
    R = wh["R"]
    wheel_off = (2 * (CARD_W + PLATE_GAP) + R - C[0], R - C[1] + 2)
    objects = [("front", (0.0, 0.0), front), ("back", (CARD_W + PLATE_GAP, 0.0), back_parts),
               ("wheel", wheel_off, wheel)]
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
            print(f"  {fn.name:22s} z {z0:.1f}-{z1:.1f}  {g.area * (z1 - z0) / 1000:.2f} cm^3")
    (parts_dir / "slice_args.txt").write_text(
        " ".join(files) + f" --assemble --extruders {','.join(map(str, slots))} "
        f"--colors \"{','.join(h for _, h in PALETTE)}\" " + " ".join("--set " + x for x in SLICER_SET) + "\n")
    print("model grams per slot (PLA 1.24 g/cm^3, solid, before purge): " +
          ", ".join(f"{i + 1} {PALETTE[i][0]} {g:.2f}" for i, g in enumerate(grams)))


SECTION_TONES = dict(back="#7a6a58", wheel="#1f5fa8", front="#b03a2e")


def section_preview(asm, cuts, path, tones=None, boxes=()):
    """Side sections (y across, z up) of re-assembled parts {name: bands}.
    cuts: [(x, (y0, y1), z scale, title)]; boxes: [(cut index, (y, z, w, h))] drawn grey (magnets)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch, Rectangle
    tones = tones or SECTION_TONES
    z_top = max(b[1] for bands in asm.values() for b in bands)
    fig_, axes = plt.subplots(len(cuts), 1, figsize=(17, 3.7 * len(cuts)), squeeze=False)
    for i, (ax, (x, (y0, y1), zs, title)) in enumerate(zip(axes[:, 0], cuts)):
        line = LineString([(x, -50), (x, 300)])
        for name, bands in asm.items():
            for z0, z1, g, _ in bands:
                cut = g.intersection(line)
                for seg in getattr(cut, "geoms", [cut]):
                    if seg.is_empty or seg.geom_type != "LineString":
                        continue
                    a, b = seg.coords[0][1], seg.coords[-1][1]
                    ax.add_patch(Rectangle((a, z0), b - a, z1 - z0, facecolor=tones[name], edgecolor="none"))
        for j, (y, z, w, h) in boxes:
            if j == i:
                ax.add_patch(Rectangle((y, z), w, h, facecolor="#8d939b", edgecolor="k", lw=0.5))
        ax.set_xlim(y0, y1); ax.set_ylim(-0.6, z_top + 0.8); ax.set_aspect(zs)
        ax.set_title(title, fontsize=9); ax.set_xlabel("y (mm)"); ax.set_ylabel("z (mm)")
        ax.legend(handles=[Patch(facecolor=c, label=n) for n, c in tones.items() if n in asm],
                  loc="upper right", fontsize=8, ncol=len(tones))
    plt.tight_layout()
    plt.savefig(path, dpi=110)
    plt.close(fig_)
    print(f"preview -> {path}")


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
    cv.paint(BLOOD, at(cloak), clip)
    for f in ([(-22.0, -17.6), (-24.2, -23.5), (-25.8, -33.5)], [(-19.5, -20.0), (-20.6, -26.0), (-21.2, -33.5)]):
        cv.paint(INK, at(S(taper(f, 0.9, 1.4))), clip)
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
    for c in (streak(x0 - 1, 23.0, 67.8, 2.2), streak(x0 - 1, 13.0, 64.0, 1.5, -0.3),
              streak(41.0, x1 + 1, 69.4, 2.0, -0.4), streak(43.0, x1 + 1, 49.2, 2.2),
              streak(47.0, x1 + 1, 45.6, 1.4, -0.3), streak(x0 - 1, 18.0, 51.8, 2.0, -0.3),
              streak(x0 - 1, 12.5, 48.4, 1.3)):
        cv.paint(GOLD, c, clip)
    cv.paint(BLOOD, disk(MOON_C, MOON_R, 128), clip)
    cv.paint(GOLD, streak(38.5, 55.0, 61.6, 1.7, 0.3), clip)          # one streak across the moon
    castle = unary_union([
        tower(x0 - 1, 8.2, 39.7, 10.0), tower(8.2, 11.6, 34.7, 7.0), tower(11.6, 15.0, 30.7, 5.0),
        tower(54.6, x1 + 1, 42.2, 11.0), tower(51.0, 54.6, 36.2, 7.5), tower(47.6, 51.0, 31.2, 5.0),
        box(x0 - 1, 18.0, 16.0, 28.2), box(47.0, 18.0, x1 + 1, 28.7)])
    cv.paint(INK, castle, clip)
    for w in (lancet(5.0, 35.2, 1.4, 3.2), lancet(57.6, 37.7, 1.4, 3.4), lancet(52.8, 32.8, 1.3, 2.6)):
        cv.paint(BLOOD, w, clip)
    for c, span, tilt in (((19.5, 64.2), 12.5, 8.0), ((44.5, 66.2), 8.5, -6.0), ((53.0, 58.7), 6.5, 10.0),
                          ((41.0, 58.7), 5.5, -12.0)):
        cv.paint(INK, bat(c, span, tilt), clip)
    knight(cv, clip)
    return finish(cv, card)


# ---- previews -----------------------------------------------------------------

def nozzle_sim(g):
    """Roughly what a 0.4 nozzle keeps: open with a bead, close a little."""
    return g.buffer(-0.21).buffer(0.21).buffer(0.15).buffer(-0.15)


def draw_face(ax, regions, wh, v, sim=False):
    hexes = [h for _, h in PALETTE]
    rot = STEP * (v - 1)
    win = mouth()
    vd.draw(ax, affinity.rotate(wh["disc"], rot, origin=tuple(C)), hexes[PAPER])
    vd.draw(ax, affinity.rotate(unary_union(wh["groups"]), rot, origin=tuple(C)), hexes[INK])
    vd.draw(ax, win.difference(window()), "#d5cfc2")              # the bevel
    vd.draw(ax, regions[PAPER].difference(win), hexes[PAPER])
    for k in (INK, BLOOD, GOLD):
        g = regions[k].difference(win)
        vd.draw(ax, nozzle_sim(g) if sim else g, hexes[k])
    ax.set_aspect("equal"); ax.set_facecolor("#9aa0a6"); ax.set_xticks([]); ax.set_yticks([])


def preview(regions, back, wh, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig_, axes = plt.subplots(1, 5, figsize=(22, 6.6))
    for ax, (v, sim, t) in zip(axes, [(1, False, "1/1"), (5, False, "5/5"), (9, False, "9/9"),
                                      (1, True, "nozzle simulation (ink, red, gold opened 0.42 mm)")]):
        draw_face(ax, regions, wh, v, sim)
        ax.set_xlim(-1, CARD_W + 1); ax.set_ylim(-PROTRUDE - 1.5, CARD_H + 1); ax.set_title(t, fontsize=9)
    ax = axes[4]
    hexes = [h for _, h in PALETTE]
    for k in range(4):
        vd.draw(ax, back[k], hexes[k])
    ax.set_aspect("equal"); ax.set_facecolor("#9aa0a6"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlim(-1, CARD_W + 1); ax.set_ylim(-PROTRUDE - 1.5, CARD_H + 1); ax.set_title("back (as seen from behind)", fontsize=9)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close(fig_)
    print(f"preview -> {path}")


def parts_preview(m, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    card, wh, arm = m["card"], m["wh"], m["arm"]
    fig_, axes = plt.subplots(1, 3, figsize=(17, 7), gridspec_kw=dict(width_ratios=[1, 1.15, 1]))
    for ax in axes[:2]:
        vd.draw(ax, card.difference(m["base"]), "#ffffff")
        vd.draw(ax, m["base"], "#e8d2a8")
        vd.draw(ax, m["spacer"], "#7a6a58")
        vd.draw(ax, arm, "#b03a2e")
        vd.draw(ax, disk(C, PIN_D / 2), "#3a2d25")
        vd.draw(ax, m["pegs"], "#3a2d25")
        ax.plot(*np.asarray(wh["disc"].exterior.coords).T, color="#1f5fa8", lw=0.8)
    axes[0].set_xlim(-2, CARD_W + 2); axes[0].set_ylim(-PROTRUDE - 2, CARD_H + 2)
    axes[0].set_title("back: base (beige), spacer (brown), detent (red); wheel outline blue")
    b = arm.bounds
    axes[1].set_xlim(b[0] - 2, b[2] + 2); axes[1].set_ylim(b[1] - 3, b[3] + 4)
    axes[1].set_title("detent: tapered arm, filleted root, nub seated in a V notch")
    ax = axes[2]
    vd.draw(ax, wh["disc"], PALETTE[PAPER][1])
    vd.draw(ax, unary_union(wh["groups"]), PALETTE[INK][1])
    ax.set_xlim(C[0] - wh["R"] - 1, C[0] + wh["R"] + 1); ax.set_ylim(C[1] - wh["R"] - 1, C[1] + wh["R"] + 1)
    ax.set_title("wheel (face, digits inlaid): V notches, reeded rim")
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
    preview(regions, back, m["wh"], OUT / "counter_preview.png")
    parts_preview(m, OUT / "parts_preview.png")


if __name__ == "__main__":
    main()
