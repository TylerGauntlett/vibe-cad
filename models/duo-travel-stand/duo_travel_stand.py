#!/usr/bin/env python3
"""
iPhone Duo travel MagSafe stand (print-in-place, folds flat)

One 8 mm slab, printed fully assembled, that unfolds into a stand for an UNFOLDED
iPhone Duo (landscape, 164.6 x 117.8 x 5.2 mm):

    B  base   front bar with a trough for the phone's bottom edge + two rails
    P  panel  hinged to the base (hinge A); holds the charger puck behind a front lip
    S  leg    hinged to the panel's top (hinge K); its ear drops into saddles on the left rail

Spec and decisions: see README.md in this folder.

Run (from the repo root):
    .venv\\Scripts\\python.exe models\\duo-travel-stand\\duo_travel_stand.py
Outputs (millimetres) go to models\\duo-travel-stand\\out\\

Frame (as printed = folded): x = width (viewer's right is +x), y = depth (front is -y, hinge A
at y = 0), z = up, slab on z = 0..T. Profiles are drawn in (y, z) and extruded along x.
"""
import math
from functools import reduce
from pathlib import Path

from build123d import (
    Plane, Pos, Rot, Axis, Box, Cylinder, Cone, Circle, Rectangle, RectangleRounded, Polygon,
    extrude, mirror, export_stl, export_step, Compound,
)

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)
NAME = "duo_travel_stand"

# ---- Parameters (mm) -------------------------------------------------------
# Phone: iPhone Duo, unfolded, landscape
PHONE_W, PHONE_H, PHONE_T = 164.6, 117.8, 5.2
RING_X = PHONE_W / 4      # MagSafe ring centre, sideways from the phone's centre (middle of one half)
RING_Z = PHONE_H / 2      # ... and above the phone's bottom edge  (ASSUMED centred: measure and adjust)
RING_SIDE = +1            # +1: ring in the half on the viewer's right; -1 mirrors the whole stand

# Charger puck (third-party, round)
PUCK_D, PUCK_T = 56.0, 7.0
POCKET_CLEAR = 0.15       # radial clearance puck -> pocket wall
RIB = 0.30                # crush ribs stand this far into the pocket (0.15 interference)
LIP_IN, LIP_T = 0.8, 1.0  # front retaining lip: radial overlap, total thickness (45 deg underside)
CABLE_W, CABLE_L, CABLE_ROOF = 13.0, 29.0, 1.2   # cable / USB-C plug tunnel through the panel

# Slab and hinges
T = 8.0                   # slab thickness = folded thickness
R = T / 2                 # knuckle radius; hinge axes sit at mid-thickness
GAP = 0.5                 # in-plane gap between separate parts (vertical walls)
HG = 0.4                  # knuckle gaps: radial (knuckle -> facing wall) and axial (knuckle -> knuckle)
PIN_R, BORE_R = 2.0, 2.4  # pin and bore radius (0.4 radial clearance)
PIN_FLAT = 1.8            # pin is flat this far below the axis (bridges on a layer line, 0.6 above bore)
BORE_ROOF = 2.8           # bore roof is a truncated teardrop this far above the axis

# Layout across x (ring on the right)
W = 122.0
RAIL_W = 6.0              # full-height rail web (both sides)
LEDGE_W = 3.5             # low ledge inside the left rail: carries the saddles
LEG_W = 8.0
X_WEB = -W / 2 + RAIL_W                 # -55.0  inner face of the left web
X_LEDGE = X_WEB + LEDGE_W               # -51.5
X_LEG0 = X_LEDGE + GAP                  # -51.0
X_LEG1 = X_LEG0 + LEG_W                 # -43.0
PX0 = X_LEG1 + GAP                      # -42.5  panel left edge
PX1 = W / 2 - RAIL_W - GAP              #  54.5  panel right edge
EAR_L = LEDGE_W - GAP + GAP             # ear reaches to GAP short of the web
POCKET_WALL_X, POCKET_WALL_TOP = 2.5, 2.6

# Front bar / trough (y, z)
TROUGH_Z = 3.0            # trough floor height
Y_FACE = -(R + HG)        # -4.4  bar's rear face opposite the panel knuckles
Y_RAMP0, Y_LIP = -6.2, -10.7
RAMP_Z = 4.2
LIP_W = 3.0
Y_FRONT = Y_LIP - LIP_W   # -13.7

# Leg / rack
L_LEG = 86.0              # hinge K -> ear axis
LEDGE_H = 4.0
SADDLE_FLOOR = 1.6
SADDLE_R = R + 0.5         # cradle radius: the ear's flat-bottomed barrel (corners at 4.33) sits in it freely
ANGLES = (60.0, 65.0, 70.0, 73.0)   # panel angles from horizontal, one saddle each
THETA_REF = 67.0          # angle at which the puck is exactly centred on the ring

# Detents (45 deg cone nub in a conical dimple)
NUB_R, NUB_H, NUB_TIP = 1.5, 1.0, 0.5
DIMPLE_PLAY = 0.45
# ---------------------------------------------------------------------------

RP = PUCK_D / 2 + POCKET_CLEAR
XC = PX1 - POCKET_WALL_X - RP           # pocket centre x


def s_corner(theta):
    """Distance along the panel (from hinge A) of the phone's back-bottom corner resting in the trough."""
    t = math.radians(theta)
    return (TROUGH_Z - R - R * math.cos(t)) / math.sin(t)


S_RING = RING_Z + s_corner(THETA_REF)   # pocket centre along the panel
P_TOP = S_RING + RP + POCKET_WALL_TOP   # panel body's top edge
S_K = P_TOP + R + HG                    # hinge K
E0 = S_K - L_LEG                        # ear axis when folded
ZS = SADDLE_FLOOR + R - R               # seated ear axis, height above the hinge-A axis level
YL_END = round(S_K + R + 0.7)           # left rail end
YR_END = YL_END                         # right rail end: same reach, for tip-back stability; the gap it
                                        #   leaves above the panel's low right corner is the finger pull
PHONE_XC = XC - RING_X


def leg_pose(theta):
    """(rho, phi, ear_y): leg rotation relative to the panel, leg angle to the table, seated ear y."""
    t = math.radians(theta)
    phi = math.asin((S_K * math.sin(t) - ZS) / L_LEG)
    return 180.0 - theta - math.degrees(phi), math.degrees(phi), S_K * math.cos(t) + L_LEG * math.cos(phi)


# ---- 2D profile helpers, local (y, z) --------------------------------------
def rect(y0, y1, z0, z1):
    return Pos((y0 + y1) / 2, (z0 + z1) / 2) * Rectangle(y1 - y0, z1 - z0)


def poly(*pts):
    return Polygon(*pts, align=None)


def barrel(ya):
    """Round knuckle that prints on the bed: circle + a 45 deg foot under it."""
    k = R / math.sqrt(2)
    f = R * math.tan(math.radians(22.5))
    return Pos(ya, R) * Circle(R) + poly((ya - k, R - k), (ya - f, 0), (ya + f, 0), (ya + k, R - k), (ya, R))


def pin(ya):
    return (Pos(ya, R) * Circle(PIN_R)) & rect(ya - 3, ya + 3, R - PIN_FLAT, R + 3)


def bore(ya):
    a = BORE_R / math.sqrt(2)
    b = BORE_R * math.sqrt(2) - BORE_ROOF
    return Pos(ya, R) * Circle(BORE_R) + poly((ya - a, R + a), (ya - b, R + BORE_ROOF),
                                              (ya + b, R + BORE_ROOF), (ya + a, R + a), (ya, R))


def prism(sk, x0, x1):
    return extrude(Plane.YZ.offset(x0) * sk, amount=x1 - x0)


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def cyl_x(x0, x1, y, z, r):
    return Pos((x0 + x1) / 2, y, z) * Rot(0, 90, 0) * Cylinder(r, x1 - x0)


def cone_x(x_base, sign, y, z, r_base, r_tip, h):
    """Cone with its base at x_base, pointing along sign*x."""
    c = Cone(r_base, r_tip, h)
    return Pos(x_base + sign * h / 2, y, z) * Rot(0, 90 * sign, 0) * c


def nub(x_wall, sign, y, z):
    return cone_x(x_wall, sign, y, z, NUB_R, NUB_TIP, NUB_H)


def dimple(x_wall, sign, y, z):
    """Recess in the wall facing a nub (x_wall = that wall, sign = direction into it)."""
    r0 = NUB_R - GAP + DIMPLE_PLAY
    depth = NUB_H - GAP + 0.4
    return cone_x(x_wall - sign * 0.01, sign, y, z, r0 + 0.01, r0 - depth, depth + 0.01)


def union(parts):
    return reduce(lambda a, b: a + b, parts)


# ---- Knuckle layout along x -------------------------------------------------
def alternate(x0, widths):
    """Intervals of the given widths starting at x0, separated by HG."""
    out, x = [], x0
    for w in widths:
        out.append((x, x + w))
        x += w + HG
    return out


A_PW = 8.0
A_BW = (PX1 - PX0 - 8 * HG - 4 * A_PW) / 5
A_SEG = alternate(PX0, [A_BW, A_PW] * 4 + [A_BW])
A_B, A_P = A_SEG[0::2], A_SEG[1::2]                 # base knuckles, panel knuckles
K_SEG = alternate(PX0, [7.0, 6.5, 7.0, 4.0])
K_P, K_S = K_SEG[0::2], K_SEG[1::2]                 # panel knuckles, leg collars
X_ROD_END = K_SEG[-1][1]

# ---- Base -------------------------------------------------------------------
front = poly((Y_FRONT + 0.4, 0), (Y_FACE, 0), (Y_FACE, TROUGH_Z), (Y_RAMP0, TROUGH_Z), (Y_LIP, RAMP_Z),
             (Y_LIP, T - 0.4), (Y_LIP - 0.4, T), (Y_FRONT + 1.2, T), (Y_FRONT, T - 1.2), (Y_FRONT, 0.4))
b_lug = Pos(0, R) * Circle(R) + rect(Y_FACE - 0.1, R, 0, TROUGH_Z) + rect(-R, R, 0, R)

base_parts = [
    prism(front, -W / 2, W / 2),
    *[prism(b_lug, x0, x1) for x0, x1 in A_B],
    prism(pin(0), PX0, PX1),
    prism(b_lug, -W / 2, X_WEB),                                 # left shoulder (web only: the leg's foot and ear
                                                                 #   sweep the space in front of them as the panel opens)
    box(-W / 2, X_WEB, 0, YL_END, 0, T),                         # left rail web
    box(X_WEB, X_LEDGE, E0 + R + GAP, YL_END, 0, LEDGE_H),       # ledge
    prism(b_lug, PX1, W / 2),                                    # right shoulder
    box(W / 2 - RAIL_W, W / 2, 0, YR_END, 0, T),                 # right rail
    nub(W / 2 - RAIL_W, -1, 76.0, R),                            # detent: holds the panel folded
]
base = union(base_parts)
for th in ANGLES:
    base -= cyl_x(X_WEB - 0.01, X_LEDGE + 1, leg_pose(th)[2], SADDLE_FLOOR + SADDLE_R, SADDLE_R)
mask = Pos(0, (YL_END + Y_FRONT) / 2) * RectangleRounded(W, YL_END - Y_FRONT, 3.0)
base &= extrude(mask, amount=T)

# ---- Panel ------------------------------------------------------------------
p_alug = barrel(0) + rect(0, R + HG + 0.1, 0, T)
p_klug = barrel(S_K) + rect(P_TOP - 0.1, S_K, 0, T)
panel = union([
    box(PX0, PX1, R + HG, P_TOP, 0, T),
    *[prism(p_alug, x0, x1) for x0, x1 in A_P],
    *[prism(p_klug, x0, x1) for x0, x1 in K_P],
])
panel -= prism(bore(0), PX0 - 1, PX1 + 1)
panel -= prism(bore(S_K), PX0 - 1, X_ROD_END + 1)
# puck pocket: open at the back, 45 deg lip at the front
z_lip = T - LIP_T
panel -= Pos(XC, S_RING, (z_lip - 1) / 2) * Cylinder(RP, z_lip + 1)
panel -= Pos(XC, S_RING, z_lip + LIP_IN / 2) * Cone(RP, RP - LIP_IN, LIP_IN)
panel -= Pos(XC, S_RING, T) * Cylinder(RP - LIP_IN, 2 * (LIP_T - LIP_IN) + 0.02)
for a in (45, 135, 225, 315):
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    rr = RP + 0.7 - RIB
    panel += Pos(XC + rr * ca, S_RING + rr * sa, z_lip / 2) * Cylinder(0.7, z_lip)
# cable / plug tunnel: from the pocket toward the far half, open at the back, roofed at the front
panel -= box(XC - RP - CABLE_L, XC - RP + 3, S_RING - CABLE_W / 2, S_RING + CABLE_W / 2, -1, T - CABLE_ROOF)
panel -= dimple(PX1, -1, 76.0, R)        # for the right rail's nub
panel -= dimple(PX0, +1, 14.0, R)        # for the leg's nub

# ---- Leg --------------------------------------------------------------------
leg = union([
    box(X_LEG0, X_LEG1, E0, S_K, 0, T),
    prism(barrel(E0), X_LEG0 - EAR_L, X_LEG1),       # round foot + ear
    prism(barrel(S_K), X_LEG0, X_LEG1),              # round top
    prism(pin(S_K), X_LEG0, X_ROD_END),              # hinge rod
    *[prism(barrel(S_K), x0, x1) for x0, x1 in K_S], # collars
    nub(X_LEG1, +1, 14.0, R),                        # detent: holds the leg folded in the panel
])

if RING_SIDE < 0:
    base, panel, leg = (mirror(p, Plane.YZ) for p in (base, panel, leg))

AX_A = Axis((0, 0, R), (1, 0, 0))
AX_K = Axis((0, S_K, R), (1, 0, 0))


def posed(theta, rho):
    return panel.rotate(AX_A, theta), leg.rotate(AX_K, rho).rotate(AX_A, theta)


def phone_at(theta, lift=0.05):
    xc = PHONE_XC * RING_SIDE
    ph = box(xc - PHONE_W / 2, xc + PHONE_W / 2, s_corner(theta) + lift, s_corner(theta) + lift + PHONE_H,
             T + lift, T + lift + PHONE_T)
    return ph.rotate(AX_A, theta)


def puck_at(theta):
    z_face = z_lip + (RP - PUCK_D / 2)          # square-edged puck seated against the lip cone
    pk = Pos(XC * RING_SIDE, S_RING, z_face - PUCK_T / 2) * Cylinder(PUCK_D / 2 - 0.01, PUCK_T)
    return pk.rotate(AX_A, theta), z_face


# ---- Checks -----------------------------------------------------------------
def overlap(a, b):
    c = a & b
    if c is None:
        return 0.0
    items = c if isinstance(c, (list, tuple)) else [c]
    return sum(s.volume for it in items for s in it.solids())


def report(name, shape):
    bb = shape.bounding_box()
    sx, sy, sz = bb.max.X - bb.min.X, bb.max.Y - bb.min.Y, bb.max.Z - bb.min.Z
    print(f"{name}: {sx:.1f} x {sy:.1f} x {sz:.1f} mm  solids={len(shape.solids())}  "
          f"valid={shape.is_valid}  vol={shape.volume / 1000:.1f} cm^3")


def assembly_check():
    ok = True

    def expect(cond, msg):
        nonlocal ok
        ok &= bool(cond)
        print(f"  {'ok  ' if cond else 'FAIL'} {msg}")

    print("Folded (as printed):")
    for n, s in (("base", base), ("panel", panel), ("leg", leg)):
        expect(len(s.solids()) == 1 and s.is_valid, f"{n} is one valid solid")
    pairs = (("base", base, "panel", panel), ("base", base, "leg", leg), ("panel", panel, "leg", leg))
    for na, a, nb, b in pairs:
        d = a.distance_to(b)
        expect(overlap(a, b) < 1e-6 and d >= 0.29, f"{na} / {nb}: no overlap, min gap {d:.2f} mm")
    bb = Compound([base, panel, leg]).bounding_box()
    expect(bb.min.Z > -1e-6 and bb.max.Z < T + 1e-6, f"everything inside the slab z = 0..{T:g}")

    print("Opening sweep (leg folded into the panel):")
    worst = min(min(base.distance_to(q) for q in posed(th, 0)) for th in (10, 22.5, 35, 50, 65, 80, 90, 95))
    expect(worst > 0.2, f"panel and leg clear the base from 0 to 95 deg (min gap {worst:.2f} mm)")
    print("Leg swing-through (panel at 90 deg):")
    worst = min(min(base.distance_to(posed(90, rho)[1]), posed(90, rho)[0].distance_to(posed(90, rho)[1]))
                for rho in (5, 10, 20, 30, 45, 60))
    expect(worst > 0.2, f"leg clears base and panel while swinging back (min gap {worst:.2f} mm)")

    print("Deployed:")
    for th in ANGLES:
        rho, phi, ey = leg_pose(th)
        p, s = posed(th, rho)
        # lift the leg 0.05 mm out of its saddle so the seated contact does not read as a collision
        s_up = s.move(Pos(0, 0, 0.05))
        bs, bp, ps = overlap(base, s_up), overlap(base, p), overlap(p, s)
        seat = base.distance_to(s_up)
        ph, (pk, _) = phone_at(th), puck_at(th)
        hits = overlap(ph, base) + overlap(ph, p) + overlap(ph, s) + overlap(pk, base) + overlap(pk, s)
        lip_gap = ph.distance_to(base)
        expect(bs + bp + ps < 1e-6 and seat < 0.08 and hits < 1e-6 and lip_gap < 0.3,
               f"{th:g} deg: leg at {phi:.1f} deg, ear seated at y = {ey:.1f} (gap {seat:.2f}), "
               f"no collisions, phone {lip_gap:.2f} mm off the trough")
    return ok


def render(path, theta=65.0):
    """Two shaded views of the deployed stand with the phone ghosted in."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    rho = leg_pose(theta)[0]
    p, s = posed(theta, rho)
    items = [(base, (0.25, 0.27, 0.30), 1.0), (p, (0.85, 0.47, 0.20), 1.0), (s, (0.20, 0.50, 0.75), 1.0),
             (puck_at(theta)[0], (0.92, 0.92, 0.92), 1.0), (phone_at(theta), (0.55, 0.6, 0.7), 0.18)]
    light = np.array([0.3, -0.7, 0.65]); light /= np.linalg.norm(light)
    fig = plt.figure(figsize=(15, 7))
    for i, (elev, azim, title) in enumerate(((22, -62, "front"), (24, 118, "rear"))):
        ax = fig.add_subplot(1, 2, i + 1, projection="3d")
        for shape, col, alpha in items:
            v, f = shape.tessellate(0.05, 0.3)
            pts = np.array([(q.X, q.Y, q.Z) for q in v])
            tri = pts[np.array(f)]
            n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
            n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
            sh = 0.35 + 0.65 * np.clip(n @ light, 0, 1)
            pc = Poly3DCollection(tri, edgecolor="none", alpha=alpha)
            pc.set_facecolor(np.c_[col[0] * sh, col[1] * sh, col[2] * sh, np.full(len(sh), alpha)])
            ax.add_collection3d(pc)
        ax.set_xlim(-110, 75); ax.set_ylim(-45, 140); ax.set_zlim(0, 125)
        ax.set_box_aspect((185, 185, 125))
        ax.view_init(elev, azim); ax.set_axis_off(); ax.set_title(f"{title}, {theta:g} deg")
    plt.tight_layout(); plt.savefig(path, dpi=110)
    print(f"render -> {path}")


if __name__ == "__main__":
    print(f"pocket centre x={XC:.2f} s={S_RING:.2f}  panel top={P_TOP:.2f}  hinge K={S_K:.2f}  "
          f"ear folded y={E0:.2f}  phone centre x={PHONE_XC:.2f}")
    for th in ANGLES:
        rho, phi, ey = leg_pose(th)
        print(f"  {th:g} deg: leg {phi:.1f} deg, opens {rho:.1f} deg from the panel, saddle at y={ey:.2f}")
    report("base ", base)
    report("panel", panel)
    report("leg  ", leg)
    folded = Compound([base, panel, leg])
    report("folded", folded)
    good = assembly_check()

    export_stl(folded, str(OUT / f"{NAME}.stl"), tolerance=0.01, angular_tolerance=0.1)
    export_step(folded, str(OUT / f"{NAME}.step"))
    p65, s65 = posed(65.0, leg_pose(65.0)[0])
    export_step(Compound([base, p65, s65]), str(OUT / f"{NAME}_deployed_view.step"))
    render(str(OUT / "deployed.png"))
    print(f"Exported to {OUT}")
    print("ALL CHECKS PASSED" if good else "CHECKS FAILED")
    raise SystemExit(0 if good else 1)
