# Vampire arcana token

## Request
"models/vampire-counter is a new simplified approach to the token. Iterate on this further by creating a new vampire
token themed similarly to those found in https://makerworld.com/en/models/1809406-token-arcana-tarot-inspired-custom-token-set.
Stand-out features: images offer great visual clarity with impressive detail; good use of space around the name;
simple borders. How might this vampire be transformed into something similar?"

What the reference does (13 gallery photos and the description, 2026-11-12):
- French woodcut tarot style: **black line art on white**, shading done with hatching, and **one accent colour**
  per card (red blood, a gold coin or sun, a blue plume).
- A white title plate at the top in roman caps with generous margins, the art panel below, and simple black borders.
- The image is printed **face-down on the plate** (smooth face, flat inlay). The author used a 0.2 mm nozzle; for a
  0.4 mm nozzle they advise a slow, clean first layer at a 65 °C bed.

## Spec (as built)
| Parameter | Value |
|---|---|
| Card | 63 × 88 mm, 3 mm corners, **4.8 mm** assembled (back 2.8 + front 2.0), same as vampire-counter |
| Layout | black card edge 1.8 mm, black rules 1.2 mm; white plates: title 12.4 mm, art 53.4 mm, footer 16.2 mm |
| Title | "VAMPIRE", **Georgia Regular, 6.0 mm caps**, black on white, 45.9 mm long in a 59.4 mm plate |
| Art | original woodcut of the vampire-counter knight: white hair with black strands, a gaunt face with red eyes, outlined armour with engraved shadow hatching, a black cloak with white folds, and a sword with blood running down the fuller. Behind him: a gold moon with 28 rays, an engraved sky, scalloped clouds, bats and castle towers |
| Dial | the vampire-counter v1.2 wheel and detent, unchanged: 1/1 … 9/9, 8 mm digits, window in a ruled box in the footer, a bat either side |
| Colours | 1 ink `#1E1A18`, 2 blood `#9B1B1E`, 3 gold `#B87333` (copper/gold silk), 4 paper `#F4F1EA` (white) |
| Inlay | **face-down**, 0.4 mm (2 layers) of colour; everything above is paper |
| Line rules | outlines 0.7, strands and hatching 0.55 at 1.25 pitch (every white gap ≥ 0.7), islands ≥ 1 mm² |
| Back | black edge plus a gold crescent and bat, inlaid in the same 2 layers (no extra swaps) |
| Material / printer | Bambu PLA Basic, A1 0.4 mm, 0.20 mm Standard + Arachne (vampire-counter `SLICER_SET`), first layer 30 mm/s walls and 60 mm/s infill, Textured PEI (65 °C) |
| Plate | 1: front, back and wheel side by side (one object, 17 parts) |
| Print | **1 h 06 min, 28.6 g, 6 filament swaps (~2.2 g purge)**, no slicer warnings |

## Decisions & interpretations
- **Scene: the vampire-counter knight, re-inked** (the scene question went unanswered, so this is the default). It is
  the most direct answer to "how might *this* vampire be transformed". The other options were an enthroned lord
  raising a goblet, or a large bust under the moon.
- **Dial kept** (asked). The window becomes a tarot-style ruled box in a footer plate that mirrors the title plate.
- **0.4 mm nozzle** (asked). Every black line is at least one bead and every white gap at least one bead, so
  hatching can't be finer than ~1.2 mm pitch; the reference's ~0.5 mm hatching needs a 0.2 mm nozzle. The detail
  comes from more, larger elements (rays, clouds, lames, strands) rather than finer lines.
- **Art drawn in code** (asked): outlines plus procedural hatching (`hatch()`), each stroke sized for the nozzle.
- **Colour discipline, as in the reference**: black on white does the drawing. Gold marks the one focal object (the
  moon, behind the head like a halo) and the hilt. Red is only blood: the eyes, the pommel gem and the blood on the blade.
- **Face-down flat inlay instead of the counter's relief**: a smooth face and crisp edges, and every swap happens in
  layers 1–2 however much ink the art has (6 swaps, against 3 for the relief). The wheel also prints face-down
  (digits inlaid flat), and the back's face gets art in the same two layers for free.
- **Clean-up rules that kept the woodcut printable**:
  - Shapes drawn over the sky lines (towers, bats) clear a 0.7 mm white **halo**, so lines stop a bead short of
    them instead of grazing them.
  - Cloud bases snap to the sky-line grid, so the cloud outline swallows one line and the next is a full gap below.
  - Armour shading is the engraver's kind: only the strip of each lower lame that shows under the next is hatched.
  - What is still narrower than a bead, where a hatch stroke meets an outline at a shallow angle (~19 mm² in
    total), goes to its neighbour (`fill_slivers()`), as woodcut lines run together.
- **Georgia Regular** for the title: of the installed romans, it is closest to the reference and keeps 99.8 % of its
  ink in the nozzle simulation (Palatino and Times Regular lose 4–5 % at their hairlines).
- Tunables: `MOON_COLOUR` (`BLOOD` for a blood moon), `PITCH` / `LINE` (hatching density), `TITLE_CAP`,
  `TITLE_TRACK`, `INLAY`, `BACK_ART`; the scene's placements are in `front_regions()`.

## Printing
- Use a **clean** Textured PEI plate (wash it with dish soap). The whole face is the first layer, and tiny ink islands
  need to stick.
- Open `out/vampire_arcana_A1.3mf` in Bambu Studio, map slots 1–4 to black, red, copper (or gold silk) and white,
  and print from there.
- If ink strokes come out ragged, slow the first layer further (`initial_layer_speed=20`, the reference's advice).

## Assembly
1. Peel the parts off. The front and wheel come off face-down; turn them over.
2. Clean any elephant foot off the wheel's rim and hole.
3. Fit the wheel onto the back's pin, digits up, with "1/1" at the bottom so a notch sits under the nub. Check that
   it clicks through all 9 values.
4. Put CA on the 6 pegs only and press the front on.

(The mechanism notes are in `models/vampire-counter/README.md`.)

## Files (`out/`)
- `vampire_arcana_A1.3mf`: the sliced A1 project, 4 AMS slots.
- `parts/`: 17 colour-part STLs (`<front|back|wheel>_<n>_<colour>.stl`, mm, mirrored and laid out as printed)
  plus `slice_args.txt`.
- `arcana_preview.png`: the face at 1/1, 5/5 and 9/9, a nozzle simulation, and the back.
- `arcana_detail.png`: the head, hilt and blade at print scale, plain and nozzle-simulated.
- No STEP: the parts are shapely polygons extruded into meshes, as in vampire-counter.

## Rebuild
```powershell
.venv\Scripts\python.exe models\vampire-arcana\vampire_arcana.py
cd models\vampire-arcana\out\parts
..\..\..\..\.venv\Scripts\python.exe ..\..\..\..\tools\check_mesh.py (Get-ChildItem *.stl).Name
python ..\..\..\..\tools\slice_bambu.py <contents of slice_args.txt> -o ..\vampire_arcana_A1.3mf
```
Imports `models/vampire-counter`, which holds everything the two cards share: the frame (plates, rules, title,
dial footer), the back, the mechanism, the face-down build and the preview sheet. This file is only the woodcut
scene; vampire-counter is the same card with flat-colour alt art.

## History
- 2026-11-12: v1, woodcut-tarot restyle of vampire-counter v1.2: flat face-down inlay, white title, art and
  footer plates, the knight re-inked with hatching, a gold moon and blood accents. 1 h 06 min, 28.6 g, 6 swaps, no warnings.
- 2026-11-12: frame, back and build moved into vampire-counter (shared with its alt art); output byte-identical.
- 2026-11-12: v1.1, dial alignment fix (in vampire-counter's shared `write_plate()`): the back was printed mirrored,
  so the wheel sat on the wrong side and the value stopped ~0.6 of a step off the window at every detent. Only the
  back art is mirrored now, checked by `assembly_check()` on the parts as printed. 1 h 06 min, 28.6 g, 6 swaps.
  **Reprint the back** (front and wheel are unchanged).
