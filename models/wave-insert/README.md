# Wave jewelry-box insert

## Request
A wave-shaped insert for a walnut jewelry box, modelled on a reference photo
(od_form "Wave jewelry box"): rolling ridges across the short side, creating
valleys to lay jewelry in. The printed insert is to be wrapped in suede.

## Spec (as built)
| Parameter | Value |
|---|---|
| Assembled size | 11.4" × 4.9" × 1.0" (289.56 × 124.46 × 25.4 mm) |
| Profile | 5 cosine waves, 2.28" crest-to-crest; valleys 0.4", crests 1.0". Each end **ramps straight up to a 1.0" edge at the box wall** (cubic `0.4 + 0.6·(1 − 1.5t + 0.5t³)`, t = distance from wall / 1.14") |
| Split | two equal 5.7" halves; seam in the **centre valley** (0.4" thick) |
| Joint | 2 dovetail keys on half A → sockets in half B; neck 18 mm, head 26 mm, depth 12 mm, 0.15 mm clearance per side |
| Material / printer | Bambu PLA Basic, Bambu Lab A1 0.4 mm, 0.20 mm Standard, Textured PEI (65 °C) |
| Plates | 1 (both halves side by side, ~1 mm apart): **4 h 04 m, 209 g** |

## Decisions & interpretations
- v4 matches the proof of concept `wave_jewelry_insert_1in_end_height.stl` (a single 11.4 × 4.9 × 1" piece,
  too long for the bed at 289.6 mm). From it: the 11.4 × 4.9" footprint, 5 waves instead of 6, and the end
  ramps. Those ramps meet the wall at about 38° instead of rounding over as a cosine crest. The fitted end curve matches the PoC to ~1e-8".
- The seam stays at the centre, which in this profile is a valley. The user accepted the thinner (0.4") joint:
  the insert sits fixed inside the box, so the dovetails only need to locate the halves, not carry load.
- "Height 1", valleys 0.4", peaks 0.6"" was ambiguous. The user chose **0.4" floor + 0.6" wave = 1.0" crests**.
- The user chose a dovetail over pins or a butt joint.
- Profile is one spline through dense samples of the piecewise curve. Separate Bezier ramp + spline edges
  were fused by build123d's post-extrude clean into one face that took minutes to tessellate.

## Verification (v4)
- Assembled halves vs PoC: same bbox, top profile within 0.042 mm (rms 0.007 mm), volume −131 mm³ (the socket clearance).
- `open_edges=0` on both halves; A/B overlap volume 0.

## Files (`out/`)
- `wave_insert_A.stl`, `wave_insert_B.stl`: the print meshes (mm); half A carries the tabs.
- `wave_insert_assembled.step`: both halves in assembled position.
- `wave_insert_A1.3mf`: sliced Bambu A1 project, 1 plate.

## Rebuild
```powershell
.venv\Scripts\python.exe models\wave-insert\wave_insert.py
.venv\Scripts\python.exe tools\check_mesh.py models\wave-insert\out\wave_insert_A.stl models\wave-insert\out\wave_insert_B.stl --png models\wave-insert\out\preview.png
python tools\slice_bambu.py models\wave-insert\out\wave_insert_A.stl models\wave-insert\out\wave_insert_B.stl -o models\wave-insert\out\wave_insert_A1.3mf
```

## History
- 2026-11-11: v1, a single 10" × 4" × 0.5" piece with 5 valleys and crests at the ends.
- 2026-11-11: v2, 12" × 5.5" × 1", split into dovetailed halves, valleys at the ends.
- 2026-11-11: v3, crests at the ends again; the seam moved onto a crest.
- 2026-11-11: v4 (current), matched to the PoC STL: 11.4" × 4.9", 5 waves, cubic end ramps, seam in the centre valley; both halves on one plate.
