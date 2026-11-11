#!/usr/bin/env python3
"""
Wave jewelry-box insert, split into two dovetailed halves for a 256 mm print bed.

Assembled: 12" long x 5.5" wide; valley floor 0.4", crests 1.0" (0.6" wave).
Each half is 6" long (half A also carries the dovetail tabs that key into B).

Run (from the repo root):  .venv\\Scripts\\python.exe models\\wave-insert\\wave_insert.py
Outputs (millimetres) in out\\: wave_insert_A.stl, wave_insert_B.stl, wave_insert_assembled.step
"""
import math
from pathlib import Path
from build123d import (
    BuildPart, BuildSketch, BuildLine, Plane, Spline, Polyline, Polygon,
    make_face, extrude, offset, export_stl, export_step, Box, Pos, Kind, IN,
    Compound,
)

# ---- Parameters (inches unless noted) ------------------------------------
LENGTH = 12.0            # assembled length (X); split into two equal halves
WIDTH = 5.5              # Y; the wave ridges run across this direction
VALLEY = 0.4             # material thickness at the bottom of each valley
PEAK = 1.0               # overall height at the crests (VALLEY + 0.6" wave)
PERIOD = 2.0             # crest-to-crest spacing; crests sit at both ends
SAMPLES_PER_WAVE = 24

# Dovetail joint (millimetres)
DT_NECK = 18.0           # tab width at the seam
DT_HEAD = 26.0           # tab width at its tip
DT_DEPTH = 12.0          # how far the tab reaches into half B
DT_CLEARANCE = 0.15      # per-side gap between tab and socket
DT_COUNT = 2             # tabs spread evenly across the width
# --------------------------------------------------------------------------

L, W = LENGTH * IN, WIDTH * IN
SEAM = L / 2
z_lo, z_hi = VALLEY * IN, PEAK * IN
mid, amp = (z_hi + z_lo) / 2, (z_hi - z_lo) / 2
P = PERIOD * IN


def z(x):
    # +cos starts and ends on a crest, so both ends ascend toward the walls
    return mid + amp * math.cos(2 * math.pi * x / P)


n = round(L / P * SAMPLES_PER_WAVE)
pts = [(L * i / n, z(L * i / n)) for i in range(n + 1)]

# Full-length wave solid
with BuildPart() as full_bp:
    with BuildSketch(Plane.XZ):
        with BuildLine():
            Spline(*pts)
            Polyline(pts[-1], (L, 0), (0, 0), pts[0])
        make_face()
    extrude(amount=-W)  # Plane.XZ normal is -Y, so this grows toward +Y
full = full_bp.part

tall = z_hi * 3  # cutter height, comfortably above the crests
y_centres = [W * (i + 0.5) / DT_COUNT for i in range(DT_COUNT)]


def dovetail_sketch(yc):
    return Polygon(
        (SEAM - 2, yc - DT_NECK / 2),          # small overlap back into half A
        (SEAM, yc - DT_NECK / 2),
        (SEAM + DT_DEPTH, yc - DT_HEAD / 2),
        (SEAM + DT_DEPTH, yc + DT_HEAD / 2),
        (SEAM, yc + DT_NECK / 2),
        (SEAM - 2, yc + DT_NECK / 2),
        align=None,
    )


tabs = None
sockets = None
for yc in y_centres:
    tab = extrude(dovetail_sketch(yc), amount=tall)
    sock = extrude(offset(dovetail_sketch(yc), amount=DT_CLEARANCE, kind=Kind.ARC), amount=tall)
    tabs = tab if tabs is None else tabs + tab
    sockets = sock if sockets is None else sockets + sock

left_box = Pos(SEAM / 2, W / 2, tall / 2) * Box(SEAM, W, tall)
right_box = Pos(SEAM + SEAM / 2, W / 2, tall / 2) * Box(SEAM, W, tall)

half_a = (full & left_box) + (full & tabs)
half_b = (full & right_box) - sockets


def report(name, shape):
    bb = shape.bounding_box()
    sx, sy, sz = bb.max.X - bb.min.X, bb.max.Y - bb.min.Y, bb.max.Z - bb.min.Z
    print(f"{name}: {sx:.1f} x {sy:.1f} x {sz:.1f} mm  "
          f"({sx/IN:.3f} x {sy/IN:.3f} x {sz/IN:.3f} in)  valid={shape.is_valid}")


report("Full ", full)
report("Half A", half_a)
report("Half B", half_b)

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
export_stl(half_a, str(OUT / "wave_insert_A.stl"), tolerance=0.01, angular_tolerance=0.1)
# Half B is shifted back to the origin so it slices from the same corner as A
export_stl(Pos(-SEAM, 0, 0) * half_b, str(OUT / "wave_insert_B.stl"), tolerance=0.01, angular_tolerance=0.1)
export_step(Compound([half_a, half_b]), str(OUT / "wave_insert_assembled.step"))
print(f"Exported wave_insert_A.stl, wave_insert_B.stl, wave_insert_assembled.step -> {OUT}")
