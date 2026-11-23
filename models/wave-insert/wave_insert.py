#!/usr/bin/env python3
"""
Wave jewelry-box insert.

10.0" long x 3.5" wide x 0.75" tall; valley floor 0.4", crests 0.75".
Profile matches the proof of concept wave_jewelry_insert_10x3.5in_0.75peak.stl:
5 waves (a cosine with slightly flattened crests and valleys), with each end
ramping up to a 0.75" edge at the box wall (a parabola, not a rounded crest).

At 254 mm it prints in one piece on the 256 mm bed. Set SPLIT = True for a longer
insert: it is then cut in the centre valley into two halves, and half A carries the
dovetail tabs that key into half B.

Run (from the repo root):  .venv\\Scripts\\python.exe models\\wave-insert\\wave_insert.py
Outputs (millimetres) in out\\: wave_insert.stl + wave_insert.step, or with SPLIT
wave_insert_A.stl, wave_insert_B.stl + wave_insert_assembled.step
"""
import math
from pathlib import Path
from build123d import (
    BuildPart, BuildSketch, BuildLine, Plane, Spline, Polyline, Polygon,
    make_face, extrude, offset, export_stl, export_step, Box, Pos, Kind, IN,
    Compound,
)

# ---- Parameters (inches unless noted) ------------------------------------
LENGTH = 10.0            # assembled length (X)
WIDTH = 3.5              # Y; the wave ridges run across this direction
VALLEY = 0.4             # material thickness at the bottom of each valley
PEAK = 0.75              # height at the interior crests and at both end walls
WAVES = 5                # wave periods along the length (period = LENGTH / WAVES)
SHAPE = 1.12             # 1 = pure cosine; above 1 flattens crests and valleys and steepens the flanks
SAMPLES_PER_WAVE = 96

SPLIT = False            # True: two dovetailed halves, for a LENGTH that won't fit the bed
BED = 256.0              # mm; Bambu Lab A1

# Dovetail joint (millimetres; used only with SPLIT)
DT_NECK = 18.0           # tab width at the seam
DT_HEAD = 26.0           # tab width at its tip
DT_DEPTH = 12.0          # how far the tab reaches into half B
DT_CLEARANCE = 0.15      # per-side gap between tab and socket
DT_COUNT = 2             # tabs spread evenly across the width
# --------------------------------------------------------------------------

L, W = LENGTH * IN, WIDTH * IN
SEAM = L / 2             # centre valley (WAVES is odd)
z_lo, z_hi = VALLEY * IN, PEAK * IN
P = L / WAVES
H = P / 2                # wall-to-first-valley run of each end ramp

if SPLIT:
    assert WAVES % 2 == 1, "the seam sits in the centre valley, which needs an odd number of waves"
else:
    assert L <= BED, f"{L:.1f} mm is longer than the {BED:.0f} mm bed: set SPLIT = True"


def z(x):
    d = min(x, L - x)    # distance from the nearer end wall
    if d < H:
        # End ramp: a parabola, VALLEY + WAVE*(1 - t)^2 with t = d/H. It leaves the wall at
        # atan(2*WAVE/H) (~35 deg here) and meets the first valley tangentially.
        u = (1 - d / H) ** 2
    else:
        # Interior: cosine with crests at x = k*P and valleys at x = (k + 1/2)*P, pushed through
        # a gain curve (exponent SHAPE) that is antisymmetric about the mid height.
        c = (1 + math.cos(2 * math.pi * x / P)) / 2          # 1 on a crest, 0 in a valley
        u = 0.5 * (2 * c) ** SHAPE if c < 0.5 else 1 - 0.5 * (2 * (1 - c)) ** SHAPE
    return z_lo + (z_hi - z_lo) * u


# One spline through dense samples. Separate Bezier/Spline edges get fused by
# the post-extrude clean into a single badly parameterised face that won't mesh.
n = WAVES * SAMPLES_PER_WAVE
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


def report(name, shape):
    bb = shape.bounding_box()
    sx, sy, sz = bb.max.X - bb.min.X, bb.max.Y - bb.min.Y, bb.max.Z - bb.min.Z
    print(f"{name}: {sx:.1f} x {sy:.1f} x {sz:.1f} mm  "
          f"({sx/IN:.3f} x {sy/IN:.3f} x {sz/IN:.3f} in)  valid={shape.is_valid}")


# Analytic volume: the interior curve averages the mid height, each end ramp VALLEY + WAVE/3
vol = W * ((L - 2 * H) * (z_lo + z_hi) / 2 + 2 * H * (z_lo + (z_hi - z_lo) / 3))
print(f"Analytic volume: {vol / IN**3:.3f} in^3 ({vol / 1000:.1f} cm^3)")

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
MESH = dict(tolerance=0.01, angular_tolerance=0.1)

if not SPLIT:
    report("Insert", full)
    export_stl(full, str(OUT / "wave_insert.stl"), **MESH)
    export_step(full, str(OUT / "wave_insert.step"))
    print(f"Exported wave_insert.stl, wave_insert.step -> {OUT}")
else:
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

    report("Full ", full)
    report("Half A", half_a)
    report("Half B", half_b)
    clash = half_a & half_b   # the halves touch on the seam face, so test volume, not None
    print(f"A/B overlap volume: {0 if clash is None else clash.volume:.3f} mm^3", flush=True)

    export_stl(half_a, str(OUT / "wave_insert_A.stl"), **MESH)
    # Half B is shifted back to the origin so it slices from the same corner as A
    export_stl(Pos(-SEAM, 0, 0) * half_b, str(OUT / "wave_insert_B.stl"), **MESH)
    export_step(Compound([half_a, half_b]), str(OUT / "wave_insert_assembled.step"))
    print(f"Exported wave_insert_A.stl, wave_insert_B.stl, wave_insert_assembled.step -> {OUT}")
