#!/usr/bin/env python3
"""
Vampire token card (4-colour AMS): a printable multi-colour version of a
trading-card token, made from a raster image.

Spec: see README.md in this folder.

How it works
  1. Resample the art to the card size at a fine working resolution (PX mm/px).
  2. Snap every pixel to one of 4 filament colours (PALETTE).
  3. Clean the colour map up for a 0.4 mm nozzle: drop islands and slivers
     smaller than MIN_FEATURE / MIN_ISLAND and refill them from their neighbours.
  4. Trace each colour region into polygons. The regions tile the card exactly:
     each colour gets what is left after the earlier ones are subtracted, and the
     base colour (black) takes whatever remains.
  5. Stack it in Z "bands" according to a LAYOUT. Each band says which filament
     slot fills which colour regions between two heights. Every (band, slot) pair
     becomes one watertight STL part.

Colour-swap economics (why there are several layouts)
  Bambu Studio already prints every region of one filament before swapping, and
  starts each layer with the filament the previous layer ended on. So the swaps in
  a layer = (number of filaments in that layer) - 1. On the A1 (no prime tower)
  each swap purges into the chute, and dark->light purges cost about 3x light->dark.
  The layout decides how many layers mix colours and which way the swaps go:
    flat-black  face-down, 3 four-colour layers on a black backing (v1)
    flat-light  face-down, 1 four-colour layer + 1 three-colour layer on a cream backing
    relief      face-up, one Z band per colour from light to dark: 3 swaps in total

Run (from the repo root):
    .venv\\Scripts\\python.exe models\\vampire-token\\vampire_token.py [layout ...]   (default: flat-light relief)
Outputs (millimetres) go to models\\vampire-token\\out\\
    <layout>/vt_<band>_<colour>.stl     parts; load as ONE object (slice_bambu.py --assemble)
    <layout>/slice_args.txt             the matching slice_bambu.py extruder/colour arguments
    colour_preview.png                  what the face should look like, at print resolution
"""
import sys
from pathlib import Path

import cv2
import numpy as np
import trimesh
from PIL import Image
from scipy import ndimage
from shapely import affinity, constrained_delaunay_triangles, set_precision
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
SRC = HERE / "source" / "vampire_token_art.png"

# ---- Parameters (mm) -------------------------------------------------------
CARD_W, CARD_H = 63.0, 88.0     # standard trading-card size
CORNER_R = 3.0                  # card corner radius

PX = 0.05                       # working resolution, mm per pixel
MIN_FEATURE = 0.15              # drop strokes thinner than this (mm); thicker ones are kept and
                                # Arachne widens anything >= 0.1 mm to a printable 0.34 mm bead
MIN_ISLAND = 0.04               # drop isolated specks smaller than this (mm^2, ~0.2 mm across)
SIMPLIFY = 0.02                 # polygon simplification tolerance (mm)

# Filament slots in AMS order. The first is the base and backing colour.
# Hex values are the colour clusters measured in the art; swap in your spools.
PALETTE = [
    ("black", "#241B16"),
    ("red",   "#8E1D19"),
    ("tan",   "#B08551"),
    ("cream", "#F0CB9A"),
]
BLACK, RED, TAN, CREAM = range(4)
ALL = (BLACK, RED, TAN, CREAM)

# Layouts: (face_down, [(z0, z1, {slot: colour regions it fills}), ...]). Heights are multiples of
# the 0.2 mm layer height. Regions not listed in a band are left empty (only used by relief).
LAYOUTS = {
    # v1: 0.6 mm image face (3 layers, all 4 colours each) + 1.0 mm black backing = 1.6 mm
    "flat-black": (True, [
        (0.0, 0.6, {BLACK: [BLACK], RED: [RED], TAN: [TAN], CREAM: [CREAM]}),
        (0.6, 1.6, {BLACK: ALL}),
    ]),
    # Light backing: light colours look right at 1 layer over cream, so only the dark ones
    # (black, red) get a second layer for opacity. 1 four-colour layer + 1 three-colour layer.
    "flat-light": (True, [
        (0.0, 0.2, {BLACK: [BLACK], RED: [RED], TAN: [TAN], CREAM: [CREAM]}),
        (0.2, 0.4, {BLACK: [BLACK], RED: [RED], CREAM: [TAN, CREAM]}),
        (0.4, 1.6, {CREAM: ALL}),
    ]),
    # Relief, face-up: cream base, then each darker colour stacked on top of the lighter ones.
    # One filament per layer -> 3 swaps, all light->dark (the cheap direction). Black ink is
    # raised 1.0 mm above the cream, like a woodcut.
    "relief": (False, [
        (0.0, 1.0, {CREAM: ALL}),
        (1.0, 1.2, {TAN: [TAN, RED, BLACK]}),
        (1.2, 1.6, {RED: [RED, BLACK]}),
        (1.6, 2.0, {BLACK: [BLACK]}),
    ]),
}
# flat-black is kept for comparison only: flat-light beats it on swaps, purge, time and looks.
DEFAULT_LAYOUTS = ["flat-light", "relief"]
# ---------------------------------------------------------------------------


def hex_rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)


def to_lab(rgb):
    """sRGB (0..255, ...x3) -> CIE Lab, for perceptual nearest-colour matching."""
    c = rgb / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[0.4124, 0.3576, 0.1805],
                        [0.2126, 0.7152, 0.0722],
                        [0.0193, 0.1192, 0.9505]]).T
    xyz /= np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16,
                     500 * (f[..., 0] - f[..., 1]),
                     200 * (f[..., 1] - f[..., 2])], -1)


def quantize(img):
    pal = to_lab(np.array([hex_rgb(h) for _, h in PALETTE]))
    lab = to_lab(img)
    d = ((lab[..., None, :] - pal) ** 2).sum(-1)
    lab_map = d.argmin(-1)
    # Near-white pixels are the image's paper corners outside its rounded border: make them base.
    lab_map[img.min(-1) > 240] = 0
    return lab_map


def refill(labels, keep):
    """Pixels where keep is False take the label of the nearest kept pixel."""
    _, (iy, ix) = ndimage.distance_transform_edt(~keep, return_indices=True)
    return labels[iy, ix]


def clean(labels):
    n = len(PALETTE)
    # 1. majority (mode) smoothing: blur each colour's mask and take the argmax
    sig = 0.04 / PX
    prob = np.stack([ndimage.gaussian_filter((labels == k).astype(np.float32), sig) for k in range(n)])
    labels = prob.argmax(0)
    # 2. morphological opening per colour removes strokes thinner than MIN_FEATURE
    r = max(1, int(round(MIN_FEATURE / 2 / PX)))
    disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    keep = np.zeros(labels.shape, bool)
    for k in range(n):
        m = (labels == k).astype(np.uint8)
        keep |= cv2.morphologyEx(m, cv2.MORPH_OPEN, disk).astype(bool)
    labels = refill(labels, keep)
    # 3. remove small islands (any colour), twice since refilling can merge specks
    min_px = MIN_ISLAND / PX ** 2
    for _ in range(2):
        keep = np.ones(labels.shape, bool)
        for k in range(n):
            cc, num = ndimage.label(labels == k)
            if num:
                sizes = np.bincount(cc.ravel())
                small = sizes < min_px
                small[0] = False
                keep &= ~small[cc]
        labels = refill(labels, keep)
    return labels


def trace(mask):
    """Binary mask -> shapely geometry in image mm (u right, v down)."""
    cs, hier = cv2.findContours(mask.astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    if hier is None:
        return Polygon()
    hier = hier[0]
    polys = []
    for i, c in enumerate(cs):
        if hier[i][3] != -1 or len(c) < 3:  # holes handled with their parent
            continue
        shell = (c[:, 0, :] + 0.5) * PX
        holes, j = [], hier[i][2]
        while j != -1:
            if len(cs[j]) >= 3:
                holes.append((cs[j][:, 0, :] + 0.5) * PX)
            j = hier[j][0]
        p = Polygon(shell, holes).buffer(0)
        if not p.is_empty:
            polys.append(p)
    # contours run through boundary-pixel centres; grow half a pixel to reach the true edge
    return unary_union(polys).buffer(0.5 * PX, join_style="mitre").simplify(SIMPLIFY)


def rounded_rect(w, h, r):
    return box(r, r, w - r, h - r).buffer(r, quad_segs=16)


def polys_of(g):
    if g.is_empty:
        return []
    return [g] if g.geom_type == "Polygon" else [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]


def manifold(m):
    """Every edge shared by exactly two faces, after welding on the same 0.1 micron grid that
    tools/check_mesh.py (and a float32 STL) effectively uses."""
    v = np.round(m.triangles.reshape(-1, 3), 4)
    _, idx = np.unique(v, axis=0, return_inverse=True)
    f = idx.reshape(-1, 3)
    e = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    return bool((np.unique(e, axis=0, return_counts=True)[1] == 2).all())


def prism(p, height):
    """Extrude one polygon. Caps come from GEOS's constrained Delaunay triangulation, which
    honours every ring exactly; trimesh's default earcut mis-triangulates polygons with hundreds
    of holes, and since the side walls are built from the cap's boundary edges that breaks the mesh."""
    tris = constrained_delaunay_triangles(orient(p))
    index, verts, faces = {}, [], []
    for t in tris.geoms:
        c = list(t.exterior.coords)[:3]
        if (c[1][0] - c[0][0]) * (c[2][1] - c[0][1]) - (c[1][1] - c[0][1]) * (c[2][0] - c[0][0]) < 0:
            c = [c[0], c[2], c[1]]  # counter-clockwise -> cap normal +Z
        f = []
        for x, y in c:
            k = (round(x, 6), round(y, 6))
            if k not in index:
                index[k] = len(verts)
                verts.append(k)
            f.append(index[k])
        if len(set(f)) == 3:
            faces.append(f)
    return trimesh.creation.extrude_triangulation(np.array(verts), np.array(faces), height)


def extrude(geom, z0, z1):
    # A 2 micron inset splits pinch points (a hole touching its shell at one vertex), and snapping
    # to a 1 micron grid removes near-duplicate vertices, so every island extrudes as a clean
    # manifold. The resulting ~4 micron seams between colours are far below slicer resolution.
    # If rings or islands still touch somewhere (vertex on edge, diagonal pixel corners), the
    # whole region is retried with a slightly larger inset; 10 microns is still invisible.
    base = set_precision(geom, 0.001)
    for inset in (0.002, 0.004, 0.006, 0.010):
        g = set_precision(base.buffer(-inset, join_style="mitre"), 0.0005)
        meshes = []
        for p in polys_of(g):
            if p.area < 1e-4:
                continue
            p = Polygon(p.exterior, [h for h in p.interiors if Polygon(h).area > 1e-3])  # drop pinholes
            meshes.append(prism(p, z1 - z0))
        if not meshes:
            return None
        mesh = trimesh.util.concatenate(meshes)
        if manifold(mesh):
            break
    else:
        print(f"  warning: region at z {z0}-{z1} still has non-manifold edges")
    mesh.apply_translation([0, 0, z0])
    return mesh


def build_layout(name, regions, card):
    face_down, bands = LAYOUTS[name]
    d = OUT / name
    d.mkdir(exist_ok=True)
    for f in d.glob("*.stl"):  # remove stale parts
        f.unlink()

    # image (u right, v down) -> printer coordinates (y up), mirrored when printing face-down
    def place(g):
        g = affinity.translate(affinity.scale(g, 1, -1, origin=(0, 0)), 0, CARD_H)
        return affinity.scale(g, -1, 1, origin=(CARD_W / 2, 0)) if face_down else g

    files, slots, vol = [], [], 0.0
    slot_vol = [0.0] * len(PALETTE)
    for bi, (z0, z1, fill) in enumerate(bands):
        for slot, cols in fill.items():
            if tuple(cols) == ALL:
                g = card
            elif len(cols) == 1:
                g = regions[cols[0]]
            else:  # merged regions: a 10 micron close seals the hairline seams between them
                g = unary_union([regions[c] for c in cols]).buffer(0.01, join_style="mitre") \
                    .buffer(-0.01, join_style="mitre").intersection(card)
            g = place(g)
            mesh = extrude(g, z0, z1)
            if mesh is None:
                continue
            path = d / f"vt_{bi}_{PALETTE[slot][0]}.stl"
            mesh.export(path)
            files.append(path.name)
            slots.append(slot + 1)
            vol += g.area * (z1 - z0)
            slot_vol[slot] += g.area * (z1 - z0)
    top = bands[-1][1]
    (d / "slice_args.txt").write_text(
        " ".join(files) + f" --assemble --extruders {','.join(map(str, slots))} "
        f"--colors \"{','.join(h for _, h in PALETTE)}\" --set wall_generator=arachne\n")
    mixed = [f"{b[0]:.1f}-{b[1]:.1f}" for b in bands if len(b[2]) > 1]
    print(f"{name:10s}: {len(files)} parts, {top:.1f} mm thick, {'face-down' if face_down else 'face-up'}, "
          f"multi-colour bands {mixed or 'none'}, analytic volume {vol / 1000:.2f} cm^3 -> {d}")
    print("            model grams per slot (PLA 1.24 g/cm^3, before purge): " + ", ".join(
        f"{i + 1} {PALETTE[i][0]} {v / 1000 * 1.24:.2f}" for i, v in enumerate(slot_vol)))


def main():
    layouts = sys.argv[1:] or DEFAULT_LAYOUTS
    w_px, h_px = int(round(CARD_W / PX)), int(round(CARD_H / PX))
    img = Image.open(SRC).convert("RGB").resize((w_px, h_px), Image.LANCZOS)
    img = np.asarray(img).astype(float)

    labels = clean(quantize(img))

    card = rounded_rect(CARD_W, CARD_H, CORNER_R)
    regions, taken = {}, Polygon()
    for k in range(len(PALETTE) - 1, 0, -1):  # light colours first; base colour gets the rest
        g = trace(labels == k).intersection(card).difference(taken).buffer(0)
        regions[k] = g
        taken = unary_union([taken, g])
    regions[0] = card.difference(taken).buffer(0)
    for k, (name, hexc) in enumerate(PALETTE):
        print(f"{name:6s} {hexc}: {100 * regions[k].area / card.area:5.1f}% of face, "
              f"{len(polys_of(regions[k]))} islands")
    print(f"tiling check: regions {sum(r.area for r in regions.values()):.2f} mm^2 "
          f"vs card {card.area:.2f} mm^2")
    print(f"card: {CARD_W:.1f} x {CARD_H:.1f} mm ({CARD_W / 25.4:.3f} x {CARD_H / 25.4:.3f} in)")
    for name in layouts:
        build_layout(name, regions, card)

    # colour preview at print resolution (as seen from the face, not mirrored)
    pal = np.array([hex_rgb(h) for _, h in PALETTE], np.uint8)
    yy, xx = np.mgrid[0:h_px, 0:w_px]
    inside = ((np.minimum(xx, w_px - 1 - xx) * PX >= CORNER_R) | (np.minimum(yy, h_px - 1 - yy) * PX >= CORNER_R)
              | (np.hypot(np.minimum(xx * PX, (w_px - xx) * PX) - CORNER_R,
                          np.minimum(yy * PX, (h_px - yy) * PX) - CORNER_R) <= CORNER_R))
    prev = np.where(inside[..., None], pal[labels], 255).astype(np.uint8)
    side = np.concatenate([img.astype(np.uint8), np.full((h_px, 40, 3), 255, np.uint8), prev], 1)
    Image.fromarray(side).save(OUT / "colour_preview.png")
    print(f"preview -> {OUT / 'colour_preview.png'}")


if __name__ == "__main__":
    main()
