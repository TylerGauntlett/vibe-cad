# Wave jewelry-box insert

## Request
A wave-shaped insert for a walnut jewelry box, modelled on a reference photo
(od_form "Wave jewelry box"): rolling ridges across the short side, creating
valleys to lay jewelry in. The printed insert is to be wrapped in suede.

## Spec (as built)
| Parameter | Value |
|---|---|
| Assembled size | 12.0" × 5.5" × 1.0" (304.8 × 139.7 × 25.4 mm) |
| Profile | cosine wave along the length, 2" crest-to-crest, **crests at both ends** (edges ascend to the walls) |
| Heights | valley floor 0.4", crests 1.0" (0.6" wave) |
| Split | two 6" halves (bed is 256 mm); seam at the middle crest, full 1" thick |
| Joint | 2 dovetail keys on half A → sockets in half B; neck 18 mm, head 26 mm, depth 12 mm, 0.15 mm clearance per side |
| Material / printer | Bambu PLA Basic, Bambu Lab A1 0.4 mm, 0.20 mm Standard, Textured PEI (65 °C) |
| Plates | 2 (one half each; both won't fit on one plate). ~2 h 20 m and ~125 g each |

## Decisions & interpretations
- "Height 1", valleys 0.4", peaks 0.6"" was ambiguous. The user chose **0.4" floor + 0.6" wave = 1.0" crests**.
- The user chose a dovetail over pins or a butt joint.
- The user first asked for descending edges (ends in a valley), then reverted to **ascending** (ends on a crest). The current build has crests at the ends.
- Dimensions are nominal. If the insert must fit an exact box cavity after suede wrapping, subtract about 2× the fabric thickness plus clearance from `LENGTH`/`WIDTH`.

## Files (`out/`)
- `wave_insert_A.stl`, `wave_insert_B.stl`: the print meshes (mm); half A carries the tabs.
- `wave_insert_assembled.step`: both halves in assembled position.
- `wave_insert_A1.3mf`: sliced Bambu A1 project, 2 plates.

## Rebuild
```powershell
.venv\Scripts\python.exe models\wave-insert\wave_insert.py
.venv\Scripts\python.exe tools\check_mesh.py models\wave-insert\out\wave_insert_A.stl models\wave-insert\out\wave_insert_B.stl --png models\wave-insert\out\preview.png
python tools\slice_bambu.py models\wave-insert\out\wave_insert_A.stl models\wave-insert\out\wave_insert_B.stl -o models\wave-insert\out\wave_insert_A1.3mf
```

## History
- 2026-11-11: v1, a single 10" × 4" × 0.5" piece with 5 valleys and crests at the ends.
- 2026-11-11: v2, 12" × 5.5" × 1", split into dovetailed halves, valleys at the ends.
- 2026-11-11: v3, crests at the ends again (current); the seam moved onto a crest.
