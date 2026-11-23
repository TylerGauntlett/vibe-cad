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
  slice_bambu.py        STL(s) -> sliced A1 .3mf via the installed Bambu Studio (incl. multi-colour AMS; 0.4 nozzle defaults)
  filaments.py          spools on hand (name, hex, Bambu preset) + named card palettes (vampire cards)
  palette_sheet.py      compare a vampire card's per-palette previews on one sheet
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
- **Bambu Lab A1**: 256 × 256 × 256 mm build volume, open frame (no enclosure), **0.4 mm nozzle**
  (back to 0.4 on 2026-11-21; the 0.2 nozzle phase is in git history). Machine preset **Bambu Lab A1 0.4 nozzle**.
- Bed: **Textured PEI Plate** (the A1's stock plate), with PLA at 65 °C.
- Filament: **Bambu PLA Basic @BBL A1**. Process: **0.20mm Standard @BBL A1**. These are
  `slice_bambu.py`'s defaults (also the `SLICER_PRESETS` in the vampire models).
- Heights: 0.2 mm layers, so a 0.4 mm face-down colour inlay is 2 layers. Models built for 0.10 mm layers
  were rebuilt for 0.4 on 2026-11-21; all their heights are already multiples of 0.2 mm.
- Art rules: beads ≥ 0.45 mm wide, islands ≥ 1 mm² (see the legibility sections below).
- Spools on hand, besides the Basic black/red/copper/white: six **Bambu PLA Matte** tan/brown colours: Ivory White,
  Desert Tan, Caramel, Terracotta, Dark Chocolate, Charcoal. The names, hex values and palettes are in `tools/filaments.py`.
- Parts larger than about 250 mm on any axis must be split; a part can also be rotated
  diagonally. Put each oversize half on its own plate (the slicer arranges this automatically).

## Environment (Windows 10, PowerShell)
Cloud (Linux) sessions also happen. They have no Bambu Studio (so no slicing: leave the 3MF to be regenerated on
the PC and say so) and no Windows fonts. Models that set text in Windows fonts cache the outlines in
`models/<slug>/text_cache.json` (`vampire_dial.text_cache()`): a build without the font uses the cache, and a
build with it refreshes the cache. Check that a fontless rebuild leaves the art STLs unchanged (volumes match).

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
- With the tower off the CLI centres the parts and ignores the tower's stored spot (35 mm wide at x 15, y 220, left
  rear; y 200.5 if the CLI arranged the plate). A plate that reaches it fails in the GUI once the tower is switched on:
  "Conflicts of gcode paths ... (WipeTower <-> Assembly)". `slice_bambu.py` now checks this for `--assemble` jobs: it
  keeps the assembly where pass 1 put it (`--arrange 0`), and if the parts' box is within 6 mm of the tower zone it
  shifts the build item's transform and slices again. Look for the `tower   :` line. A plate needs about 60 mm of free
  bed width (or 45 mm of depth) for this to work, so don't fill the bed edge to edge.
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
  The user wants power and toughness on **separate wheels** (one digit each, rims out of the left and right edges).
  A single 8 mm Bahnschrift digit needs r 11.2 → a Ø36.8 wheel, so two need a 70.5 mm card (vampire-counter v4).
  Pushing a rim up counts up, so the left wheel's digits run the other way round.
  8 mm condensed "N/N" (12 mm wide) → r 21 → a Ø59 wheel, the most a 63 mm card can hold. Scale the slash to the digit height.
  That leaves no room past the digits: for a bottom-edge thumb rim plus a bevelled window the cards use 7.5 mm digits (r 19.75).
- Woodcut/engraved style (see models/vampire-arcana): black line art on white plus ONE accent reads far clearer than flat
  4-colour fills. On a 0.4 nozzle, strokes of 0.55 at 1.25 pitch, outlines 0.7. Print it **face-down as a 0.4 mm flat inlay**:
  every swap is in layers 1–2 (4 colours → 6 swaps), however much ink the art has.
- Hatching against outlines leaves sub-bead white slivers. Clear a ~0.7 mm white halo around shapes drawn over line fields,
  snap shapes to the line grid, then merge what's left into its neighbour. After many painter's-algorithm booleans, snap
  the final regions (`set_precision` 0.5 µm, then grid 0), or later booleans and `vt.extrude` throw TopologyExceptions.

## Face-down / multi-part print transforms
- Mirror only parts that print **face-down** (front, wheel). A part printed on its back with the working side up
  (the counter's back: cavity up) is already in the front-view frame, so mirror only its back-face art. A mirrored
  back with symmetric pegs still assembles, but the wheel moves to the other side and the window lands off-detent.
- Design-frame asserts can't see a wrong print transform. Re-assemble the parts **as written** (flip, seat on the
  printed pin) and check the result (models/vampire-counter `assembly_check()`).

## Layered (shapely-extruded) parts (see models/token-dock)
- Keep one STL per z band. `check_mesh.py` welds vertices, so stacked prisms in one file share edges four ways and
  read as open edges.
- A 45° face is a stack of one-layer prisms, each stepped 0.2 mm: the print is identical to a true bevel. Use it
  for a lap joint between two face-down parts (both print without support) and to bevel a deep window.
- A window deeper than ~2 mm hides the digits' bottoms when read at 45°. Bevel it out toward the face and keep
  under 1 mm of straight wall above the digits.
- Check a multi-part stack by rebuilding it from the printed bands and intersecting every pair of parts in every
  shared z range (`assembly_check()`), plus a side-section plot.
- Showing 1 of N values by sliding needs (2N−1) pitches of run; by a rack on a printable pinion (r ≥ ~4 mm) about
  45 mm for 9 steps. At card size, only a wheel shows 7.5–8 mm digits.
- A 9-value "N/N" ring needs r ≈ 2.63 × digit height (8 mm → 21, 7.5 mm → 19.75) with the window straight below the axle.
- Thumb rim through an edge: the rim must clear the window by bevel + a 3-bead frame strip + the protrusion, so the
  window sits ~8 mm in from that edge. With 9 notches, put the detent 160° from the exposed spot so a notch rests there.
- The dial (wheel, detent, window, checks) lives in `models/vampire-counter/vampire_counter.py`. arcana, cathedral and
  token-dock all import it, so after a change rebuild all four and compare STL hashes for the ones meant to stay put.

## Large digits at card size (see models/emblem-counter)
- A 0–9 digit wheel is about 4.2 × the digit height across (ring r = 1.35 × height for Bahnschrift Bold Condensed).
  Two side by side cap at ~7 mm digits on a 63 mm card (8 mm needed the 70.5 mm card).
- **Overlap the wheels on two levels** to reach 12 mm at 63 mm wide: power in front (left rim), toughness behind
  (right rim) with a divider plate between. The rear window must miss the front wheel's cavity by a wall (1.6 mm), so
  the front wheel sits ~11 mm higher and the digits read as a diagonal fraction that fills a 59 × 29 mm "text box".
  With both windows in a row the same stack caps at 10 mm; at 13–14 mm the digits end up nearly one above the other.
- The rear digit is ~4.4 mm below the face: bevel its well's bottom side 45° through plate and spacer (stacked
  one-layer prisms), and dock the window boxes to the plate's border so the bevel has room.
- One tongue can locate three layers: stand it on the back, pass it through slots in the divider (dash it, with
  bridges, so the divider stays in one piece) and end it in the front's groove.
- The mechanism lives in `models/emblem-counter/emblem_counter.py`; `models/sleeve-counter` re-sizes it with
  `ec.configure(CARD_W=..., CARD_H=..., ...)`. After changing it, rebuild both and compare the emblem STL hashes.
- A slide-in card pocket (models/sleeve-counter) can't be bridged (68 mm), so it is a back plate with a U rim, glued
  under a tray whose base is the slot's roof.
- A counter that sits over a real card must have its wheels in front of the card, so the block is 2R + 4.4 tall
  (digit = 22 % of it) and whatever exceeds the covered part of the card hangs below it. Two-level wheels in a row also
  need width: 72 mm for 12 mm digits, 78 for 13, 84 for 14. Say so before building: "larger font" means a larger block.
  Put the windows ABOVE the wheel centres (`layout_up()`), or the digits end up below the card.
- What the user liked for the plug-on counter: the digit row of five cells along the top with a woodcut scene below
  (v1.1/v3). They rejected a text-box-only block with an emblem roundel (v2) after asking for "just the counters".
  Show a preview before re-slicing a restyle.
- A new face for the plug-on counter is one scene function plus a `MORE_DESIGNS` entry (four spools) in
  `sleeve_counter.py`; registering it in `ec.DESIGNS` at import leaves emblem-counter untouched. Build new faces with
  `$env:SLEEVE_OUT` set to a scratch folder first, then check the older faces' STL hashes after the real build.
- Sliders cannot show a large digit (a strip needs 2N−1 pitches of run). A 7-segment mask over a sliding or turning
  pattern needs 10 patches per segment in each track, which comes out no smaller than a digit wheel.

## Print-in-place mechanisms (see models/duo-travel-stand)
- Nest the moving bodies side by side in ONE slab (2.5D) so nothing prints over a gap. Gaps: 0.5 mm in plan,
  0.4 mm between knuckles, 0.4 mm radial pin-to-bore.
- Horizontal hinge: knuckle = circle + 45° foot (starts on the bed), pin with a flat underside on a layer line and
  3 layers above the bore floor, bore roof a truncated teardrop, pin bridges ≤ ~10 mm between the knuckles it joins.
- A hinge at mid-thickness folds only ±90°. A strut folded back into its panel swings through "straight down" on
  its way out, so its length must be under the hinge height with the panel upright.
- Anything near a hinge sweeps a circle about it: check the opening sweep with every body, not only the hinged one
  (the folded leg's foot hit the base shoulder at 90°). Leave detent nubs out of the pass/fail: they interfere by design.
- A flat-bottomed barrel has corners at 1.08 × R: give a cradle that seats it R + 0.5.
- `a.distance_to(b)` gives the true minimum gap between bodies; use it next to `a & b`.

## Printing design rules of thumb
- Design parts to print flat on their largest flat face, with no supports. Keep overhangs at or under 45°.
- Snap/detent springs in PLA: keep the peak flex strain ≤ ~0.6 % (taper the cantilever, fillet its root, make the
  pocket wall an over-travel stop). For a detent that centres firmly, use V notches (~35° flanks) with a round nub
  seated on both flanks and 0.3–0.4 mm preload, not a small nub in a wide round scallop (see models/vampire-counter).
- Mating clearance: about **0.15 mm per side** for press- or slide-fit joints on the A1 (elephant-foot compensation is 0.075 mm by default).
- Glued sandwich parts: join them with a **tongue and groove** round the edge, not pegs (see `vampire_dial.edge_tongue()`):
  a 1.2 × 0.6 mm ridge 2 mm in from the edge, broken where it nears a cavity, in a groove 0.15 mm per side wider and
  0.2 mm deeper. A thin line of CA in the groove.
- Spinning wheels on an axle pin: **0.4 mm radial hub clearance** (0.25 was too snug). A wheel in a snug cavity holds
  its value by friction, so the user doesn't want a spring detent (it's a failure point).
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
| Vampire token with separate power + toughness wheels, 1–9 each (63×92×4.8 mm, 4 parts, 4-colour relief, tongue-and-groove) | `models/vampire-dial/` | v3 rebuilt + sliced for 0.4 nozzle, not printed |
| Vampire counter: flat-colour alt art of vampire-arcana (same frame, title, P/T wheels, back; 70.5×88 mm); hosts the shared frame + mechanism | `models/vampire-counter/` | v4 rebuilt + sliced for 0.4 nozzle, not printed |
| Vampire arcana: woodcut-tarot restyle of the counter (ink on white, gold moon, blood accents), face-down flat inlay; imports the counter's frame | `models/vampire-arcana/` | v3 rebuilt + sliced for 0.4 nozzle, not printed |
| Vampire cathedral: rule-based blend of the two (flat colour for cloth/glass/gold, woodcut for skin/hair/steel/stone): counter's red cloak, arcana's armour, merged sword, spiked crown, red-lined collar, engraved nave, gold rose window; imports arcana's knight parts + counter | `models/vampire-cathedral/` | v4 (two-wheel 70.5 mm card) sliced for A1, not printed |
| Token dock: reusable 1/1–9/9 counter base (bottom-edge thumbwheel, bevelled window, 63×69.4×6 mm, same width as the card) + swappable flat 63×88 token cards (cleat toe, 2 magnet bosses, Ø6×2 magnets); imports arcana's scene + counter's dial (same wheel as the one-piece cards) | `models/token-dock/` | v1.2 sliced for A1 (base plate + arcana card plate), not printed |
| Emblem counter: generic P/T token with **12 mm digits**, 0–9 each, on two overlapping wheels (power in front, left rim; toughness behind, right rim), read as a diagonal "7 / 5" across the text-box area; 63×88×6.6 mm, 5 parts; five woodcut faces (sun, moon, tree, flame, mountain), each in 4 of the 6 Matte tan/brown spools; uses arcana's drawing helpers; hosts the two-level wheel mechanism (`configure()` re-sizes it), which sleeve-counter imports | `models/emblem-counter/` | v1 sliced for A1 (5 plates), not printed |
| Sleeve counter: P/T counter that **plugs onto a real sleeved card** (the card slides into a slot in its back); an 84×62.6×9.2 mm block covering the card up to its art (40 mm), 22.6 mm below it; **14 mm digits** 0–9 in a row of five cells along the top (sword, power, slash, toughness, shield), a woodcut scene below: ten faces (sun, moon, tree, flame, mountain in emblem-counter's palettes; ship, storm, skull, castle, pines in its own `MORE_DESIGNS`); 6 parts (back with slot rim and lead-in lip, tray, divider, front, 2 wheels); imports emblem-counter's mechanism | `models/sleeve-counter/` | v3.1 sliced for A1 (10 plates), not printed |
| iPhone Duo travel stand: one 8 mm print-in-place slab (122×110 mm) that unfolds into panel + prop leg + base; Ø56×7 puck behind a front lip, offset for the unfolded Duo; 60–73° | `models/duo-travel-stand/` | v1 sliced for A1, not printed |
