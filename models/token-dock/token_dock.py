#!/usr/bin/env python3
"""
Token dock: a reusable 1/1 ... 9/9 counter base that plain token cards dock onto.

The counter lives in the BASE, so one base serves any number of cards: print a few bases and
swap cards between them. A card is a single flat 63 x 88 part with no mechanism.

Base (4 parts, 2 colours):
  back    plate + spacer with the wheel cavity, axle pin, detent arm, glue pegs and two magnet
          pockets (open at the back, closed toward the card)
  wheel   the vampire-counter number wheel, face-down; its rim pokes out of the BOTTOM edge
  cover   the shelf: a flat plate over the wheel that the card lies on
  block   the visible stat block, face-down: black frame, bats, a bevelled window on the wheel
Card (1 part, 4 colours): face-down flat inlay; a bevelled toe along its bottom edge and two
  magnet bosses on its back.

The base is exactly as wide as the card: docked, only the stat block shows, below the card.

Docking: tilt the card, hook its toe under the block's bevelled top edge and lay it down. The
bosses drop into the shelf's holes (they take every sideways and upward load) and the magnets hold
it down. Lift the card's top edge to release.

Reuses models/vampire-arcana (the scene) and, through it, models/vampire-counter (palette, frame,
title and the whole dial: wheel, detent, window). The dial is the one-piece cards' own, so the same
wheel fits both; only the window's bevel is deeper here, because the block is thicker than a card front.

Spec: see README.md in this folder.

Run (from the repo root):
    .venv\\Scripts\\python.exe models\\token-dock\\token_dock.py
Outputs (millimetres) go to models\\token-dock\\out\\
    base/<part>_<n>_<colour>.stl, base/slice_args.txt            the base plate (one object)
    card_arcana/card_<n>_<colour>.stl, card_arcana/slice_args.txt  one token card
    dock_preview.png      docked at 1/1, 5/5, 9/9, a nozzle simulation, the bare base, the back
    parts_preview.png     back, cover, wheel, card back
    section_preview.png   side sections through the window and through a magnet
"""
import importlib.util
import math
from pathlib import Path

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


va = _load("vampire_arcana", HERE.parent / "vampire-arcana" / "vampire_arcana.py")   # the card's scene
vc = va.vc                       # vampire-counter: palette, frame, title, wheel, detent
vt, vd = vc.vt, vc.vd            # extrusion; glyphs and drawing

# ---- Parameters (mm) -------------------------------------------------------
PALETTE = vc.PALETTE             # AMS slots 1-4: ink, blood, gold, paper
INK, BLOOD, GOLD, PAPER = range(4)
LAYER = 0.2
INLAY = vc.INLAY                 # 0.4: two layers of colour on every face that prints on the plate
EDGE = vc.EDGE                   # 1.8 black frame edge

# The card: a standard token card, one flat part.
CARD_W, CARD_H, CORNER_R = vc.CARD_W, vc.CARD_H, vc.CORNER_R     # 63 x 88, 3 mm corners
CARD_T = 2.0
CARD_NAME = "arcana"

# The base: exactly as wide as the card, so nothing shows either side of a docked card.
BASE_W = CARD_W
BACK_T = vc.BACK_T               # 2.8 = 0.6 plate + 2.2 cavity (1.8 wheel + 0.4 play)
COVER_T = 1.2                    # the shelf plate over the wheel
SHELF_Z = BACK_T + COVER_T       # 4.0: the card's back rests here
FACE_Z = SHELF_Z + CARD_T        # 6.0: card face and block face are flush
BLOCK_T = FACE_Z - BACK_T        # 3.2
TOP_WALL = 1.6                   # spacer above the detent pocket

# The dial is vampire-counter's, unchanged: wheel centred, window straight below the axle, rim at the
# bottom edge (push it RIGHT to count up), detent at 110 deg, reeded rim. See that module's parameters.
PROTRUDE = vc.PROTRUDE           # rim past the base's bottom edge

# Window: straight for the last 0.8 mm above the wheel, then bevelled out to the face, so the digits
# stay whole when read at an angle (the owner looks up from below the card: the bottom wall matters).
BEVEL_X, BEVEL_Y = 1.0, 2.0
BEVEL_STEPS = 10                 # one per layer
MOUTH_R = 2.2
WIN_RULE = vc.WIN_RULE           # 0.7 black rule round the window's mouth
FOOT_PAD = 1.1                   # white between that rule and the block's top edge
FOOTER_BAT = vc.FOOTER_BAT       # the card's footer bats (wingspan)
FLOURISH = (13.0, 3.6, 0.8)      # the block's ornament either side of the window: rule length, lozenge height, rule width

# Cleat: the block's top edge leans over the card's bottom edge at 45 deg (one layer per step); the
# card's matching toe hooks under it. Both print face-down without support.
CLEAT = CARD_T - INLAY           # 1.6: from under the inlay down to the shelf
TOE = 1.4                        # the toe stops one step short of a knife edge
CLEAT_GAP = 0.2                  # along y (0.14 square to the 45 deg faces)
TOE_INSET = CORNER_R             # the toe runs between the card's corner radii
COVER_LAP = 2.2                  # the shelf reaches this far under the block's top edge (under the toe)
PART_GAP = 0.1                   # between the shelf plate and the block

# Magnets: 2 in the base, 2 per card. Base pockets open at the BACK and keep a roof toward the card,
# so removing a card pulls the magnet against plastic, not glue.
MAG_D, MAG_T = 6.0, 2.0
MAG_FIT = 0.05                   # per side: a press fit once the hole prints a little small
MAG_ROOF = 0.4
MAG_INSET = (8.5, 7.5)          # magnet centre from the base's side and top edges
BOSS_D = 9.6                     # boss on the card's back: holds the magnet and locates the card
BOSS_H = 1.0                     # 0.2 short of the shelf thickness, so the card rests on the shelf
BOSS_CLR = 0.2                   # per side in the shelf's hole

PEG_D, PEG_H = vc.PEG_D, vc.PEG_H            # Ø2 x 0.4 glue pegs on the spacer
SOCKET_CLR, SOCKET_DEPTH = vc.SOCKET_D_CLR, vc.SOCKET_DEPTH
PIN_D = vc.PIN_D

PLATE_GAP = 8.0
SLICER_SET = vc.SLICER_SET       # Arachne tuned for thin strokes + a slow first layer (the art IS layer 1)
# ---------------------------------------------------------------------------


# ---- the dial: vampire-counter's, with this block's deeper bevel -----------------
vc.WIN_BEVEL, vc.MOUTH_R = (BEVEL_X, BEVEL_Y), MOUTH_R           # vc.opening() reads these when called
C, R, WIN_C, WIN_WH = vc.C, vc.R_WHEEL, vc.WIN_C, vc.WIN_WH
STEP = vc.STEP
opening = vc.opening             # f = 0 at the wheel (the window) ... 1 at the face (the bevel's mouth)

MOUTH_TOP = WIN_C[1] + WIN_WH[1] / 2 + BEVEL_Y
BLOCK_H = round(MOUTH_TOP + WIN_RULE + FOOT_PAD + EDGE, 1)       # the visible stat block's height
CARD_X0, CARD_Y0 = 0.0, BLOCK_H + CLEAT_GAP                      # the docked card's bottom-left corner


def disk(c, r, n=48):
    return vc.disk(c, r, n)


def mirror(g, x):
    return affinity.scale(g, -1, 1, origin=(x, 0))


# ---- the design, in the assembly frame ----------------------------------------
# x, y: front view, base bottom-left at the origin. z: 0 at the base's back, FACE_Z at the faces.

def design():
    wh = vc.wheel_geometry()
    arm, pocket, nub = vc.detent(R)
    base_h = math.ceil((pocket.bounds[3] + TOP_WALL) * 10) / 10
    outline = vt.rounded_rect(BASE_W, base_h, CORNER_R)
    window, mouth = opening(0.0), opening(1.0)

    mags = [(MAG_INSET[0], base_h - MAG_INSET[1]), (BASE_W - MAG_INSET[0], base_h - MAG_INSET[1])]
    mag_holes = unary_union([disk(p, MAG_D / 2 + MAG_FIT) for p in mags])
    boss_holes = unary_union([disk(p, BOSS_D / 2 + BOSS_CLR) for p in mags])
    cavity = disk(C, R + vc.WHEEL_CLR, 512).union(pocket)
    spacer = outline.difference(cavity)
    plate = outline.difference(pocket)

    cover = outline.intersection(box(0, BLOCK_H - COVER_LAP, BASE_W, base_h))
    block = outline.intersection(box(0, 0, BASE_W, BLOCK_H))
    block_low = outline.intersection(box(0, 0, BASE_W, BLOCK_H - COVER_LAP - PART_GAP))   # below shelf level

    pegs_cover = [(6.0, base_h - 16.5), (BASE_W - 6.0, base_h - 16.5), (20.0, base_h - 3.0)]
    pegs_block = [(5.0, 4.5), (BASE_W - 5.0, 4.5), (3.6, 11.5), (BASE_W - 3.6, 11.5)]
    pegs = unary_union([disk(p, PEG_D / 2, 24) for p in pegs_cover + pegs_block])
    pin = disk(C, PIN_D / 2, 32)
    sock = lambda pts: unary_union([disk(p, PEG_D / 2 + SOCKET_CLR, 24) for p in pts])
    sockets_cover = sock(pegs_cover).union(disk(C, PIN_D / 2 + SOCKET_CLR, 32))
    sockets_block = sock(pegs_block)

    # ---- fits ----
    side_wall = C[0] - R - vc.WHEEL_CLR
    assert side_wall >= 1.5, f"the wheel cavity leaves only a {side_wall:.2f} mm side wall"
    assert outline.buffer(-0.9).contains(pocket), "detent pocket too close to the base's edge"
    assert arm.intersection(spacer).area > 0.5, "detent arm root must be anchored in the spacer"
    k = vc.PRELOAD * np.cos(np.radians(vc.NOTCH_FLANK))
    assert nub.intersects(wh["disc"]) and not nub.buffer(-k - 0.01).intersects(wh["disc"]), "nub preload is off"
    assert arm.difference(nub.buffer(0.01)).disjoint(wh["disc"]), "only the nub may touch the wheel"
    assert spacer.disjoint(wh["disc"].buffer(vc.WHEEL_CLR - 0.01)), "spacer runs into the wheel"
    for p in pegs_cover:
        assert spacer.buffer(-0.8).contains(disk(p, PEG_D / 2)), f"cover peg {p} not on solid spacer"
        assert cover.difference(boss_holes).buffer(-0.8).contains(disk(p, PEG_D / 2)), f"cover peg {p} off the cover"
    for p in pegs_block:
        assert spacer.buffer(-0.8).contains(disk(p, PEG_D / 2)), f"block peg {p} not on solid spacer"
        assert block_low.difference(mouth).buffer(-0.8).contains(disk(p, PEG_D / 2)), f"block peg {p} off the block"
    for p in mags:
        assert spacer.contains(disk(p, MAG_D / 2 + 1.2)), f"magnet pocket at {p} needs solid spacer around it"
        assert cover.buffer(-1.0).contains(disk(p, BOSS_D / 2 + BOSS_CLR)), f"boss hole at {p} too near the shelf's edge"
    assert cover.contains(pin.buffer(1.5)), "the axle pin must sit under the shelf plate"
    assert block_low.buffer(-1.5).contains(window), "the window needs block all round it"
    assert mouth.bounds[1] >= 3 * vc.BEAD, "under a bead and a half of frame left below the window's mouth"
    assert BLOCK_H - COVER_LAP - PART_GAP - mouth.bounds[3] >= 1.0, "the bevel runs into the cleat"
    assert BLOCK_T - INLAY - BEVEL_STEPS * LAYER >= 0.39, "no straight window left above the wheel"
    assert BOSS_CLR < TOE - CLEAT_GAP, "the bosses must stop the card before its toe can leave the cleat"
    mech = vc.arm_mechanics(R)
    for name, (d, P, e) in mech.items():
        print(f"detent {name:11s}: deflection {d:.2f} mm, nub force {P:.2f} N, peak strain {100 * e:.2f} %")
    assert mech["at the stop"][2] < vc.MAX_STRAIN, "the arm would be over-strained at its stop"

    chord = 2 * math.sqrt(R ** 2 - (R - PROTRUDE) ** 2)
    print(f"base: {BASE_W:.1f} x {base_h:.1f} mm (+ {PROTRUDE:.1f} mm of rim), {FACE_Z:.1f} mm thick at the block, "
          f"{SHELF_Z:.1f} mm at the shelf ({BASE_W / 25.4:.3f} x {base_h / 25.4:.3f} x {FACE_Z / 25.4:.3f} in)")
    print(f"docked: {BASE_W:.1f} x {CARD_Y0 + CARD_H:.1f} mm; the stat block shows {BLOCK_H:.1f} mm below the card, "
          f"the shelf backs the card's lower {base_h - CARD_Y0:.1f} mm")
    print(f"wheel: centre ({C[0]:.2f}, {C[1]:.2f}), R {R:.2f}, digits {vc.DIGIT_H} mm at r {vc.DIGIT_R}, rim band "
          f"{vc.WHEEL_RIM:.2f} mm, side wall {side_wall:.2f} mm, rim exposed over "
          f"{chord:.1f} mm of the bottom edge; window {WIN_WH[0]:.1f} x {WIN_WH[1]:.1f} at ({WIN_C[0]:.2f}, "
          f"{WIN_C[1]:.2f}), mouth {mouth.bounds[2] - mouth.bounds[0]:.1f} x {mouth.bounds[3] - mouth.bounds[1]:.1f}")
    return dict(wh=wh, arm=arm, pocket=pocket, nub=nub, base_h=base_h, outline=outline, window=window, mouth=mouth,
                mags=mags, mag_holes=mag_holes, boss_holes=boss_holes, spacer=spacer, plate=plate,
                cover=cover, block=block, block_low=block_low,
                pegs=pegs, pin=pin, sockets_cover=sockets_cover, sockets_block=sockets_block)


# ---- art ----------------------------------------------------------------------

def clean(cv, shape):
    regions = {k: g.intersection(shape).buffer(0) for k, g in cv.r.items()}
    return {k: vc.tidy(g) for k, g in vc.absorb_islands(vc.fill_slivers(regions)).items()}


def block_regions(d):
    """The stat block's face: the family footer (black edge, white plate) with a flourish either side
    of the bevelled window, whose black rule runs into the bottom edge."""
    cv = vc.Canvas(d["block"])
    plate = vc.rrect((EDGE, EDGE, BASE_W - EDGE, BLOCK_H - EDGE), vc.PLATE_R)
    cv.paint(PAPER, plate)
    cv.paint(INK, d["mouth"].buffer(WIN_RULE, join_style="round"))
    fr = d["mouth"].buffer(WIN_RULE).bounds
    for x in ((EDGE + fr[0]) / 2, (fr[2] + BASE_W - EDGE) / 2):
        cv.paint(INK, flourish((x, BLOCK_H / 2)), plate)
    return clean(cv, d["block"].difference(d["mouth"]))


def flourish(c, w=FLOURISH[0], h=FLOURISH[1], line=FLOURISH[2]):
    """A lozenge on a short rule: the base is shared by every card, so its ornament is not card-specific."""
    x, y = c
    gem = Polygon([(x - h * 0.7, y), (x, y + h / 2), (x + h * 0.7, y), (x, y - h / 2)])
    return unary_union([gem, box(x - w / 2, y - line / 2, x + w / 2, y + line / 2)]).buffer(0.15).buffer(-0.15)


def base_back_regions(d):
    """The base's back, as seen from behind: black edge, a black crescent and bat over the wheel."""
    cv = vc.Canvas(d["outline"])
    cv.paint(PAPER, d["outline"].buffer(-EDGE).buffer(-0.3).buffer(0.3))
    c = (BASE_W / 2, C[1])
    crescent = disk(c, 10.0, 96).difference(disk((c[0] + 4.2, c[1] + 2.0), 8.4, 96)).buffer(0.35).buffer(-0.35)
    cv.paint(INK, crescent)
    cv.paint(INK, vc.bat((c[0] + 3.0, c[1] + 0.8), 9.0, -8.0))
    return clean(cv, d["outline"])


def card_frame(cv):
    """vc.frame without the dial: the footer plate carries a gold crescent between two bats."""
    title_in, art_in, foot_in = (vc.rrect(b, vc.PLATE_R) for b in (vc.TITLE_BOX, vc.ART, vc.FOOTER))
    for g in (title_in, art_in, foot_in):
        cv.paint(PAPER, g)
    cv.paint(INK, vc.title_text())
    fy = (vc.FOOTER[1] + vc.FOOTER[3]) / 2
    c = (vc.CX, fy)
    crescent = disk(c, 5.4, 96).difference(disk((c[0] + 2.3, c[1] + 1.1), 4.5, 96)).buffer(0.3).buffer(-0.3)
    cv.paint(INK, crescent.buffer(0.4, join_style="round"), foot_in)
    cv.paint(GOLD, crescent.buffer(-0.35, join_style="round"), foot_in)
    for x in ((vc.FOOTER[0] + c[0] - 7.0) / 2, (c[0] + 7.0 + vc.FOOTER[2]) / 2):
        cv.paint(INK, vc.bat((x, fy), FOOTER_BAT, 0.0), foot_in)
    return art_in


def card_finish(cv, card):
    return clean(cv, card)


def card_regions(card):
    """The arcana scene in the dial-less frame: arcana's front_regions() calls vc.frame and vc.finish."""
    vc.frame, vc.finish = card_frame, card_finish
    return va.front_regions(card)


# ---- parts as z bands, in the assembly frame ------------------------------------
# A band is (z0, z1, shape, slot). A part printed face-down is flipped at assembly, so it is mirrored
# for printing; a part printed as it sits is not (see CLAUDE.md, "Face-down / multi-part print transforms").

def part(name, bands, face_down, z_ref, axis=None):
    return dict(name=name, bands=[b for b in bands if not b[2].is_empty], face_down=face_down, z_ref=z_ref, axis=axis)


def parts_of(d, block_art, back_art, card_art):
    wh = d["wh"]
    digits = unary_union(wh["groups"])
    mx = BASE_W / 2

    # back: printed as it sits (cavity up). Only its ART is mirrored: it is drawn as seen from behind.
    mag_top = BACK_T - MAG_ROOF
    back = [(0.0, INLAY, mirror(back_art[k], mx).intersection(d["plate"]).difference(d["mag_holes"]), k)
            for k in range(4)] + [
        (INLAY, vc.BASE_T, d["plate"].difference(d["mag_holes"]), PAPER),
        (0.0, BACK_T - vc.ARM_TOP_CLR, d["arm"], PAPER),            # stands free in a slot through the plate
        (vc.BASE_T, mag_top, d["spacer"].difference(d["mag_holes"]), PAPER),
        (mag_top, BACK_T, d["spacer"], PAPER),                       # the roof over the magnet pockets
        (vc.BASE_T, BACK_T + PEG_H, d["pin"], PAPER),
        (BACK_T, BACK_T + PEG_H, d["pegs"], PAPER)]

    # wheel: face-down. At assembly it lies on the plate, digits up.
    wz = vc.BASE_T + vc.WHEEL_T
    wheel = [(wz - INLAY, wz, digits, INK), (wz - INLAY, wz, wh["disc"].difference(digits), PAPER),
             (vc.BASE_T, wz - INLAY, wh["disc"], PAPER)]

    # cover: printed as it sits; sockets for the pegs and pin in its underside.
    shelf = d["cover"].difference(d["boss_holes"])
    cover = [(BACK_T, BACK_T + SOCKET_DEPTH, shelf.difference(d["sockets_cover"]), PAPER),
             (BACK_T + SOCKET_DEPTH, SHELF_Z, shelf, PAPER)]

    # block: face-down, sliced by depth below the face, one slice per layer.
    slices = []
    for i in range(int(round(BLOCK_T / LAYER))):
        d0, d1 = i * LAYER, (i + 1) * LAYER
        j = max(0, i + 1 - int(round(INLAY / LAYER)))               # layers below the inlay
        f = max(0.0, 1.0 - j / BEVEL_STEPS)
        if d1 <= CARD_T + 1e-9:                                     # beside the card: the cleat leans back
            lean = min(CLEAT, j * LAYER)
            g = d["block"].difference(box(0, BLOCK_H - lean, BASE_W, BLOCK_H + 1))
        else:                                                       # beside the shelf plate
            lean, g = -1.0, d["block_low"]
        socketed = d0 >= BLOCK_T - SOCKET_DEPTH - 1e-9
        g = g.difference(opening(f))
        slices.append((d0, d1, (round(f, 4), round(lean, 4), socketed),
                       g.difference(d["sockets_block"]) if socketed else g))
    block = []
    for d0, d1, key, g in vc.merge_slices(slices):
        if d1 <= INLAY + 1e-9:
            block += [(FACE_Z - d1, FACE_Z - d0, block_art[k], k) for k in range(4)]
        else:
            block.append((FACE_Z - d1, FACE_Z - d0, g, PAPER))

    # card: face-down, in its own frame (bottom-left corner at the origin), then moved to its dock.
    card = vt.rounded_rect(CARD_W, CARD_H, CORNER_R)
    mags_c = [(x - CARD_X0, y - CARD_Y0) for x, y in d["mags"]]
    hole = unary_union([disk(p, MAG_D / 2 + MAG_FIT) for p in mags_c])
    boss = unary_union([disk(p, BOSS_D / 2) for p in mags_c])
    assert card.buffer(-1.0).contains(boss), "a magnet boss is off the card"
    skin = CARD_T - (MAG_T - BOSS_H)                                # card left in front of the magnet
    slices = []
    for i in range(int(round(CARD_T / LAYER))):
        d0, d1 = i * LAYER, (i + 1) * LAYER
        j = max(0, i + 1 - int(round(INLAY / LAYER)))
        toe = min(TOE, j * LAYER)
        pocketed = d0 >= skin - 1e-9
        g = card.union(box(TOE_INSET, -toe, CARD_W - TOE_INSET, CORNER_R)) if toe else card
        slices.append((d0, d1, (round(toe, 4), pocketed), g.difference(hole) if pocketed else g))
    cz = lambda depth: FACE_Z - depth
    place = lambda g: affinity.translate(g, CARD_X0, CARD_Y0)
    card_bands = []
    for d0, d1, key, g in vc.merge_slices(slices):
        if d1 <= INLAY + 1e-9:
            card_bands += [(cz(d1), cz(d0), place(card_art[k]), k) for k in range(4)]
        else:
            card_bands.append((cz(d1), cz(d0), place(g), PAPER))
    card_bands.append((SHELF_Z - BOSS_H, SHELF_Z, place(boss.difference(hole)), PAPER))
    print(f"card: {CARD_W:.0f} x {CARD_H:.0f} x {CARD_T:.1f} mm + a {TOE:.1f} mm toe and two Ø{BOSS_D} x {BOSS_H} "
          f"bosses; {skin:.1f} mm of card in front of each magnet")

    return [part("back", back, False, 0.0), part("wheel", wheel, True, wz, C[0]),
            part("cover", cover, False, BACK_T), part("block", block, True, FACE_Z, mx),
            part("card", card_bands, True, FACE_Z, CARD_X0 + CARD_W / 2)]


def to_print(p):
    """Assembly frame -> as it lies on the plate."""
    if p["face_down"]:
        return [(p["z_ref"] - z1, p["z_ref"] - z0, mirror(g, p["axis"]), s) for z0, z1, g, s in p["bands"]]
    return [(z0 - p["z_ref"], z1 - p["z_ref"], g, s) for z0, z1, g, s in p["bands"]]


def reassemble(p, printed):
    """A printed part put back in the assembly: a face-down part is turned over about its y axis."""
    if p["face_down"]:
        return [(p["z_ref"] - z1, p["z_ref"] - z0, affinity.scale(g, -1, 1, origin=(p["axis"], 0)), s)
                for z0, z1, g, s in printed]
    return [(z0 + p["z_ref"], z1 + p["z_ref"], g, s) for z0, z1, g, s in printed]


def assembly_check(d, parts, printed):
    """Rebuild the token from the parts AS PRINTED and check it: nothing collides, the nub seats in a
    notch, every value is centred in the window, the card's toe is caught under the block, and each
    card magnet sits over a base magnet."""
    asm = {p["name"]: reassemble(p, printed[p["name"]]) for p in parts}
    names = list(asm)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if {a, b} == {"back", "wheel"}:
                continue                                            # the nub preloads the wheel: checked below
            ov = vc.overlap(asm[a], asm[b])
            assert ov < 0.01, f"{a} and {b} collide ({ov:.3f} mm^2)"
    arm = next(g for z0, z1, g, _ in asm["back"] if abs(z1 - (BACK_T - vc.ARM_TOP_CLR)) < 1e-6)
    rest = [(z0, z1, g, s) for z0, z1, g, s in asm["back"] if g is not arm]
    assert vc.overlap(rest, asm["wheel"]) < 0.01, "the wheel collides with the back"
    disc = max((g for _, _, g, _ in asm["wheel"]), key=lambda g: g.area)
    ink = next(g for _, _, g, s in asm["wheel"] if s == INK)
    pc = np.array(d["pin"].centroid.coords[0])
    hc = np.array(Polygon(disc.interiors[0]).centroid.coords[0])
    assert np.allclose(pc, hc, atol=0.01), f"wheel hole at {hc}, pin at {pc}"
    ov = [arm.intersection(affinity.rotate(disc, a, origin=tuple(pc))).area for a in (-0.5, 0.0, 0.5)]
    assert ov[1] > 0 and abs(ov[0] - ov[2]) < 0.02 * max(ov), f"nub not centred in a notch: {ov}"
    # the window as built: the hole in the block's deepest band
    deep = min(asm["block"], key=lambda b: b[0])[2]
    win = max((Polygon(r) for r in deep.interiors), key=lambda g: g.area)
    wc = np.array(win.centroid.coords[0])
    worst = 0.0
    for v in vc.VALUES:
        shown = affinity.rotate(ink, STEP * (v - 1), origin=tuple(pc)).intersection(win)
        want = vc.nn_text(v, WIN_C)
        assert abs(shown.area - want.area) < 0.01 * want.area, f"{v}/{v}: the window shows the wrong ink"
        b = np.array(shown.bounds)
        err = np.hypot((b[0] + b[2]) / 2 - wc[0], (b[1] + b[3]) / 2 - wc[1])
        worst = max(worst, err)
        assert err < 0.1, f"{v}/{v} is {err:.2f} mm off the window centre"
    # a notch rests at the bottom of the rim, under the thumb
    low = disc.intersection(box(C[0] - 0.3, C[1] - R - 1, C[0] + 0.3, C[1] - R + 3))
    assert low.bounds[1] > C[1] - R + 0.5 * vc.NOTCH_DEPTH, "no notch at the bottom of the rim at rest"
    # the cleat: the block's face reaches over the toe of the card's back
    face = unary_union([g for z0, z1, g, _ in asm["block"] if z1 > FACE_Z - 1e-6])
    card_back = min((b for b in asm["card"] if b[1] > SHELF_Z + 1e-6), key=lambda b: b[0])[2]
    caught = face.bounds[3] - card_back.bounds[1]
    assert caught >= 1.0, f"the block overlaps the card's toe by only {caught:.2f} mm"
    # magnets: the card's boss holes over the base's pockets
    boss = min(asm["card"], key=lambda b: b[0])[2]
    holes = sorted(Polygon(p.interiors[0]).centroid.coords[0] for p in vt.polys_of(boss))
    for h, m in zip(holes, sorted(d["mags"])):
        assert np.hypot(h[0] - m[0], h[1] - m[1]) < 0.05, f"card magnet at {h}, base magnet at {m}"
    print(f"assembly check (parts as printed): no collisions; nub centred in a notch; all {len(vc.VALUES)} values "
          f"centred in the window (worst {worst:.3f} mm); a notch rests at the bottom of the rim; the block "
          f"catches {caught:.2f} mm of the card's toe; card magnets over the base's")
    return asm


# ---- export ---------------------------------------------------------------------

def write_plate(objects, folder):
    """objects: [(name, (dx, dy), printed bands)]. One STL per band + the slice_bambu.py arguments."""
    folder.mkdir(parents=True, exist_ok=True)
    for f in folder.glob("*.stl"):
        f.unlink()
    files, slots, grams = [], [], [0.0] * 4
    for name, off, bands in objects:
        for i, (z0, z1, g, slot) in enumerate(bands):
            mesh = vt.extrude(vc.snappable(g), z0, z1)
            if mesh is None:
                continue
            mesh.apply_translation([off[0], off[1], 0])
            fn = folder / f"{name}_{i:02d}_{PALETTE[slot][0]}.stl"
            mesh.export(fn)
            files.append(fn.name)
            slots.append(slot + 1)
            grams[slot] += g.area * (z1 - z0) / 1000 * 1.24
    (folder / "slice_args.txt").write_text(
        " ".join(files) + f" --assemble --extruders {','.join(map(str, slots))} "
        f"--colors \"{','.join(h for _, h in PALETTE)}\" " + " ".join("--set " + x for x in SLICER_SET) + "\n")
    print(f"{folder.name}: {len(files)} STLs; solid grams per slot (PLA 1.24): " +
          ", ".join(f"{i + 1} {PALETTE[i][0]} {g:.2f}" for i, g in enumerate(grams) if g) +
          f" = {sum(grams):.1f} g")


def extent(bands):
    b = np.array([g.bounds for _, _, g, _ in bands])
    return b[:, 0].min(), b[:, 1].min(), b[:, 2].max(), b[:, 3].max()


def base_plate(printed):
    """Back, cover, block and wheel side by side."""
    objects, x = [], 0.0
    for name in ("back", "cover", "wheel"):
        b = extent(printed[name])
        objects.append((name, (x - b[0], -b[1]), printed[name]))
        if name == "cover":                                         # the block lies above the cover
            k = extent(printed["block"])
            objects.append(("block", (x - k[0], b[3] - b[1] + PLATE_GAP - k[1]), printed["block"]))
        x += max(b[2] - b[0], BASE_W if name == "cover" else 0) + PLATE_GAP
    return objects


# ---- previews --------------------------------------------------------------------

HEX = [h for _, h in PALETTE]
SHELF_TONE, BEVEL_TONE, MAGNET = "#e6e1d6", "#d5cfc2", "#8d939b"


def draw_front(ax, d, block_art, card_art, v, docked=True, sim=False):
    wh = d["wh"]
    rot = STEP * (v - 1)
    vd.draw(ax, affinity.rotate(wh["disc"], rot, origin=tuple(C)), HEX[PAPER])
    vd.draw(ax, affinity.rotate(unary_union(wh["groups"]), rot, origin=tuple(C)), HEX[INK])
    vd.draw(ax, d["outline"].difference(d["block"]), SHELF_TONE)
    vd.draw(ax, d["boss_holes"], BEVEL_TONE)
    vd.draw(ax, d["mag_holes"], MAGNET)
    vd.draw(ax, d["mouth"].difference(d["window"]), BEVEL_TONE)
    arts = [(block_art, (0.0, 0.0))] + ([(card_art, (CARD_X0, CARD_Y0))] if docked else [])
    for art, off in arts:
        for k in (PAPER, INK, BLOOD, GOLD):
            g = art[k] if (k == PAPER or not sim) else vc.nozzle_sim(art[k])
            vd.draw(ax, affinity.translate(g, *off), HEX[k])
    ax.set_aspect("equal"); ax.set_facecolor("#9aa0a6"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlim(-2, BASE_W + 2); ax.set_ylim(-PROTRUDE - 2, CARD_Y0 + CARD_H + 2)


def preview(d, block_art, back_art, card_art, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 6, figsize=(25, 7.6))
    for ax, (v, docked, sim, t) in zip(axes, [(1, True, False, "docked, 1/1"), (5, True, False, "5/5"),
                                              (9, True, False, "9/9"),
                                              (1, True, True, "nozzle simulation (colours opened 0.42 mm)"),
                                              (3, False, False, "base alone, 3/3 (shelf, boss holes)")]):
        draw_front(ax, d, block_art, card_art, v, docked, sim)
        ax.set_title(t, fontsize=9)
    ax = axes[5]
    for k in range(4):
        vd.draw(ax, back_art[k].difference(mirror(d["pocket"].union(d["mag_holes"]), BASE_W / 2)), HEX[k])
    ax.set_aspect("equal"); ax.set_facecolor("#9aa0a6"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlim(-2, BASE_W + 2); ax.set_ylim(-PROTRUDE - 2, CARD_Y0 + CARD_H + 2)
    ax.set_title("base back (from behind): detent slot, magnet pockets", fontsize=9)
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close(fig)
    print(f"preview -> {path}")


def parts_preview(d, asm, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    wh = d["wh"]
    fig, axes = plt.subplots(1, 4, figsize=(22, 8))
    ax = axes[0]
    vd.draw(ax, d["plate"], "#e8d2a8")
    vd.draw(ax, d["spacer"], "#7a6a58")
    vd.draw(ax, d["arm"], "#b03a2e")
    vd.draw(ax, d["pin"].union(d["pegs"]), "#2b211b")
    vd.draw(ax, d["mag_holes"], MAGNET)
    ax.plot(*np.asarray(wh["disc"].exterior.coords).T, color="#1f5fa8", lw=0.8)
    ax.set_title("back: plate (beige), spacer (brown), detent (red), pegs + pin,\n"
                 "magnet pockets (grey, open at the back); wheel outline blue", fontsize=9)
    ax = axes[1]
    vd.draw(ax, d["cover"].difference(d["boss_holes"]), SHELF_TONE)
    vd.draw(ax, d["sockets_cover"], "#b8b2a6")
    vd.draw(ax, d["block_low"].difference(d["window"]), "#cfc9bc")
    vd.draw(ax, d["sockets_block"], "#a9a397")
    ax.set_title("from behind the faces: shelf plate (boss holes, sockets) and the block's\n"
                 "underside (window, sockets)", fontsize=9)
    ax = axes[2]
    vd.draw(ax, wh["disc"], HEX[PAPER])
    vd.draw(ax, unary_union(wh["groups"]), HEX[INK])
    ax.set_title("wheel (face): V notches every 40 deg, reeded rim between them", fontsize=9)
    ax = axes[3]
    for z0, z1, g, _ in sorted(asm["card"], key=lambda b: -b[0]):   # seen from behind: deepest band last
        if z1 <= FACE_Z - INLAY + 1e-6:
            tone = "#8f8778" if z0 < SHELF_Z - 1e-6 else ("#f4f1ea" if z0 < SHELF_Z + 0.25 else "#d9d3c6")
            vd.draw(ax, mirror(g, BASE_W / 2), tone)
    ax.set_title("card back (from behind): toe along the bottom edge, two magnet bosses", fontsize=9)
    for ax in axes:
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([]); ax.autoscale_view()
    plt.tight_layout()
    plt.savefig(path, dpi=110)
    plt.close(fig)
    print(f"preview -> {path}")


def section_preview(d, asm, path):
    """Side sections of the re-assembled printed parts, with the magnets drawn in."""
    mx, my = d["mags"][0]
    cuts = [(C[0], (-3, CARD_Y0 + CARD_H + 1), 4.0, f"through the window and axle (x = {C[0]:.1f}), z x4"),
            (C[0], (-3, 30), 1.0, "window, bevel and cleat, true scale"),
            (mx, (d["base_h"] - 22, d["base_h"] + 4), 1.0, f"through a magnet (x = {mx:.1f}), true scale")]
    magnets = [(2, (my - MAG_D / 2, z, MAG_D, MAG_T)) for z in (BACK_T - MAG_ROOF - MAG_T, SHELF_Z - BOSS_H)]
    vc.section_preview(asm, cuts, path, boxes=magnets,
                       tones=dict(back="#7a6a58", wheel="#1f5fa8", cover="#c9a227", block="#b03a2e", card="#3c8d5a"))


# ---- build -----------------------------------------------------------------------

def main():
    d = design()
    block_art = block_regions(d)
    back_art = base_back_regions(d)
    card_art = card_regions(vt.rounded_rect(CARD_W, CARD_H, CORNER_R))
    for name, art, shape in (("block", block_art, d["block"].difference(d["mouth"])),
                             ("card", card_art, vt.rounded_rect(CARD_W, CARD_H, CORNER_R))):
        print(f"{name} face (tiling {sum(g.area for g in art.values()):.2f} of {shape.area:.2f} mm^2): " +
              ", ".join(f"{PALETTE[k][0]} {100 * art[k].area / shape.area:.1f}%" for k in range(4)))
        for cname, (thin, n, small) in vc.printability(art).items():
            if n:
                print(f"  {cname:5s}: {n:4d} islands, {thin:.2f} mm^2 thinner than {vc.BEAD} mm"
                      + (f", small islands {[round(a, 2) for a in small]}" if small else ""))
    parts = parts_of(d, block_art, back_art, card_art)
    printed = {p["name"]: to_print(p) for p in parts}
    asm = assembly_check(d, parts, printed)
    write_plate(base_plate(printed), OUT / "base")
    cb = extent(printed["card"])
    write_plate([("card", (-cb[0], -cb[1]), printed["card"])], OUT / f"card_{CARD_NAME}")
    preview(d, block_art, back_art, card_art, OUT / "dock_preview.png")
    parts_preview(d, asm, OUT / "parts_preview.png")
    section_preview(d, asm, OUT / "section_preview.png")


if __name__ == "__main__":
    main()
