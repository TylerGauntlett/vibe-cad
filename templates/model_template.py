#!/usr/bin/env python3
"""
__TITLE__

Spec: see README.md in this folder.

Run (from the repo root):
    .venv\\Scripts\\python.exe models\\__SLUG__\\__MODULE__.py
Outputs (millimetres) go to models\\__SLUG__\\out\\
"""
from pathlib import Path

from build123d import (  # noqa: F401  (import what you need from the main module only)
    BuildPart, BuildSketch, BuildLine, Plane, Pos, Rot, Box, Cylinder,
    Spline, Polyline, Polygon, make_face, extrude, offset, fillet, chamfer,
    export_stl, export_step, Compound, Kind, Axis, IN, MM,
)

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

# ---- Parameters ------------------------------------------------------------
# Work in inches if the user speaks inches, but always multiply by IN so the
# geometry (and every export) is in millimetres.
LENGTH = 4.0 * IN
WIDTH = 2.0 * IN
HEIGHT = 0.5 * IN
EDGE_FILLET = 2.0  # mm
# ---------------------------------------------------------------------------

with BuildPart() as bp:
    Box(LENGTH, WIDTH, HEIGHT, align=None)  # align=None -> corner at origin, sits on z=0
    fillet(bp.edges().filter_by(Axis.Z), radius=EDGE_FILLET)
part = bp.part


def report(name, shape):
    bb = shape.bounding_box()
    sx, sy, sz = bb.max.X - bb.min.X, bb.max.Y - bb.min.Y, bb.max.Z - bb.min.Z
    print(f"{name}: {sx:.1f} x {sy:.1f} x {sz:.1f} mm  "
          f"({sx / IN:.3f} x {sy / IN:.3f} x {sz / IN:.3f} in)  valid={shape.is_valid}")


report("Part", part)

export_stl(part, str(OUT / "__MODULE__.stl"), tolerance=0.01, angular_tolerance=0.1)
export_step(part, str(OUT / "__MODULE__.step"))
print(f"Exported to {OUT}")
