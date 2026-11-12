#!/usr/bin/env python3
"""
Vampire token with a P/T dial: the 4-colour relief vampire token (models/vampire-token, layout
"relief") rebuilt as a sandwich with a thumbwheel inside. Turning the wheel shows 1/1 ... 9/9 in a
window cut where the art's 1/1 box is.

Spec: see README.md in this folder.

Parts (all printed in one go, on one plate, in the orientation they are assembled in - no flipping):
  back   base plate + spacer frame with the wheel cavity, an axle pin, 4 alignment pegs and a
         spring detent arm (a cantilever, free over a slot through the base) that clicks into the
         wheel's 9 scallops
  wheel  scalloped disc; its rim pokes out of the card's right edge as a thumb grip. Raised
         black-topped "N/N" digits stand in a recessed cream channel.
  front  the relief art (Z bands as models/vampire-token v3) with the window through it and sockets
         underneath for the pin and pegs. The art is simplified so nothing is narrower than a bead
         (no stray specks), and the type line is re-set as printable vector text.
Assembly: wheel onto the pin, front on top (pegs into sockets). A drop of CA glue on the pegs.

Colour bands: every layer of the whole plate is ONE filament, exactly like the relief token
(cream 0-1.0, tan 1.0-1.2, red 1.2-1.6, black 1.6+). The back and wheel just take the colour of the
band they are in, so the dial adds no filament swaps: still 3, all light -> dark.

Run (from the repo root):
    .venv\\Scripts\\python.exe models\\vampire-dial\\vampire_dial.py
Outputs (millimetres) go to models\\vampire-dial\\out\\
    parts/<object>_<n>_<colour>.stl   parts; load as ONE object (slice_bambu.py --assemble)
    parts/slice_args.txt              the matching slice_bambu.py arguments
    dial_preview.png                  assembled top view at several settings + the window close up
"""
import importlib.util
from pathlib import Path

import cv2
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from PIL import Image
from scipy import ndimage
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
PARTS = OUT / "parts"

# The art pipeline (quantize, clean, trace, extrude) is shared with the plain token.
_spec = importlib.util.spec_from_file_location(
    "vampire_token", HERE.parent / "vampire-token" / "vampire_token.py")
vt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vt)
BLACK, RED, TAN, CREAM = vt.BLACK, vt.RED, vt.TAN, vt.CREAM

# ---- Parameters (mm) -------------------------------------------------------
CARD_W, ART_H = vt.CARD_W, vt.CARD_H     # 63 x 88 art
EXTRA_H = 4.0                   # black border added below the art to make room for the wheel
INSERT_AT = 87.0                # ... inserted at this depth from the art's top (inside the bottom border)
CARD_H = ART_H + EXTRA_H        # 92.0

# Art simplification for the front. The v3 token kept every stroke >= 0.25 mm and speck >= 0.04 mm^2;
# Arachne prints the 0.25-0.4 mm ones as broken single beads and the specks as stray dots, so the
# print looked fragmented. Here every colour is opened to a full bead and small islands go, with
# gentler settings where fine detail is the point (the face), and a light clean + thickening for
# the thin frame lines, title and symbol (opening would erase them; thickening keeps them whole).
ART = dict(sigma=0.12, stroke=0.50, area=1.0)        # illustration: poster-like, no specks/slivers
DETAIL = dict(sigma=0.10, stroke=0.45, area=0.4)     # the face: keeps eyes, nose and mouth
FRAME_MIN_FEATURE = 0.15                             # frames/title: v3-style light clean ...
# zones in art mm from the art's top-left: (x0, y0, x1, y1), simplification, colours to thicken and
# by how much per side. The title's cream letters are 1 mm-deep slots in the black bar: under ~0.6 mm
# wide their floor barely shows (seen on the v3 print), so they grow more.
ZONES = [
    ((26.5, 26.0, 37.0, 36.5), "detail", (), 0),               # face
    ((1.5, 1.8, 61.5, 9.4), "frame", (CREAM, TAN), 0.20),      # title bar: cream letters, gold lines
    ((2.4, 74.2, 60.6, 80.8), "frame", (TAN,), 0.10),          # type-line box border
    ((53.3, 75.4, 57.6, 79.8), "frame", (BLACK,), 0.10),       # set symbol
    ((48.6, 80.5, 59.8, 86.3), "frame", (TAN,), 0.10),         # P/T box border (window cuts the inside)
]
FINAL_MIN_AREA = 0.25           # last pass over the composite: islands left at zone seams

# Type line: the art's lettering is a serif at 2.1 mm cap height with 0.3 mm crossbars - below what
# a 0.4 nozzle can print (Arachne drops the thin branches). It is erased and re-set as vector text in
# a condensed sans whose every stroke and gap survives a 0.4 mm nozzle (searched: strokes >= 0.42,
# counters/gaps >= 0.3 mm), at 2.8 mm cap height.
TYPE_TEXT = "Token Creature \u2014 Vampire"
TYPE_ERASE = (5.9, 75.42, 50.4, 79.82)     # art mm (x0, y0, x1, y1): old lettering -> cream
TYPE_AREA = (6.2, 75.30, 50.2, 79.94)      # new text: left edge, interior top, right limit, interior bottom
TYPE_FONT = (r"C:\Windows\Fonts\bahnschrift.ttf", {"wght": 600, "wdth": 75})  # Bahnschrift SemiBold Condensed
TYPE_BOLDEN = 0.04              # per side
TYPE_TRACK = 0.45               # extra letter spacing (mm)
TYPE_MAX_H = 3.6                # cap top to descender

# Z bands (shared by every part, so each layer is one filament). Same as vampire-token "relief".
BANDS = [(0.0, 1.0, CREAM), (1.0, 1.2, TAN), (1.2, 1.6, RED), (1.6, 99.0, BLACK)]
FRONT_T = 2.0

# Window: centred on the art's P/T box (measured: 9.8 x 4.5 mm cream box, centre 54.24, 4.56 from
# the art's bottom-left), shifted up by the added border.
PT_BOX = (54.24, 4.56 + EXTRA_H)
WIN_W, WIN_H, WIN_R = 7.4, 3.8, 0.8
TEXT_H = 3.0                    # "N/N" bounding-box height (the art's own 1/1 is 2.6 mm)
DIGIT_BOLDEN = 0.05             # per side: plain DejaVu Bold has ~0.4 mm strokes (29% of the ink under a bead)
FONT = FontProperties(family="DejaVu Sans", weight="bold")
VALUES = range(1, 10)
STEP = 360 / len(VALUES)        # 40 degrees per value

# Wheel. Its centre sits DIGIT_R from the window, in direction WIN_ANGLE+180. Turning the wheel
# counter-clockwise (pushing the rim UP at the card's right edge) counts up.
WIN_ANGLE = -60.0               # direction wheel centre -> window
DIGIT_R = 10.75                 # radius of the digit ring (smallest that hides the neighbours)
CHANNEL_MARGIN = 0.4            # recessed channel extends this far past the window's footprint
RIM = 0.8                       # raised rim between the channel and the scallop valleys
SCALLOP_DEPTH, SCALLOP_R = 1.2, 5.0   # 9 thumb scallops = 9 detent valleys
WHEEL_FLOOR = 1.0               # channel floor (top of the cream band)
WHEEL_T = 1.8                   # raised rim/hub/digits: tan 1.0-1.2, red 1.2-1.6, black cap 1.6-1.8
PIN_D, PIN_CLR = 5.0, 0.25      # axle pin; radial clearance in the wheel's hole
WHEEL_CLR = 0.4                 # radial clearance wheel -> cavity wall
AX_CLR = 0.4                    # axial play: cavity height = WHEEL_T + AX_CLR
WALL = 0.9                      # minimum spacer wall to the card edge

# Back
BASE_T = 0.6                    # back plate under the wheel
CAVITY = WHEEL_T + AX_CLR       # 2.2
BACK_T = BASE_T + CAVITY        # 2.8: the front sits on this
PEG_D, PEG_H = 2.0, 0.4         # alignment pegs on the spacer (and the pin) go into front sockets
SOCKET_D_CLR = 0.15             # per side
SOCKET_DEPTH = 0.6
PEGS = [(5.0, 5.0), (5.0, CARD_H - 5.0), (CARD_W - 5.0, CARD_H - 5.0), (24.0, 4.0)]

# Detent: a cantilever spring in the spacer; its nub sits in a scallop valley at DETENT_ANGLE.
DETENT_ANGLE = 180.0            # left side of the wheel; the arm runs up from there
ARM_L, ARM_T = 14.0, 1.0        # free length, width (in-plane); strain ~1% at full deflection
ARM_TOP_CLR = 0.2               # below the front
NUB_R, PRELOAD = 1.2, 0.2       # nub radius; interference in a valley so it seats firmly
ARM_GAP = 0.4                   # clearance around the arm
SWING = SCALLOP_DEPTH + PRELOAD + 0.4   # room for the tip to deflect outward

PLATE_GAP = 8.0                 # spacing of the three objects on the bed
# ---------------------------------------------------------------------------

C = np.array(PT_BOX) - DIGIT_R * np.array([np.cos(np.radians(WIN_ANGLE)), np.sin(np.radians(WIN_ANGLE))])


def rounded_box(cx, cy, w, h, r):
    return box(cx - w / 2 + r, cy - h / 2 + r, cx + w / 2 - r, cy + h / 2 - r).buffer(r, quad_segs=8)


def disk(c, r, n=128):
    return Point(*c).buffer(r, quad_segs=n)


def glyphs(s, prop):
    """Outline of a string (1 unit = 1 em) with the nonzero fill rule: contours wound like the
    largest one are ink, the others are counters. (Even-odd would punch holes where a variable
    font's contours overlap.)"""
    rings = [r for r in TextPath((0, 0), s, size=1.0, prop=prop).to_polygons(closed_only=True) if len(r) >= 3]
    if not rings:
        return Polygon()

    def signed(r):
        x, y = r[:, 0], r[:, 1]
        return 0.5 * (x * np.roll(y, -1) - np.roll(x, -1) * y).sum()
    ref = np.sign(signed(max(rings, key=lambda r: abs(signed(r)))))
    ink = unary_union([Polygon(r).buffer(0) for r in rings if np.sign(signed(r)) == ref])
    holes = unary_union([Polygon(r).buffer(0) for r in rings if np.sign(signed(r)) != ref])
    return ink.difference(holes)


def text_geom(s, centre, height):
    """Text outline as shapely geometry, bbox centred on centre with the given height."""
    g = glyphs(s, FONT)
    minx, miny, maxx, maxy = g.bounds
    k = (height - 2 * DIGIT_BOLDEN) / (maxy - miny)
    g = affinity.scale(g, k, k, origin=(0, 0)).buffer(DIGIT_BOLDEN, join_style="round")
    minx, miny, maxx, maxy = g.bounds
    return affinity.translate(g, centre[0] - (minx + maxx) / 2, centre[1] - (miny + maxy) / 2)


def colour_at(z):
    return next(s for z0, z1, s in BANDS if z0 <= z + 1e-9 < z1)


def slabs(prisms):
    """[(z0, z1, geom)] -> [(z0, z1, geom, slot)]: split at every band boundary so each slab is one
    colour, and merge neighbours that have the same colour and outline."""
    top = max(p[1] for p in prisms)
    zs = sorted({round(z, 4) for p in prisms for z in p[:2]} | {b[0] for b in BANDS if 0 < b[0] < top})
    out = []
    for z0, z1 in zip(zs, zs[1:]):
        gs = [g for a, b, g in prisms if a <= z0 + 1e-9 and b >= z1 - 1e-9]
        if not gs:
            continue
        g = unary_union(gs)
        slot = colour_at(z0)
        if out and out[-1][3] == slot and abs(out[-1][1] - z0) < 1e-9 \
                and out[-1][2].symmetric_difference(g).area < 1e-6:
            out[-1][1] = z1
        else:
            out.append([z0, z1, g, slot])
    return out


# ---- geometry --------------------------------------------------------------

def window():
    return rounded_box(*PT_BOX, WIN_W, WIN_H, WIN_R)


def wheel_geometry():
    win = window()
    pts = np.array(win.exterior.coords)
    r_out = np.hypot(*(pts - C).T).max() + CHANNEL_MARGIN
    r_in = Point(*C).distance(win) - CHANNEL_MARGIN
    r_valley = r_out + RIM
    R = r_valley + SCALLOP_DEPTH
    channel = disk(C, r_out).difference(disk(C, r_in))
    scallops = unary_union([
        disk(C + (R + SCALLOP_R - SCALLOP_DEPTH) * np.array([np.cos(a), np.sin(a)]), SCALLOP_R, 32)
        for a in np.radians(DETENT_ANGLE + STEP * np.arange(len(VALUES)))])
    hole = disk(C, PIN_D / 2 + PIN_CLR, 32)
    disc = disk(C, R, 256).difference(scallops).difference(hole)
    # value v is laid out upright at the window, then turned back (v-1) steps: turning the wheel
    # (v-1) steps counter-clockwise brings it into the window.
    groups = [affinity.rotate(text_geom(f"{v}/{v}", PT_BOX, TEXT_H), -STEP * (v - 1), origin=tuple(C))
              for v in VALUES]
    for g in groups:
        assert channel.contains(g), "digits must sit inside the channel"
    # neighbours must stay out of the window
    for s in (-STEP, STEP):
        nb = affinity.rotate(groups[0], s, origin=tuple(C))
        assert not nb.intersects(win.buffer(0.3)), "neighbouring value would show in the window"
    raised = disc.difference(channel).union(unary_union(groups))
    return dict(R=R, r_in=r_in, r_out=r_out, r_valley=r_valley, disc=disc, raised=raised, groups=groups)


def detent(R, r_valley):
    a = np.radians(DETENT_ANGLE)
    u = np.array([np.cos(a), np.sin(a)])         # radial, outward
    t = np.array([np.sin(a), -np.cos(a)])        # tangent (clockwise): the arm runs this way
    tip = C + (R + ARM_GAP + ARM_T / 2) * u
    root = tip + ARM_L * t
    beam = LineString([tip, root + 1.5 * t]).buffer(ARM_T / 2, cap_style="flat")
    nub = Point(*(C + (r_valley - PRELOAD + NUB_R) * u)).buffer(NUB_R, quad_segs=16)
    tip_block = LineString([tip, tip + 2 * NUB_R * t]).buffer(ARM_T / 2, cap_style="flat")
    arm = unary_union([beam, nub.union(tip_block).convex_hull])
    # pocket: the arm at rest and swung out by SWING at the tip, plus clearance
    rest = LineString([tip, root]).buffer(ARM_T / 2, cap_style="flat").union(nub.union(tip_block).convex_hull)
    best = None
    for sgn in (1, -1):
        sw = affinity.rotate(rest, sgn * np.degrees(np.arctan(SWING / ARM_L)), origin=tuple(root))
        d = Point(*C).distance(sw.centroid)
        if best is None or d > best[0]:
            best = (d, sw)
    pocket = rest.union(best[1]).convex_hull.buffer(ARM_GAP, join_style="mitre")
    return arm, pocket


def _disk_px(d):
    r = max(1, int(round(d / 2 / vt.PX)))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


def drop_islands(labels, area):
    """Every connected patch (any colour) smaller than area mm^2 takes its surroundings' colour."""
    for _ in range(2):
        keep = np.ones(labels.shape, bool)
        for k in range(len(vt.PALETTE)):
            cc, num = ndimage.label(labels == k)
            if num:
                small = np.bincount(cc.ravel()) * vt.PX ** 2 < area
                small[0] = False
                keep &= ~small[cc]
        labels = vt.refill(labels, keep)
    return labels


def simplify(labels, sigma, stroke, area):
    """Poster-style clean-up: majority blur, then every colour opened to `stroke` mm (anything
    thinner would print as a broken single bead) and islands under `area` mm^2 removed."""
    n = len(vt.PALETTE)
    prob = np.stack([ndimage.gaussian_filter((labels == k).astype(np.float32), sigma / vt.PX) for k in range(n)])
    labels = prob.argmax(0)
    disk_ = _disk_px(stroke)
    for _ in range(2):  # refilling can leave new slivers, so do it twice
        keep = np.zeros(labels.shape, bool)
        for k in range(n):
            keep |= cv2.morphologyEx((labels == k).astype(np.uint8), cv2.MORPH_OPEN, disk_).astype(bool)
        labels = vt.refill(labels, keep)
        labels = drop_islands(labels, area)
    return labels


def thicken(labels, colours, d):
    """Grow the given colours by d mm per side (into whatever surrounds them), so thin lines print
    as solid strokes instead of being dropped or broken up."""
    fg = np.isin(labels, colours)
    grown = cv2.dilate(fg.astype(np.uint8), _disk_px(2 * d)).astype(bool)
    return np.where(grown & ~fg, vt.refill(labels, fg), labels)


def art_labels():
    """The art quantized to the 4 filaments and simplified zone by zone (88 mm tall, image rows)."""
    w_px, h_px = int(round(CARD_W / vt.PX)), int(round(ART_H / vt.PX))
    img = Image.open(vt.SRC).convert("RGB").resize((w_px, h_px), Image.LANCZOS)
    raw = vt.quantize(np.asarray(img).astype(float))
    x0, y0, x1, y1 = (int(round(v / vt.PX)) for v in TYPE_ERASE)
    raw[y0:y1, x0:x1] = CREAM                      # old type-line lettering; re-set as vector text
    labels = simplify(raw, **ART)
    detail = simplify(raw, **DETAIL)
    light = vt.clean(raw, FRAME_MIN_FEATURE)
    for (zx0, zy0, zx1, zy1), kind, grow, amount in ZONES:
        sl = (slice(int(round(zy0 / vt.PX)), int(round(zy1 / vt.PX))),
              slice(int(round(zx0 / vt.PX)), int(round(zx1 / vt.PX))))
        if kind == "detail":
            labels[sl] = detail[sl]
        else:
            labels[sl] = thicken(light, list(grow), amount)[sl] if grow else light[sl]
    return drop_islands(labels, FINAL_MIN_AREA)


def type_font():
    """Bahnschrift is a variable font; matplotlib can't pick its axes, so cut a static instance."""
    import tempfile
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    src, axes = TYPE_FONT
    if not Path(src).exists():
        print(f"  warning: {src} not found, type line falls back to DejaVu Sans Bold")
        return FontProperties(family="DejaVu Sans", weight="bold")
    dst = Path(tempfile.gettempdir()) / f"vampire_dial_{Path(src).stem}_{axes['wght']}_{axes['wdth']}.ttf"
    if not dst.exists():
        instantiateVariableFont(TTFont(src), axes).save(dst)
    return FontProperties(fname=str(dst))


def type_line():
    """The type line as vector text, letter by letter (kerned positions + TYPE_TRACK), emboldened,
    left-aligned in the type box and centred vertically. Card frame (y up)."""
    from matplotlib.textpath import text_to_path
    fp = type_font()
    size = fp.get_size_in_points()

    def width(s):  # advance width in em, including trailing spaces
        return (text_to_path.get_text_width_height_descent(s + "|", fp, ismath=False)[0]
                - text_to_path.get_text_width_height_descent("|", fp, ismath=False)[0]) / size

    def layout(k):
        parts = [affinity.translate(affinity.scale(glyphs(c, fp), k, k, origin=(0, 0)),
                                    width(TYPE_TEXT[:i]) * k + TYPE_TRACK * i, 0)
                 for i, c in enumerate(TYPE_TEXT) if c != " "]
        return unary_union(parts).buffer(TYPE_BOLDEN, join_style="round")

    x0, top, x1, bottom = TYPE_AREA
    k = 1.0
    for _ in range(5):  # fit the scale to the width and height limits
        g = layout(k)
        minx, miny, maxx, maxy = g.bounds
        k *= min((x1 - x0) / (maxx - minx), TYPE_MAX_H / (maxy - miny))
    g = layout(k)
    minx, miny, maxx, maxy = g.bounds
    cy = CARD_H - (top + bottom) / 2
    cap = glyphs("T", fp).bounds[3] * k
    print(f"type line: {fp.get_name()}, cap height {cap:.2f} mm, {maxx - minx:.1f} mm long")
    return affinity.translate(g, x0 - minx, cy - (miny + maxy) / 2)


def front_regions(card):
    labels = art_labels()
    ins, n = int(round(INSERT_AT / vt.PX)), int(round(EXTRA_H / vt.PX))
    interior = labels[ins, int(4 / vt.PX):-int(4 / vt.PX)]
    assert (interior == BLACK).mean() > 0.97, "insert row should lie in the black bottom border"
    labels = np.concatenate([labels[:ins], np.full((n, labels.shape[1]), BLACK, labels.dtype), labels[ins:]])
    regions, taken = {}, Polygon()
    for k in (CREAM, TAN, RED):  # light colours first; black gets the rest
        g = vt.trace(labels == k)
        g = affinity.translate(affinity.scale(g, 1, -1, origin=(0, 0)), 0, CARD_H)  # image -> y up
        g = g.intersection(card).difference(taken).buffer(0)
        regions[k] = g
        taken = unary_union([taken, g])
    regions[BLACK] = card.difference(taken).buffer(0)
    text = type_line()
    for k in (CREAM, TAN, RED):
        regions[k] = regions[k].difference(text)
    regions[BLACK] = regions[BLACK].union(text).intersection(card)
    # black = card minus the rest also collects hairline seams between the other colours; drop them
    regions[BLACK] = unary_union([p for p in vt.polys_of(regions[BLACK]) if p.area >= 0.02])
    return regions


def thin_report(regions):
    """Area (mm^2) of each colour's visible top that is thinner than one 0.42 mm bead, i.e. what a
    0.4 mm nozzle can't reproduce. Includes the rounding of sharp corners, so it is never 0."""
    return {vt.PALETTE[k][0]: g.difference(g.buffer(-0.21).buffer(0.21)).area for k, g in regions.items()}


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
            else:  # merged regions: a 10 micron close seals the hairline seams between them
                g = unary_union([regions[c] for c in cols]).buffer(0.01, join_style="mitre") \
                    .buffer(-0.01, join_style="mitre").intersection(card)
            g = g.difference(win)
            if z0 == 0.0:  # sockets in the underside of the base
                out.append((0.0, SOCKET_DEPTH, g.difference(sockets), slot))
                out.append((SOCKET_DEPTH, z1, g, slot))
            else:
                out.append((z0, z1, g, slot))
    return out


# ---- preview ---------------------------------------------------------------

def draw(ax, g, colour, **kw):
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath
    for p in vt.polys_of(g):
        paths = [MPath(np.asarray(r.coords)) for r in [p.exterior, *p.interiors]]
        ax.add_patch(PathPatch(MPath.make_compound_path(*paths), facecolor=colour, edgecolor="none", **kw))


def preview(regions, card, wh, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    hexes = [h for _, h in vt.PALETTE]
    shows = [1, 4, 9]
    fig, axes = plt.subplots(1, len(shows) + 1, figsize=(4.2 * (len(shows) + 1), 6.2),
                             gridspec_kw=dict(width_ratios=[1] * len(shows) + [1.1]))
    win = window()
    for ax, v in zip(list(axes[:len(shows)]) + [axes[-1]], shows + [4]):
        rot = STEP * (v - 1)
        draw(ax, affinity.rotate(wh["disc"], rot, origin=tuple(C)), hexes[CREAM])
        draw(ax, affinity.rotate(wh["raised"], rot, origin=tuple(C)), hexes[BLACK])
        front = card.difference(win)
        draw(ax, front, hexes[CREAM])
        for k in (TAN, RED, BLACK):
            draw(ax, regions[k].difference(win), hexes[k])
        ax.set_aspect("equal")
        ax.set_facecolor("#9aa0a6")
        ax.set_xticks([]); ax.set_yticks([])
        if ax is axes[-1]:
            ax.set_xlim(PT_BOX[0] - 9, CARD_W + 4); ax.set_ylim(-1, PT_BOX[1] + 12)
            ax.set_title(f"window close-up (showing {v}/{v})")
        else:
            ax.set_xlim(-2, CARD_W + 5); ax.set_ylim(-2, CARD_H + 2)
            ax.set_title(f"dial at {v}/{v}")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close(fig)
    print(f"preview -> {path}")


# ---- build -----------------------------------------------------------------

def main():
    PARTS.mkdir(parents=True, exist_ok=True)
    for f in PARTS.glob("*.stl"):
        f.unlink()
    card = vt.rounded_rect(CARD_W, CARD_H, vt.CORNER_R)
    wh = wheel_geometry()
    R = wh["R"]
    arm, pocket = detent(R, wh["r_valley"])
    cavity = disk(C, R + WHEEL_CLR, 256).union(pocket)
    spacer = card.difference(cavity)
    base = card.difference(pocket)
    peg_disks = unary_union([disk(p, PEG_D / 2, 24) for p in PEGS])
    sockets = unary_union([disk(p, PEG_D / 2 + SOCKET_D_CLR, 24) for p in PEGS] +
                          [disk(C, PIN_D / 2 + SOCKET_D_CLR, 32)])

    # sanity checks on the layout
    protrude = C[0] + R - CARD_W
    bottom_wall = C[1] - R - WHEEL_CLR
    assert bottom_wall >= WALL - 1e-6, f"wheel cavity is {bottom_wall:.2f} mm from the bottom edge"
    assert 1.5 <= protrude <= 3.5, f"rim protrudes {protrude:.2f} mm"
    assert card.buffer(-WALL).contains(pocket), "detent pocket too close to the card edge"
    for p in PEGS:
        assert spacer.buffer(-0.8).contains(disk(p, PEG_D / 2, 24)), f"peg {p} not on solid spacer"
    assert arm.intersection(spacer).area > 0.5, "detent arm root must be anchored in the spacer"
    assert arm.intersection(disk(C, wh["r_valley"] - PRELOAD - 0.01)).is_empty, "nub preload too deep"

    print(f"card: {CARD_W:.1f} x {CARD_H:.1f} mm, {BACK_T + FRONT_T:.1f} mm thick assembled "
          f"({CARD_W / 25.4:.3f} x {CARD_H / 25.4:.3f} x {(BACK_T + FRONT_T) / 25.4:.3f} in)")
    print(f"wheel: centre ({C[0]:.2f}, {C[1]:.2f}), R {R:.2f} (valleys {wh['r_valley']:.2f}), "
          f"channel {wh['r_in']:.2f}-{wh['r_out']:.2f}, digits at r {DIGIT_R}, "
          f"rim protrudes {protrude:.2f} mm past the right edge (valleys {protrude - SCALLOP_DEPTH:.2f}), "
          f"bottom wall {bottom_wall:.2f} mm")

    regions = front_regions(card)
    print("front colours: " + ", ".join(f"{vt.PALETTE[k][0]} {100 * regions[k].area / card.area:.1f}%"
                                        for k in range(4)))
    print("front islands per colour: " + ", ".join(
        f"{vt.PALETTE[k][0]} {len(vt.polys_of(regions[k]))}" for k in range(4)))
    print("thinner than a bead (mm^2, mostly corner rounding): " + ", ".join(
        f"{n} {a:.2f}" for n, a in thin_report(regions).items()))

    arm_top = BACK_T - ARM_TOP_CLR
    back_prisms = [(0.0, BASE_T, base), (0.0, arm_top, arm), (BASE_T, BACK_T, spacer),
                   (BASE_T, BACK_T + PEG_H, disk(C, PIN_D / 2, 32)), (BACK_T, BACK_T + PEG_H, peg_disks)]
    wheel_prisms = [(0.0, WHEEL_FLOOR, wh["disc"]), (WHEEL_FLOOR, WHEEL_T, wh["raised"])]
    wheel_off = (2 * (CARD_W + PLATE_GAP) + R - C[0], R - C[1] + 2)
    objects = [
        ("front", (0.0, 0.0), [list(p) for p in front_prisms(regions, card, sockets)]),
        ("back", (CARD_W + PLATE_GAP, 0.0), slabs(back_prisms)),
        ("wheel", wheel_off, slabs(wheel_prisms)),
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
        f"--colors \"{','.join(h for _, h in vt.PALETTE)}\" --set wall_generator=arachne\n")
    print("model grams per slot (PLA 1.24 g/cm^3, solid, before purge): " +
          ", ".join(f"{i + 1} {vt.PALETTE[i][0]} {g:.2f}" for i, g in enumerate(grams)))
    preview(regions, card, wh, OUT / "dial_preview.png")
    parts_preview(card, base, spacer, arm, pocket, peg_disks, wh, OUT / "parts_preview.png")


def parts_preview(card, base, spacer, arm, pocket, pegs, wh, path):
    """Top views of the back (with the wheel's outline) and the wheel, plus the detent close up."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(15, 6.5))
    for ax in axes:
        draw(ax, card.difference(base), "#ffffff")
        draw(ax, base, "#e8d2a8")                   # base plate (0-0.6)
        draw(ax, spacer, "#7a6a58")                 # spacer frame (0.6-2.8)
        draw(ax, arm, "#b03a2e")                    # detent arm (free over the slot)
        draw(ax, disk(C, PIN_D / 2), "#3a2d25")
        draw(ax, pegs, "#3a2d25")
        ax.plot(*np.asarray(wh["disc"].exterior.coords).T, color="#1f5fa8", lw=0.8)
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    axes[0].set_xlim(-2, CARD_W + 5); axes[0].set_ylim(-2, CARD_H + 2)
    axes[0].set_title("back: base (beige), spacer (brown), detent arm (red); wheel outline blue")
    a = np.radians(DETENT_ANGLE)
    d = C + wh["R"] * np.array([np.cos(a), np.sin(a)])
    axes[1].set_xlim(d[0] - 6, d[0] + 6); axes[1].set_ylim(d[1] - 4, d[1] + ARM_L + 3)
    axes[1].set_title("detent: nub seated in a scallop valley")
    ax = axes[2]
    ax.cla()
    draw(ax, wh["disc"], "#e8d2a8")
    draw(ax, wh["raised"], "#241B16")
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlim(C[0] - wh["R"] - 1, C[0] + wh["R"] + 1); ax.set_ylim(C[1] - wh["R"] - 1, C[1] + wh["R"] + 1)
    ax.set_title("wheel (top): black raised rim, hub and digits; cream channel")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close(fig)
    print(f"preview -> {path}")


if __name__ == "__main__":
    main()
