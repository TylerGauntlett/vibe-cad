#!/usr/bin/env python3
"""
Validate STL files for 3D printing and optionally render a preview PNG.

Usage:
    .venv\\Scripts\\python.exe tools\\check_mesh.py part1.stl [part2.stl ...] [--png preview.png] [--bed 256]

For each STL reports: triangle count, mesh volume (in^3 and cm^3), bounding box
(mm and in), open/non-manifold edge count (must be 0), and whether it fits the bed.
Exit code 1 if any mesh is not watertight or does not fit.

The preview lays parts out side by side. It uses matplotlib, whose depth sorting
sometimes paints dark patches on curved surfaces: that is a renderer artifact,
not a geometry fault - trust the open-edge count.
"""
import argparse
import struct
import sys

import numpy as np

IN = 25.4


def load_stl(path):
    data = open(path, "rb").read()
    if data[:5] == b"solid" and b"facet" in data[:400]:
        verts = [[float(v) for v in line.split()[1:4]]
                 for line in data.decode(errors="ignore").splitlines()
                 if line.strip().startswith("vertex")]
        return np.array(verts, dtype=float).reshape(-1, 3, 3)
    n = struct.unpack("<I", data[80:84])[0]
    rec = np.frombuffer(data[84:84 + n * 50],
                        dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]))
    return rec["v"].reshape(-1, 3, 3).astype(float)


def open_edge_count(tris):
    # Weld vertices on a 1e-4 mm grid, then every undirected edge must be shared by exactly 2 faces
    v = np.round(tris.reshape(-1, 3), 4)
    _, idx = np.unique(v, axis=0, return_inverse=True)
    f = idx.reshape(-1, 3)
    e = np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1)
    _, counts = np.unique(e, axis=0, return_counts=True)
    return int((counts != 2).sum())


def render(parts, names, out_png):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    palette = [(0.30, 0.38, 0.24), (0.36, 0.30, 0.22), (0.25, 0.32, 0.42), (0.42, 0.28, 0.28)]
    light = np.array([0.4, -0.6, 1.0]); light /= np.linalg.norm(light)
    fig = plt.figure(figsize=(13, 8))
    ax = fig.add_subplot(1, 1, 1, projection="3d")
    x_off, gap, hi = 0.0, 15.0, np.zeros(3)
    for i, t in enumerate(parts):
        t = t - t.reshape(-1, 3).min(0) + np.array([x_off, 0, 0])
        size = t.reshape(-1, 3).max(0)
        hi = np.maximum(hi, size)
        x_off = size[0] + gap
        nrm = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
        s = 0.3 + 0.7 * np.clip(nrm @ light, 0, 1)
        c = palette[i % len(palette)]
        pc = Poly3DCollection(t, edgecolor="none")
        pc.set_facecolor(np.c_[c[0] * s, c[1] * s, c[2] * s])
        ax.add_collection3d(pc)
    span = max(hi[0], hi[1])
    ax.set_xlim(0, span); ax.set_ylim(0, span); ax.set_zlim(0, max(hi[2], 1))
    ax.set_box_aspect((span, span, max(hi[2], 1)))
    ax.view_init(50, -65); ax.set_axis_off()
    ax.set_title("  |  ".join(names))
    plt.tight_layout(); plt.savefig(out_png, dpi=110)
    print(f"preview -> {out_png}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl", nargs="+")
    ap.add_argument("--png", help="write a preview image here")
    ap.add_argument("--bed", type=float, default=256.0, help="square bed size in mm (Bambu A1 = 256)")
    a = ap.parse_args()

    ok, parts = True, []
    for p in a.stl:
        t = load_stl(p)
        parts.append(t)
        vol = np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6
        size = t.reshape(-1, 3).max(0) - t.reshape(-1, 3).min(0)
        bad = open_edge_count(t)
        fits = bool((size <= a.bed).all())  # square bed, so rotation doesn't matter
        ok &= bad == 0 and fits
        print(f"{p}\n  triangles={len(t)}  volume={vol / IN**3:.3f} in^3 ({vol / 1000:.1f} cm^3)"
              f"\n  size={size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm"
              f"  ({size[0] / IN:.3f} x {size[1] / IN:.3f} x {size[2] / IN:.3f} in)"
              f"\n  open_edges={bad} {'OK' if bad == 0 else 'NOT WATERTIGHT'}"
              f"  fits {a.bed:.0f} mm bed: {'yes' if fits else 'NO'}")
    if a.png:
        render(parts, [p.replace("\\", "/").split("/")[-1] for p in a.stl], a.png)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
