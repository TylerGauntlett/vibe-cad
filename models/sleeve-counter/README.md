# Sleeve counter: a P/T counter that plugs onto a real, sleeved card

## Request
After the emblem counter (a full token card): "Consider one that allows sleeved cards to slide directly into the
base (covering the bottom of the card up to the card art). I mostly want the style of the art work (ie the clean
lines, nice color pallet, ect); it's not critical to have an exact matching look/mechanic of the counter itself."
- "i.e. a horizontal rectangle that covers the bottom half of a real mtg card with large number counters."
- An image of a real card with its text box outlined (about 57 × 27.5 mm, 5 to 32 mm above the bottom edge).
- "The goal here is to have the counter plug into a real mtg card. The 3d print should specifically be the
  counters, covering the text box and showing off the art from the original card."
- With the v1.1 preview attached (digit row along the top, woodcut scene below, block up to the card's art):
  "Remake using these styles. The main complaint I had with these is the font could be larger. Otherwise the
  style is great."
- "Create 5 additional options following similar design art work of the existing models." (v3.1: ship, storm,
  skull, castle, pines.)

## Spec (as built, v3.1)
| Parameter | Value |
|---|---|
| Block | **84.0 × 62.6 mm**, 3 mm corners, **9.2 mm** thick, plus 2.5 mm of wheel rim past the left and right edges |
| Card slot | 68.0 mm wide × 1.2 mm deep, open at the top, 40.0 mm tall: the block covers a sleeved card from its bottom edge to the foot of its art. Name and art stay in view. Takes sleeves up to 67 × 92 mm, single or double |
| Overhang | 22.6 mm of block below the card and 8.5 mm past each side of a 67 mm sleeve. A card with the counter on is 114 mm long |
| Back plate | 84.0 × 70.6 × 1.2 mm: it stands 8 mm above the block as a lead-in lip. Lay the card on it and slide down |
| Counter | power and toughness on **separate wheels, 0–9 each, 14 mm digits** (7.5 mm wide), in a row of five cells along the top: sword, power, slash, toughness, shield. On the card the digits sit 19 to 33 mm above its bottom edge |
| Display plate | 80.4 × 22.5 mm; windows 9.1 × 15.2 mm at (21.5, 49.4) and (62.5, 49.4) from the block's bottom-left corner |
| Art panel | 80.4 × 35.3 mm below the display, one woodcut scene per design |
| Wheels | as the emblem counter's, larger: Ø 57.7 mm, 1.6 mm thick, digit ring r 18.75, knurled rims. Power in front (rim out of the left edge), toughness behind (right edge). Push a rim **up** to count up. No detent |
| Depth of the digits | power 1.2 mm below the face, toughness 4.0 mm, its well bevelled 45° on the bottom side |
| Joints | back to tray: three ridges on the foot (1.2 × 0.6 mm; 40, 9 and 26 mm long) in grooves through the tray's roof, plus the glued rim. Tray to front: the emblem counter's tongue through the divider, here 7 dashes (80 mm) |
| Back | ink edge and an eight-point star |
| Material / printer | Bambu PLA Matte, A1 0.4 mm nozzle, 0.20 mm Standard + Arachne, slow first layer, Textured PEI |
| Plate | one per design, 174 × 203 mm: front and tray, then divider and back, then the two wheels |

### The ten designs
AMS order 1–4: lines, accent, accent, ground. The first five palettes are the emblem counter's; the second five
(v3.1) are this model's own (`MORE_DESIGNS`).

| Design | AMS 1 | AMS 2 | AMS 3 | AMS 4 | Print | Swaps (purge) |
|---|---|---|---|---|---|---|
| sun: rising between hills | Dark Chocolate | Terracotta | Caramel | Ivory White | 1 h 35 min, 50.0 g | 6 (2.1 g) |
| moon: crescent, stars, cloud bank | Charcoal | Ivory White | Caramel | Desert Tan | 1 h 36 min, 50.0 g | 6 (2.1 g) |
| tree: fruiting tree, two bushes | Dark Chocolate | Terracotta | Caramel | Desert Tan | 1 h 36 min, 49.9 g | 7 (2.1 g) |
| flame: fire in a footed bowl | Charcoal | Terracotta | Caramel | Ivory White | 1 h 34 min, 50.2 g | 6 (2.3 g) |
| mountain: range, sun and waves | Charcoal | Terracotta | Ivory White | Desert Tan | 1 h 38 min, 50.9 g | 7 (3.0 g) |
| ship: under sail on a swell, cloud, gulls | Dark Chocolate | Caramel | Ivory White | Desert Tan | 1 h 36 min, 50.4 g | 7 (2.5 g) |
| storm: thunderhead, three bolts, rain, dark hills | Charcoal | Ivory White | Dark Chocolate | Desert Tan | 1 h 35 min, 49.7 g | 6 (1.8 g) |
| skull: skull among six candles, rays | Charcoal | Ivory White | Terracotta | Caramel | 1 h 35 min, 50.2 g | 6 (2.3 g) |
| castle: keep and towers on a hill, road, poplars | Dark Chocolate | Terracotta | Ivory White | Desert Tan | 1 h 35 min, 50.0 g | 6 (2.1 g) |
| pines: firs in snow before a low moon, stars | Charcoal | Caramel | Dark Chocolate | Ivory White | 1 h 35 min, 50.3 g | 6 (2.4 g) |

No slicer warnings on any plate (only the open-frame bed-temperature advisory and the timelapse note). Nothing is printed yet: the slot fit and the card's hold are untested.

### Parts (z from the back face when assembled)
- **back** (printed as it sits): 0–1.2 plate with the back art; 1.2–2.4 the rim (two 8 mm side walls and the foot)
  that leaves the slot; three locating ridges on the foot.
- **tray** (printed as it sits): 2.4–3.2 the slot's roof, its top edge chamfered so a sleeve doesn't catch; 3.2–5.2
  spacer round the toughness cavity; the toughness pin; the tongue dashes.
- **toughness wheel** (face-down): 3.2–4.8.
- **divider** (printed as it sits): 5.2–6.0, with the power pin on top.
- **power wheel** (face-down): 6.0–7.6.
- **front** (face-down): 6.0–8.0 spacer, 8.0–9.2 face plate with the art and both openings.

### Assembly
1. Peel the parts. Front and wheels come off face-down. Clean any elephant foot off the wheel holes, pins, tongue
   dashes and ridges, and out of the grooves in the tray's underside.
2. Tray down, cavity up. Drop the **toughness** wheel on its pin, digits up. (On the plate the power wheel is the
   left one of the two, toughness the right.)
3. Divider on, over the tongue dashes and the pin. Drop the **power** wheel on the divider's pin, digits up.
4. Dry-fit the front, check both wheels turn, then glue: thin CA on the tray's spacer top, divider on; CA in the
   front's groove and on its spacer face, front on. Keep glue away from the wheels and pins.
5. Dry-fit the body on the back (ridges into the grooves, top edges flush). Then CA on the foot and along the two
   side walls only, and press the body on. **Keep glue out of the slot.**
6. Slide a sleeved card in from the top until it meets the foot.

## Decisions & interpretations
- **The style is v1.1's** (asked): the digit row of five cells along the top, a woodcut scene below, the block
  reaching up to the card's art. v2 (text box only, 10 mm digits, an emblem roundel) was dropped.
- **Larger font means a larger block.** The digits ride on wheels that are 4.2 × the digit height across. The
  block is the wheel plus 4.4 mm tall, and it has to be wide enough for the toughness well to miss the power
  wheel's cavity. So the digit stays about 22 % of the block's height whatever the size; only the absolute size
  can grow, and the block grows with it:

  | Digits | Block | Below the card | Past each side of a sleeve | |
  |---|---|---|---|---|
  | 12 mm (v1.1) | 72 × 55.5 | 15.5 | 2.5 | builds, passes the checks |
  | 13 mm | 78 × 59.1 | 19.1 | 5.5 | builds, passes the checks |
  | **14 mm** | 84 × 62.6 | 22.6 | 8.5 | built and sliced |
  | 15 mm | 84 × 66.6 | 26.6 | 8.5 | from the sizing study; 1.8 mm well wall, not built |

  I took 14 mm: the largest step that keeps a sound wall, 17 % taller than v1.1 and 36 % more digit area. For
  another size set `DIGIT_H` and `BLOCK_W` (or `$env:SLEEVE_DIGIT_H`, `$env:SLEEVE_BLOCK_W` for a trial build).
  12 mm is the most a 72 mm block holds.
- **What would make the digits a larger share of the block**: fewer values per wheel. A 0–7 wheel carries 14 mm
  digits in the v1.1 block (72 × 56.6). 0–9 was the range asked for, so this is not built.
- **The second five (v3.1) change only the scene and the spools.** Block, frame, digit row, mechanism and back are
  the first five's, part for part. The subjects are my choice (the request left them open): ship, storm, skull,
  castle, pines. Each uses four of the six Matte spools in a combination the first five don't, so the ten read as
  one set without two looking alike. Three points to know before printing:
  - **skull** has a Caramel ground: the whole block (about 50 g) and the wheels print in Caramel, with Charcoal
    digits. It is the dark one of the set: Charcoal on Caramel is 6.2:1 in contrast (swatch values), where the
    other nine grounds give 8.4:1 (Dark Chocolate on tan) to 21:1 (Charcoal on ivory).
  - **storm** and **pines** fill shapes in Dark Chocolate inside Charcoal outlines. The outline barely shows
    against the fill (1.8:1), by intent: the cloud, hill and firs read as dark silhouettes.
  - Their palettes live in `MORE_DESIGNS` in this model; the first five's stay in the emblem counter.
- **The scenes scale with the panel.** They are drawn for a 68 × 30 mm panel and scaled (here × 1.16); outlines
  and halos keep their printed widths, strokes and hatching grow with the scale.
- **The digits sit above the wheels' centres** (`layout_up()` turns the emblem counter's layout over), so they are
  over the card's text box and the lower halves of the wheels are behind the scene.
- **Same mechanism as the emblem counter**, re-sized (`ec.configure`). The two windows sit level, with 3.8 mm of
  wall between the toughness well and the power cavity.
- **The pocket is two parts.** A 68 mm slot can't be bridged, so the back plate carries the rim and the tray's base
  is the roof. The tray's grooves are cut only where it is solid above the roof, so none opens under the wheel.
- **A plain slot, no clip.** The card is held by the slot and its own weight: fine lying on a table and when moved
  by the block. Lifted by the card alone, the block can slide off. `SLOT_T` (1.2 mm) sets the grip; 1.0 mm would
  hold a single-sleeved card more firmly but may not take double sleeves.
- **Lead-in lip** (my addition): the back plate is 8 mm taller than the block, and the roof's edge is chamfered.
- **Thickness**: 9.2 mm, of which 2.4 mm is behind the card. The card lies 1.2 mm off the table at the block.
- The type line is covered (`COVER` 40 mm, as in the style asked for). `COVER = 33.5` would leave it showing and
  add 6.5 mm to the overhang below the card.

## Printing
- Use a clean Textured PEI plate: the whole face is the first layer.
- The plates are sliced with the **prime tower off**. If you switch it on in Bambu Studio, the parts are already
  placed 6 mm clear of the tower's spot (left rear of the bed), so it slices without the "conflicts of gcode
  paths (WipeTower <-> Assembly)" warning. Don't re-arrange the plate afterwards, or move the tower if you do.

## Checks the build runs
- The emblem counter's design checks and its `assembly_check()` on the body **as printed**: tongue 0.15 mm inside
  the divider's slots and the front's groove, pins in their sockets, hubs 0.4 mm, each wheel clear of its cavity,
  all ten values of both wheels centred in the aperture the printed parts leave.
- The pocket: ridges 0.2 mm inside grooves that the tray's spacer roofs over; no hole in the slot's roof; the slot
  is 68.0 mm wide from the foot up; a 67 × 92 mm sleeve clears the rim by 0.5 mm each side.
- The digits land over the covered part of the card (18.8–32.8 mm up it).
- `check_mesh.py`: all 390 STLs (39 per design) have `open_edges=0` and fit the bed.
- Adding the second five left the first five's 195 STLs byte-identical (SHA-1 compared before and after).

## Files (`out/`)
- `sleeve_counter_<design>_A1.3mf`: the sliced plate for each design. Open it in Bambu Studio, load the four
  spools in the order above, and print from there.
- `<design>/`: the part STLs (`<object>_<n>_<slot>.stl`, mm, laid out as printed) and `slice_args.txt`.
- `designs_preview.png`: the ten counters, each on a stand-in card.
- `<design>_preview.png`: one face at larger scale, with a nozzle simulation.
- `parts_preview.png`: back, tray, divider, front underside, and a section through the slot.
- `text_cache.json` (next to the script): the digit outlines, for builds without the Windows font.
- No STEP: the parts are shapely polygons extruded into meshes, as in the other card models.

## Rebuild
```powershell
.venv\Scripts\python.exe models\sleeve-counter\sleeve_counter.py          # all ten; or name designs: ... sun ship
cd models\sleeve-counter\out\sun
..\..\..\..\.venv\Scripts\python.exe ..\..\..\..\tools\check_mesh.py (Get-ChildItem *.stl).Name
$a = Get-Content slice_args.txt
Invoke-Expression "python ..\..\..\..\tools\slice_bambu.py $a -o ..\sleeve_counter_sun_A1.3mf"
```
Imports `models/emblem-counter/emblem_counter.py` (wheels, windows, tongue, drawing helpers, palettes, plate
writer). Rebuild this model after changing that file.

## History
- 2026-11-22: v1. A 72 × 55.2 × 9.2 mm block covering the card up to its art (40 mm), 12 mm digits in a row along
  the bottom, a woodcut scene panel above. v1.1 moved the digit row to the top, over the text box.
- 2026-11-22: v2 (dropped): text box only (33.5 mm), 72 × 48.4 mm, 10 mm digits, an emblem roundel between the
  numbers in place of the scene.
- 2026-11-22: v3, after "remake using these styles [v1.1] ... the font could be larger": v1.1's layout with
  **14 mm digits**; the block grows to 84 × 62.6 mm and the scenes scale with their panel. Each plate about 1 h 36 min, 50 g, 6-7 swaps; no slicer warnings.
  Not printed yet.
- 2026-11-22: re-sliced after "conflicts of gcode paths (WipeTower <-> Assembly)" appeared in Bambu Studio with
  the prime tower switched on. `slice_bambu.py` now moves the parts clear of the tower's spot: here 18 mm to the
  right, 6 mm clear. Geometry, times and weights unchanged.
- 2026-11-22: v3.1, after "create 5 additional options following similar design art work": five more faces on the
  same block and frame (**ship, storm, skull, castle, pines**), each in a new four-spool palette. The first
  five's STLs are byte-identical. Each new plate about 1 h 35 min, 50 g, 6-7 swaps; no slicer warnings. Not printed.
