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
- Build a piecewise profile (e.g. ramp + cosine) as ONE `Spline` through dense samples. Separate G1-joined
  Bezier/Spline edges get fused into one face by the post-extrude clean, and it then takes minutes to tessellate.
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
- Slicer warnings such as "floating regions" appear only in the CLI's `result.json` (`warning_message`).
  `slice_bambu.py` prints them as `WARNING`. Check for that line, because the 3MF doesn't carry them.
- The CLI writes `enable_prime_tower = 0` for these A1 multi-colour jobs even though the preset (and `--set`) says 1.
  Tell the user to switch it on in the GUI if wanted.
- Stacked colour reliefs: strokes under ~0.2 mm trigger "floating regions" (Bambu skips them in some
  layers). Drop them (the opening disk ≥ 0.25 mm) for multi-layer columns.
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
- `shapely.set_precision(g, grid)` **attaches** the grid to the geometry, and later buffers run on it: a 2 µm inset
  on a 1 µm grid deleted thin slanted strokes (the / in 2/2). Reset it with `set_precision(g, 0)` before buffering.
- Printable art ≠ clean art: in a relief, anything under one bead (~0.45 mm wide) or ~1 mm² prints as broken beads or stray
  dots. Open every colour to ≥ 0.5 mm and drop islands < 1 mm², but zone it. Faces get milder settings. Thin frame lines
  get a light clean plus 0.1 mm/side dilation instead, because opening deletes them (models/vampire-dial `ZONES`).
- Small text (< ~3 mm caps) from raster art is unprintable: re-set it as vector text in a condensed sans with tracking
  (Bahnschrift SemiBold Condensed via a fontTools instance). Judge fonts by simulating the nozzle: open the glyphs with
  0.42 mm, close with 0.3 mm. Use the nonzero fill rule for glyphs; even-odd punches holes where variable-font contours overlap.
- Thin frame lines in raster art (gold rims around text boxes) survive clean-up only in patches. Redraw them: find the
  box interior (connected component + fill holes + smoothing), then draw a uniform rim and outline by dilation.
- Bambu silently skips islands much under 0.3 mm² (a 0.49 mm-square i-dot vanished; 0.29 mm² printed). Verify
  against the G-code. Align the plate offset by fitting, because outer-wall centrelines sit half a bead inside the edge.
- Arachne leaves hollow slits in strips 2–3 beads wide (~1.0–1.4 mm): the extra bead stops short. `--set
  wall_transition_angle=30 --set wall_transition_filter_deviation=50%` filled them (measured on models/vampire-dial).
  Adding `min_bead_width=50% wall_transition_length=50%` fills the V-dents where single-bead letter strokes
  join (n/m/r/p shoulders, k). Text with strokes under ~0.85 mm prints as centrelines and will always round off a little.
- Box frames and other geometric linework: rebuild them as exact vector shapes (rounded rectangles plus offset rims),
  not traced pixels. Traced rims wobble even after smoothing.
- Stack colours in Z "bands" to control swaps: the face-up light→dark relief needs only 3 swaps for 4 colours.
- Mechanical parts on the same plate (see models/vampire-dial) can add **zero** swaps: give every part the
  same global Z bands, so each layer is still one filament. Lay several objects out as parts of ONE
  `--assemble` object; the slicer keeps their relative positions.

## Legibility at card scale (see models/vampire-counter)
- Traced raster art doesn't survive a 0.4 mm nozzle at card size. Draw the scene as vector shapes (painter's algorithm
  over 4 regions that tile the card) with outlines ≥ 0.7 mm, and absorb any island < 1 mm² into its neighbour.
- Dial digits: to hide both neighbours, a value W mm wide on a 9-position ring needs a ring radius of about 1.75·W.
  8 mm condensed "N/N" (12 mm wide) → r 21 → a Ø59 wheel, the most a 63 mm card can hold. Scale the slash to the digit height.

## Printing design rules of thumb
- Design parts to print flat on their largest flat face, with no supports. Keep overhangs at or under 45°.
- Snap/detent springs in PLA: keep the peak flex strain ≤ ~0.6 % (taper the cantilever, fillet its root, make the
  pocket wall an over-travel stop). For a detent that centres firmly, use V notches (~35° flanks) with a round nub
  seated on both flanks and 0.3–0.4 mm preload, not a small nub in a wide round scallop (see models/vampire-counter).
- Mating clearance: about **0.15 mm per side** for press- or slide-fit joints on the A1 (elephant-foot compensation is 0.075 mm by default).
- Place split seams in thick regions (e.g. on a crest rather than in a valley) for joint strength.
- For fabric-wrapped inserts, the model dimension is the bare core: subtract about 2× the fabric thickness plus clearance to fit a cavity.

## Preview images
`check_mesh.py --png` renders with matplotlib, and dark blotches on curved faces are
depth-sorting artifacts, not holes. Trust `open_edges`. View the PNG with the Read tool.

## Model index
| Model | Folder | Status |
|---|---|---|
| Wave jewelry-box insert (11.4×4.9×1", 5 waves + end ramps, 2 dovetailed halves) | `models/wave-insert/` | v4 sliced for A1 (1 plate) |
| Vampire token card, 4-colour AMS (63×88 mm; flat-light + relief layouts) | `models/vampire-token/` | v2 sliced for A1 |
| Vampire token with internal 1/1–9/9 dial wheel + detent (63×92×4.8 mm, 3 parts, 4-colour relief) | `models/vampire-dial/` | v1 sliced for A1 |
| Vampire counter: legible redesign, vector vampire-knight scene, 8 mm 1/1–9/9 dial (63×88×4.8 mm, 3 parts) | `models/vampire-counter/` | v1.2 sliced for A1 |
