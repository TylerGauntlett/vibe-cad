# Vampire counter token

## Request
After a photo of the printed `models/vampire-dial` token: "much of the [art] is visually hard to understand or
read. The numbers in the counter are far too small to read, title and sub title text too small, and image unclear
compared to details on the source photo. Instead of producing a like magic card, reimagine this token visual and
functionality": clear card art in the 4-colour palette, a 1/1 counter dial, simple "vampire" labelling, and all
text large enough to read easily. Follow-up: "The vampire face looks cheesy. How would it be modeled more like
Edgar Markov (a vampire knight)".

v2: "vampire-arcana provides a cleaner iteration on the vampire token counter made in vampire-counter. I'd like to
keep decisions like typography and borders, then port those learnings back into the vampire-counter model so that
it functions as an alt artwork primarily." So this card is now the **flat-colour alt art of vampire-arcana**: the
same frame, type, dial footer, print method and back, with only the art plate differing.

## Spec (as built)
| Parameter | Value |
|---|---|
| Card | 63 × 88 mm (standard token size), 3 mm corners, **4.8 mm** thick assembled (back 2.8 + front 2.0) |
| Frame (shared with arcana) | black card edge 1.8 mm, black rules 1.2 mm; white plates: title 12.4 mm, art 53.4 mm, footer 16.2 mm |
| Title (shared) | "VAMPIRE", **Georgia Regular, 6.0 mm caps**, black on the white title plate, 45.9 mm long in a 59.4 mm plate |
| Dial | one wheel, 9 positions × 40°: **1/1 … 9/9**, click detent at each value |
| Digits | Bahnschrift Bold Condensed, **8.0 mm** tall, slash cut to digit height, black inlaid flat in the white wheel |
| Window (shared) | 13.7 × 9.3 mm at (32.4, 10.2), in a ruled box (0.7 white mat + 0.7 black rule) in the footer, a bat either side |
| Wheel | Ø 58.9 mm, digit ring r 21, 9 **V notches** (1.3 deep, 35° flanks, 0.6 mm rounded edges); the rim pokes **2.5 mm** out of the right edge |
| Detent | 26 mm cantilever tapered 1.4 → 2.2 mm, R 3 root fillet, Ø2 nub on both notch flanks with 0.4 mm preload. Holds **0.40 N** seated and 1.47 N over the rim at **0.52 %** peak strain; the pocket wall stops it at 0.73 % |
| Turning | push the rim **up** to count up |
| Art (this card's own) | flat-colour vector scene: an elder vampire knight (long white hair, pointed beard, layered pauldrons with copper edges, gorget, red cloak, sword planted point-down) before a **blood moon**, with copper cloud streaks, bats and a black castle with red lancet windows |
| Colours (shared) | 1 ink `#1E1A18`, 2 blood `#9B1B1E`, 3 gold `#B87333` (copper), 4 paper `#F4F1EA` (white): the same spools as v1 |
| Inlay (shared) | **face-down**, 0.4 mm (2 layers) of colour on front, back and wheel; everything above is white |
| Back (shared) | black edge plus a gold crescent and bat, inlaid in the same 2 layers |
| Material / printer | Bambu PLA Basic, A1 0.4 mm, 0.20 mm Standard + Arachne, first layer 30 mm/s walls and 60 mm/s infill, Textured PEI (65 °C) |
| Plate | 1: front, back and wheel side by side (one object, 17 colour parts) |
| Print | **1 h 04 min, 29.1 g, 7 filament swaps (~2.6 g purge)**, no slicer warnings |
| Model grams per slot | ink 1.45, blood 0.27, gold 0.28, paper 28.96 (solid volume; 15 % infill makes the real total lower) |

### Mechanism
Same sandwich as `models/vampire-dial`, scaled up:
- **Back**: 0.6 mm plate + 2.2 mm spacer with the wheel cavity (0.4 mm radial clearance), a Ø6 axle pin, 6 Ø2
  alignment pegs, and the detent arm on top of the wheel, running left. The arm stands free over a slot through the
  plate. The pocket around it doubles as an over-travel stop.
- **Wheel**: a flat 1.8 mm white disc with the digits inlaid black in its face (printed face-down).
- **Front**: printed face-down: the 0.4 mm colour inlay, white above it, the window cut through, sockets underneath.

### Assembly
1. Peel the three parts off the plate. The front and wheel come off face-down; turn them over. Clean any elephant
   foot off the wheel's hole and rim.
2. Hold the wheel digits up with "1/1" at the bottom, so a notch sits at the top under the nub. Lower it onto
   the pin. If the nub catches, lift the arm's tip outward by about 0.5 mm; the pocket wall stops it before it over-bends.
3. Check the wheel clicks through all 9 values, then return it to 1/1.
4. Lay the front on so the pegs and pin enter its sockets. Put a drop of **CA on the 6 pegs only**, then press flat.

## Decisions & interpretations
### v2: alt art of vampire-arcana
- **One frame, two arts.** Everything the cards share lives in `vampire_counter.py`: palette, plates and rules,
  Georgia title, ruled window box with footer bats, back, mechanism, face-down build, sliver/island clean-up and
  preview sheet. `models/vampire-arcana` imports it. Each card is only its scene in the art plate
  (`front_regions()`), so a frame change lands on both. After the move, arcana's 17 STLs were byte-identical.
- **Kept from arcana**:
  - Georgia Regular 6.0 mm caps, black on a white plate. They replace Cambria Bold 6.8 mm in cream on a black bar.
  - A 1.8 mm black card edge and 1.2 mm black rules. They replace the copper rims.
  - The dial window as a ruled box in a footer plate, with a bat either side. It replaces the mat on a black field.
  - The back, and the face-down 0.4 mm flat inlay with a slow first layer.
- **Kept from the counter**: the flat-colour scene, which is what makes it the *alt* art:
  - a red blood moon (arcana: a gold moon) and a red cloak (arcana: black);
  - copper streaks for cloud (arcana: engraved lines) and a solid black castle.
  The colours are the same four spools, so the previews now use arcana's hex values.
- **Refit to arcana's art plate** (1.8–61.2 × 19.2–72.6, against 4–59 × 18.2–71.4 before):
  - the scene moved up 1.2 mm, and the streaks and castle now run off the plate edges;
  - the cloak flares to ±31.5, so it fills the plate's lower corners;
  - the plate's bottom edge cuts across the chest at local y −31, so the two fauld seams became one at −30.0. The
    upper seam had left a 0.2 mm black wedge against the quillons (2.3 mm² of sub-bead ink).
- **Swaps: 3 → 7.** The relief's Z bands gave 3 light→dark swaps. The flat inlay puts every colour in layers 1–2,
  so it costs 4 more swaps (~2 g more purge, ~11 min more). In return the face is smooth, the colour edges are
  crisp, and the card matches arcana. No island is under 1 mm², and the only sub-bead ink is the Georgia serifs,
  the same as on arcana.

### v1.x
- **Shape: card + side wheel** (asked; the other option was a Ø70 round medallion). The card keeps sleeve and
  playmat size.
- **Art: new vector scene** (asked; the alternatives were an enlarged crop of the old art or a single icon).
  Drawn in code (`knight()`, `front_regions()`), so every shape is a deliberate size: outlines and strands ≥ 0.7 mm, rims
  0.8 mm, and no island under 1 mm² (`absorb_islands()` merges any leftover sliver into its neighbour). What
  `printability()` still reports as "thinner than a bead" is corner rounding at sharp tips.
- **Knight, not Dracula (v1.1)**: the first figure (slicked widow's peak, bared fangs, pointed collar) read as a costume.
  It is now an original elder vampire knight in the Edgar Markov spirit, the archetype and not the card's art:
  - armour (lamed pauldrons with copper edges, a gorget, a breastplate) replaces the cape;
  - long white hair with black strands frames a stern face: heavy level brows, narrow red eyes, a moustache and a
    pointed beard, mouth closed;
  - a sword planted before him (copper-wrapped grip, red pommel gem) gives the figure a vertical axis.
  - Black linework separates touching cream shapes (hair, face, beard), like a woodcut.
- **Big digits drive the layout.** To hide both neighbours, a value 12 mm wide needs a digit ring of radius ≥ 21 mm
  (searched), so the wheel is ~59 mm across. It sits under the lower card, and only the window shows. The slash is
  scaled to the digit height: its natural overshoot would make the window, and so the wheel, bigger. At 8 mm the
  wheel only just fits: the rim pokes 2.5 mm out of the right edge, and the cavity is 6 mm from the left edge.
- **Window a little left of straight down** (`WIN_ANGLE` −100°), so it sits near the card's centre line (32.3 vs 31.5).
- **The type line is dropped.** "VAMPIRE" is the only text, so it can be large.
- **Zero extra swaps** (v1.x, superseded by the v2 flat inlay): every part used the relief Z bands (cream 0–1.0, tan 1.0–1.2, red 1.2–1.6, black 1.6+),
  so each layer is one filament. That makes 3 swaps, all light → dark.
- **Stronger, firmer detent (v1.2)**, after "can the stopping mechanism be strengthened so it is less brittle?" and
  "enlarged so there is less wiggle room when not fully spinning to the next number". `arm_mechanics()` prints the
  numbers for a tapered cantilever under a tip load, with E = 3.5 GPa:

  | | v1.1 | v1.2 |
  |---|---|---|
  | Arm | 15 × 1.0 mm, square root | 26 mm, 1.4 → 2.2 mm taper, R 3 root fillet |
  | Peak strain riding over the rim | 1.07 % | **0.52 %** |
  | Strain at the over-travel stop | (no stop) | 0.73 % (asserted < 0.8 %) |
  | Force holding a value | 0.13 N | **0.40 N** |
  | Force over the rim (click) | 1.08 N | 1.47 N |
  | Notch | round scallop R 6 vs nub R 1.2 | 35° V, nub Ø2 seated on both flanks |

  - **Wiggle**: a small nub in a wide round scallop rises only s²/(2·4.8 mm), so the wheel rested anywhere within
    about ±1 mm of a value. On straight 35° flanks the nub lifts 0.7 mm per mm of turn from the first moment, against
    0.4 mm of preload. A part-turn now springs back to the number, or on to the next one.
  - **Brittleness**: the taper spreads the strain along the arm, and the fillet removes the sharp root corner where
    a crack would start. The arm bends in the bed plane, so its stress runs along the printed walls and never across
    the layer lines.
  - The pocket around the arm is also an over-travel stop, so assembly can't over-bend it.
  - The V notches are narrower (3.7 mm at the rim) than the old scallops (7.7 mm). Their sharper edges still give a
    thumb something to catch.
- Tunables: `DIGIT_H` (every 0.5 mm of digit height grows the wheel radius ~1.4 mm), `PIN_CLR`, `WHEEL_CLR`, `AX_CLR`.
  Detent: `PRELOAD` (holding force), `NOTCH_FLANK` (steeper = firmer centring and a harder click), `NOTCH_DEPTH`,
  and `ARM_T_TIP` / `ARM_T_ROOT` / `ARM_L` (stiffness against strain; the build asserts strain stays under `MAX_STRAIN`).

## Files (`out/`)
- `vampire_counter_A1.3mf`: the sliced A1 project, 4 AMS slots. Open it in Bambu Studio, map slots 1–4 to black,
  red, copper and white, and print from there.
- `parts/`: the 17 colour-part STLs (`<front|back|wheel>_<n>_<colour>.stl`, mm, mirrored and laid out as printed)
  plus `slice_args.txt`.
- `counter_preview.png`: the face at 1/1, 5/5 and 9/9, a nozzle simulation, and the back.
- `parts_preview.png`: the back (spacer, detent, pin, pegs) and the wheel.
- No STEP: the parts are shapely polygons extruded into meshes (as in vampire-dial).

## Printing
- Use a **clean** Textured PEI plate (wash it with dish soap). The whole face is the first layer.
- If strokes come out ragged, slow the first layer further (`initial_layer_speed=20`).

## Rebuild
```powershell
.venv\Scripts\python.exe models\vampire-counter\vampire_counter.py
cd models\vampire-counter\out\parts
..\..\..\..\.venv\Scripts\python.exe ..\..\..\..\tools\check_mesh.py (Get-ChildItem *.stl).Name
python ..\..\..\..\tools\slice_bambu.py <contents of slice_args.txt> -o ..\vampire_counter_A1.3mf
```
Uses helpers from `models/vampire-token` (extrusion) and `models/vampire-dial` (glyphs, text layout, drawing).
**`models/vampire-arcana` imports this file**, so rebuild arcana too after changing anything shared.

## History
- 2026-11-12: v1, redesign of vampire-dial for legibility: vector scene, 6.8 mm title, 8 mm N/N dial. Caricature vampire.
- 2026-11-12: v1.1, figure redrawn as an elder vampire knight (armour, white hair, beard, sword); smoother bats; sliver
  clean-up. 53 min, 24.5 g, 3 swaps, no slicer warnings.
- 2026-11-12: v1.2, stronger detent: 26 mm tapered, filleted arm with an over-travel stop; V notches with a
  preloaded Ø2 nub, so the wheel no longer wiggles between values. 53 min, 24.6 g, 3 swaps.
- 2026-11-12: v2, alt art of vampire-arcana. This file now holds the shared frame, Georgia title, ruled dial footer,
  back and face-down flat inlay; the colour scene is refit to the new art plate (one fauld seam). 1 h 04 min,
  29.1 g, 7 swaps, no warnings.
- 2026-11-12: v2.1, fix the dial alignment found on the first arcana print: the value never centred in the window
  with the detent seated. `write_plate()` had mirrored the whole back (pin, spacer, detent, pegs), not just its
  art; the symmetric pegs still fit, but the wheel sat on the wrong side, so the window saw the ring at −75° instead
  of −100° (0.6 of a 40° step). Only the back art is mirrored now, and a new `assembly_check()` rebuilds the parts
  as printed (flipped, wheel on the printed pin) and asserts every value is centred with the nub seated.
  1 h 04 min, 29.0 g, 7 swaps. **Reprint the back** (front and wheel are unchanged).
