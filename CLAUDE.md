# vibe-cad: parametric 3D models for printing

A workspace for designing printable parts in code (build123d), validating them,
and slicing them into ready-to-print Bambu Lab A1 projects. Each model lives in
its own folder under `models/`. Shared tooling lives in `tools/`.

## Layout
```
CLAUDE.md               this file: methodology + environment (read first)
README.md               human quickstart
requirements.txt        pinned Python deps for .venv
.venv/                  Python 3.11 venv with build123d (not committed)
tools/
  new_model.py          scaffold models/<slug>/ from templates/
  check_mesh.py         watertight / volume / size / bed-fit check + preview PNG
  slice_bambu.py        STL(s) -> sliced A1 .3mf via the installed Bambu Studio (incl. multi-colour AMS)
templates/              model_template.py + model_README.md used by new_model.py
models/<slug>/
  <module>.py           the parametric model (parameters at the top)
  README.md             request, spec, decisions, history for that model
  out/                  generated: .stl, .step, _A1.3mf, preview.png
```

## Workflow for a new model
1. **Pin down the spec before modelling.** Restate dimensions, units and orientation.
   If numbers conflict (e.g. "height 1"" alongside "peaks 0.6""), ask with
   AskUserQuestion and offer concrete interpretations with ASCII previews. Don't guess.
   Also ask about joints and splits when a part won't fit the bed.
2. Scaffold: `python tools\new_model.py <slug> "<Title>"`.
3. Model in `models/<slug>/<module>.py`. Put every dimension in the parameter block at the
   top. Write dimensions in the user's units (inches are common here) × `IN`, so geometry
   and exports are in **mm**.
4. Build: `.venv\Scripts\python.exe models\<slug>\<module>.py`. It prints the bbox in mm and in, plus `is_valid`.
5. Verify: `.venv\Scripts\python.exe tools\check_mesh.py <stl...> --png <out>\preview.png`.
   Require `open_edges=0` and a fit on the 256 mm bed. Look at the PNG. Cross-check the
   mesh volume against an analytic estimate when one is easy to compute.
6. Slice: `python tools\slice_bambu.py <stl...> -o models\<slug>\out\<module>_A1.3mf`.
   Report the per-plate time and grams to the user.
7. Update `models/<slug>/README.md`: spec table, the decisions made, and a history line.
8. Remove stale outputs that no longer match the model.

## File types and when to use them
- **STL** (mm): the mesh for any slicer. Always export. STL has no units, and mm is the convention.
- **STEP**: the exact solid for CAD, CNC or editing in Fusion. Always export it as well
  (for split parts, the assembled `Compound` is handy).
- **3MF (Bambu project)**: the deliverable for printing. It carries the plates, printer,
  process and filament settings plus the sliced G-code, so prefer it over a bare STL when
  the user will print on the A1. Generate it with `tools/slice_bambu.py`. Don't hand-build
  Bambu 3MF metadata.
- **GLB**: only needed for web viewers or the `render-glb` plugin. Not installed or used so far.

## Printer and materials (defaults; confirm per job if it matters)
- **Bambu Lab A1**: 256 × 256 × 256 mm build volume, 0.4 mm nozzle, open frame (no enclosure).
- Bed: **Textured PEI Plate** (the A1's stock plate), with PLA at 65 °C.
- Filament: **Bambu PLA Basic**. Process: **0.20mm Standard @BBL A1** (15% infill, 2 walls).
- Parts larger than about 250 mm on any axis must be split; a part can also be rotated
  diagonally. Put each oversize half on its own plate (the slicer arranges this automatically).

## Environment (Windows 10, PowerShell)
- Python 3.11 at the system level. **`uv` is not installed**, so ignore the VibeCAD skill's
  `uvx --from build123d` advice and use `.venv\Scripts\python.exe` instead. Recreate the venv with
  `python -m venv .venv; .venv\Scripts\python.exe -m pip install -r requirements.txt`.
- **Bambu Studio 02.07** is at `C:\Program Files\Bambu Studio\bambu-studio.exe`. Its system
  presets are in `%APPDATA%\BambuStudio\system\BBL\{machine,process,filament}`.
- Claude Code plugin **`build123d@vibecad`** is installed (marketplace `rawwerks/VibeCAD`).
  Its skill `build123d:build123d` holds build123d references and examples. Its own files
  are at `%USERPROFILE%\.claude\plugins\cache\vibecad\build123d\*\skills\build123d\`.

## build123d gotchas learned here
- Import everything from `build123d`. There is no `build123d.exporters` module.
- The `Plane.XZ` normal is **-Y**: `extrude(amount=-W)` grows the part toward +Y.
- For a wave or any curved profile: sketch on `Plane.XZ` with `Spline(*pts)` plus a closing `Polyline`, then `make_face()` and `extrude`.
- To split parts, intersect with half-space boxes (`full & box`). Add tabs with `+` and cut sockets with `-`, making each socket with `offset(sketch, clearance, kind=Kind.ARC)`.
- `a & b` returns **None** when the shapes don't overlap. That's the quick check that mating parts don't collide.
- The B-rep `.volume` was about 1.3% off on a spline solid. Trust the mesh volume from `check_mesh.py`.
- `export_stl(shape, path, tolerance=0.01, angular_tolerance=0.1)` gives smooth curves at a manageable size (about 20k triangles for a 6" wave half).

## Bambu Studio CLI gotchas (handled in slice_bambu.py)
- The exe is a GUI-subsystem binary: `--help` prints nothing. Check the exit code and `result.json` (`error_string: "Success."`).
- System presets use `inherits` chains and must be flattened before `--load-settings`.
- Without `--curr-bed-type` the CLI picks **Cool Plate**, which gives a cold bed. Always pass the plate.
- The CLI writes `plate_N.gcode` and `result.json` next to the 3MF. The script slices in a temp dir.
- `printer_model_id` comes out blank, so tell the user to **open the 3MF in Bambu Studio and print from there** rather than sending it straight to the printer.
- The `bed_temperature_too_high_than_filament` warning is an enclosure advisory. It's harmless on the open-frame A1.
- **Multi-colour (AMS)**: `slice_bambu.py a.stl b.stl ... --assemble --extruders 1,2,... --colors "#..,#.."`.
  A hand-written input 3MF crashes the CLI (access violation), even with p:UUIDs. So the script
  has the CLI `--assemble` the STLs (export only), patches each `<part>`'s `extruder` in
  `model_settings.config`, then slices that. The object-level `extruder` must be set too, or it
  overrides the **first** part's filament.
- The CLI's default `flush_volumes_matrix` is a flat 280 mm³. `--flush auto` writes a colour-aware estimate.
- The A1 process has **no prime tower**: every swap purges into the chute. Per-layer swaps = filaments in
  that layer − 1, because Bambu already groups by filament and chains layers. Dark→light purges cost ~3× light→dark.
- `slice_info.config` `<filament>` entries and the gcode's `total filament weight` list can drop a slot
  and shift the rest. Count swaps from `M620 S<n>A` lines (the initial load isn't in the gcode).

## Image → multi-colour mesh (see models/vampire-token)
- Quantize in Lab, then clean with a gentle majority blur + opening. Too much opening wipes out thin
  highlights. Use `wall_generator=arachne`, which prints strokes down to ~0.1 mm as a 0.34 mm bead.
- Trace with `cv2.findContours(RETR_CCOMP)`, grow by half a pixel, and make the colours tile the card exactly by
  ordered subtraction, with the base colour = card − rest.
- Triangulate caps with `shapely.constrained_delaunay_triangles` + `trimesh.creation.extrude_triangulation`.
  trimesh's default earcut mis-triangulates polygons with hundreds of holes, which gives non-manifold walls.
  Inset each region 2–10 µm to break pinch points, and verify the whole region is manifold.
- Stack colours in Z "bands" to control swaps: the face-up light→dark relief needs only 3 swaps for 4 colours.

## Printing design rules of thumb
- Design parts to print flat on their largest flat face, with no supports. Keep overhangs at or under 45°.
- Mating clearance: about **0.15 mm per side** for press- or slide-fit joints on the A1 (elephant-foot compensation is 0.075 mm by default).
- Place split seams in thick regions (e.g. on a crest rather than in a valley) for joint strength.
- For fabric-wrapped inserts, the model dimension is the bare core: subtract about 2× the fabric thickness plus clearance to fit a cavity.

## Preview images
`check_mesh.py --png` renders with matplotlib, and dark blotches on curved faces are
depth-sorting artifacts, not holes. Trust `open_edges`. View the PNG with the Read tool.

## Model index
| Model | Folder | Status |
|---|---|---|
| Wave jewelry-box insert (12×5.5×1", 2 dovetailed halves) | `models/wave-insert/` | v3 sliced for A1 |
| Vampire token card, 4-colour AMS (63×88 mm; flat-light + relief layouts) | `models/vampire-token/` | v2 sliced for A1 |
