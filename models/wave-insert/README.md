# Wave jewelry-box insert

## Request
A wave-shaped insert for a walnut jewelry box, modelled on a reference photo
(od_form "Wave jewelry box"): rolling ridges across the short side, creating
valleys to lay jewelry in. The printed insert is to be wrapped in suede.

## Spec (as built)
| Parameter | Value |
|---|---|
| Size | 10.0" × 3.5" × 0.75" (254.0 × 88.9 × 19.05 mm), **one piece** |
| Profile | 5 waves, 2.0" crest-to-crest; valleys 0.4", crests 0.75". A cosine pushed through a gain curve (exponent 1.12), which flattens crests and valleys a little and steepens the flanks. Each end **ramps up to a 0.75" edge at the box wall** (parabola `0.4 + 0.35·(1 − t)²`, t = distance from wall / 1.0"; about 35° at the wall) |
| Split | none (`SPLIT = False`). `SPLIT = True` cuts it in the centre valley into two halves with 2 dovetail keys (neck 18 mm, head 26 mm, depth 12 mm, 0.15 mm clearance per side), for a length that won't fit the bed |
| Material / printer | Bambu PLA Basic, Bambu Lab A1 0.4 mm, 0.20 mm Standard, Textured PEI (65 °C); 15 % grid infill, 2 walls (the same presets as v4) |
| Plates | 1, the part **on the bed's diagonal** (45°), 6.8 mm clear of every edge: **2 h 27 m, 115 g** |

## Decisions & interpretations
- v5 matches the proof of concept `wave_jewelry_insert_10x3.5in_0.75peak.stl` (a single 10 × 3.5 × 0.75" piece).
  From it: the footprint, the 0.75" crests on the same 0.4" floor, and two changes of curve. The interior is no longer a
  pure cosine: `u = ½(2c)^1.12` below mid height, mirrored above it, with `c = (1 + cos)/2`. The end ramps are a
  parabola where v4's were the cubic `1 − 1.5t + 0.5t³`. Both forms fit the PoC to ~1e-7".
- **One piece, no dovetail.** v2–v4 were split only because 289.6 mm didn't fit the bed. 254 mm does, so the seam
  under the suede goes away. The dovetail code stays behind `SPLIT` for a longer insert.
- **Diagonal on the plate.** Laid square, the part is 1 mm from the front and rear edges of the 256 mm bed (that is
  what the slicer's arranger does on its own). At 45° its box is 242.5 mm square. `slice_bambu.py --rotate 45`
  places it there; rotating it back in Bambu Studio also slices, with the 1 mm margins.
- Slicer settings carried over from v4 unchanged: the stock presets (15 % grid infill, 2 walls, 5 top / 3 bottom layers).
- "Height 1", valleys 0.4", peaks 0.6"" (v2) was ambiguous. The user chose a 0.4" floor with the wave on top; the
  0.4" floor is kept here.
- Profile is one spline through dense samples of the piecewise curve. Separate Bezier ramp + spline edges
  were fused by build123d's post-extrude clean into one face that took minutes to tessellate.

## Verification (v5)
- Against the PoC: same bbox, top profile within 0.021 mm (rms 0.005 mm), volume +0.03 % (323.19 vs 323.10 cm³).
- Analytic volume 19.717 in³ (323.1 cm³); mesh 19.722 in³.
- `open_edges=0`. A build with `SPLIT = True` still gives two valid, watertight halves with zero overlap (not kept).

## Files (`out/`)
- `wave_insert.stl`: the print mesh (mm), long axis along X.
- `wave_insert.step`: the exact solid.
- `wave_insert_A1.3mf`: sliced Bambu A1 project, 1 plate. Open it in Bambu Studio and print from there.

## Rebuild
```powershell
.venv\Scripts\python.exe models\wave-insert\wave_insert.py
.venv\Scripts\python.exe tools\check_mesh.py models\wave-insert\out\wave_insert.stl --png models\wave-insert\out\preview.png
python tools\slice_bambu.py models\wave-insert\out\wave_insert.stl -o models\wave-insert\out\wave_insert_A1.3mf --rotate 45
```

## History
- 2026-11-11: v1, a single 10" × 4" × 0.5" piece with 5 valleys and crests at the ends.
- 2026-11-11: v2, 12" × 5.5" × 1", split into dovetailed halves, valleys at the ends.
- 2026-11-11: v3, crests at the ends again; the seam moved onto a crest.
- 2026-11-11: v4, matched to the PoC STL `wave_jewelry_insert_1in_end_height.stl`: 11.4" × 4.9" × 1", 5 waves, cubic end ramps, seam in the centre valley; both halves on one plate (4 h 04 m, 209 g).
- 2026-11-23: v5 (current), matched to the new PoC STL: 10" × 3.5" × 0.75", flattened-cosine waves, parabolic end ramps; one piece, printed diagonally. `slice_bambu.py` gained `--rotate` and now merges the presets' `include` templates.
