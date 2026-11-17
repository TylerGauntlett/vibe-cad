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
| Card | **70.5** × 88 mm (v4: widened from the 63 mm token size so two wheels fit), 3 mm corners, **4.8 mm** thick assembled (back 2.8 + front 2.0; the tongue sits in the front's groove) |
| Frame (shared with arcana) | black card edge 1.8 mm, black rules 1.2 mm; white plates: title 12.4 mm, art 66.9 × 53.4 mm, footer 16.2 mm |
| Title (shared) | "VAMPIRE", **Georgia Regular, 6.0 mm caps**, black on the white title plate, 45.9 mm long in a 66.9 mm plate (59.4 before v4) |
| Dial | **two wheels**: power (bottom-left, rim out of the left edge) and toughness (bottom-right, rim out of the right edge), 9 positions × 40°, **1–9 each**, held by friction (no detent since v3) |
| Digits | Bahnschrift Bold Condensed, **8.0 mm** tall, one per window, black inlaid flat in the white wheels |
| Windows (shared) | 5.9 × 9.3 mm at (15.9, 8.6) and (54.6, 8.6), each in a ruled box (0.7 white mat + 0.7 black rule) in the footer's corners; between them a **bat shaped as the "/"** |
| Wheels | Ø 36.8 mm each, digit ring r 11.2, 9 **V notches** as a grip (1.3 deep, 35° flanks, 0.6 mm rounded edges); each rim pokes **2.5 mm** out of its side; 1.07 mm of spacer between the cavities; hubs Ø6.8 on Ø6 pins (**0.4 mm** radial clearance) |
| Joint | **tongue and groove**: 1.2 × 0.6 mm ridge 2 mm in from the edge (186 mm in 2 runs: down both sides to the wheels and across the top; along the bottom between the wheels), in a 1.5 × 0.8 mm groove under the front; the pins in 0.8 mm sockets |
| Turning | push either rim **up** to count up |
| Art (this card's own) | flat-colour vector scene: an elder vampire knight (long white hair, pointed beard, layered pauldrons with copper edges, gorget, red cloak, sword planted point-down) before a **blood moon**, with copper cloud streaks, bats and a black castle with red lancet windows |
| Colours (shared) | 1 ink `#1E1A18`, 2 blood `#9B1B1E`, 3 gold `#B87333` (copper), 4 paper `#F4F1EA` (white): the same spools as v1 |
| Inlay (shared) | **face-down**, 0.4 mm (4 layers at 0.10 mm) of colour on front, back and wheels; everything above is white |
| Back (shared) | black edge plus a gold crescent and bat, inlaid in the same layers |
| Material / printer | Bambu PLA Basic, A1 **0.2 mm nozzle**, 0.10mm Standard @BBL A1 0.2 nozzle + Arachne, Textured PEI (65 °C) |
| Plate | 1: front, back and both wheels side by side (one object, 19 colour parts), 194 × 88 mm |
| Print | **v4 not sliced yet** (built in a cloud session without Bambu Studio; see Rebuild). v2 on the 0.4 nozzle: 1 h 04 min, 29.1 g, 7 swaps |
| Model grams per slot | ink 1.50, blood 0.29, gold 0.28, paper 33.21 (solid volume; 15 % infill makes the real total lower) |

### Mechanism (v4)
- **Back**: 0.6 mm plate + 2.2 mm spacer with the two wheel cavities (0.4 mm radial clearance), two Ø6 axle pins
  (0.6 mm taller than the spacer), and the tongue on the spacer's top face. No detent: each wheel's friction holds its value.
- **Wheels** (power, toughness): flat 1.8 mm white discs with the digits inlaid black in their faces (printed
  face-down); hubs Ø6.8.
- **Front**: printed face-down: the 0.4 mm colour inlay, white above it, the window cut through, and the groove and
  pin socket (0.8 mm deep) in its underside.

### Assembly
1. Peel the three parts off the plate. The front and wheel come off face-down; turn them over. Clean any elephant
   foot off the wheel's hole and rim, and off the tongue.
2. Drop each wheel onto its pin, digits up: **power** (its digits run clockwise) on the left pin, **toughness** on the
   right (the parts are labelled by file name; on the plate the power wheel is the lower one). With no clicks, centre
   each value in its window by eye once the front is on.
3. Dry-fit the front: the tongue should drop into the groove all the way round, with the pin in its socket.
4. Run a thin line of **CA in the groove only** (none on the pin or near the wheel) and press the front flat while it sets.

## Decisions & interpretations
### v4: separate power and toughness wheels, 70.5 mm card
Asked: "show power and toughness as separate values, on the left and right bottom corners with their own wheels;
font size maintained or enlarged; the wheels can be exposed on the left and right sides".
- **Two wheels, 1–9 each** (asked). Power is bottom-left with its rim out of the left edge, toughness bottom-right
  out of the right edge. Each window sits straight below its wheel's centre. Pushing either rim **up** counts up, so
  the power wheel's digits run the other way round.
- **Digits kept at 8 mm** (Bahnschrift Bold Condensed, single digits from the same outlines as v3's "N/N"). To hide
  both neighbours, a single 8 mm digit needs a digit ring of r 11.2 (searched), so each wheel is Ø36.8. Two of those
  don't fit side by side in 63 mm. **The card is widened to 70.5 mm** (chosen over a thicker stacked-wheel card,
  6 mm rims, or smaller digits): 4R + 2·clearance + 1 mm wall − 2·2.5 mm protrusion = 70.4 mm. The card is
  no longer standard token or sleeve size; height, thickness, frame and type are unchanged.
- **Footer**: two ruled windows (5.9 × 9.3 mm) in the corners. Between them, a **bat whose spread wings form the "/"**
  (asked: "a bat shaped /"). It's a dedicated shape (`slash_bat_shape()`): straight leading edges, three
  pointed fingers and scallops per wing, the body and ears square to the wing line, all turned 62°. Rotating the
  ordinary bat read as a leaf.
- **Art refit to the wider plate**: left-side elements stay put, right-side ones (towers, streaks, lancets) move with
  the right edge (`xr()`), and the bats round the moon move with the centre (`xc()`). The knight and moon follow the
  centre. The cloak widens progressively (`cloak_widen()`): unchanged under the pauldrons, ×1.126 at the plate's
  bottom, so it still fills the corners without a sliver above the shoulders.
- **Joint**: the tongue now runs across the top and down both sides to the wheels (168 mm), plus an 18 mm run along
  the bottom edge between the wheels; the bottom corners belong to the wheels. Two pins in two 0.8 mm sockets.
- `assembly_check()` checks both wheels on the parts as printed: each value centred in its own window, the pins on the
  hub centres with 0.4 mm clearance, the tongue and pins 0.15 mm inside their grooves.

### v3: no detent, tongue and groove, looser hub, 0.2 mm nozzle
Asked: "remake back piece that presses into the gears of the wheel; make connection between pieces use tongue and
groove connections instead of the single dots, along most of the top edges and bottom corner; make the middle area
of the wheel have more tolerance so it fits less snugly into the bottom half; update anything needed to print with
a 0.2 mm nozzle".
- **Detent removed** (clarified: it "adds complexity and a failing point to a non problem"; the wheel's friction in
  the case already holds a value). The back is now a plain plate + spacer around the wheel cavity: no arm, no pocket,
  and no slot through the back plate. The 9 V notches stay as the thumb grip. Without clicks, line the value up
  in the window by eye.
- **Tongue and groove** replaces the 6 Ø2 pegs (layout chosen: top U + bottom-left L). A 1.2 × 0.6 mm ridge on the
  spacer, its centreline 2.0 mm in from the card edge, runs wherever it stays ≥ 1.2 mm from the wheel cavity:
  one 198 mm run from the bottom edge, up the left side, across the top and down the right side to the wheel, plus
  a 21 mm L in the bottom-right corner below the wheel's rim. The front's underside has a 1.5 × 0.8 mm groove
  (0.15 mm per side, 0.2 mm of glue room on top). The pin's socket is 0.8 mm deep too, and the pin is 0.6 mm taller.
  The front's groove keeps a 1.25 mm outer wall, and 1.2 mm of front stays above it.
- **Hub clearance 0.25 → 0.4 mm** radial (hole Ø6.8 on the Ø6 pin). Cavity, axial play and the wheel are unchanged.
- **0.2 mm nozzle** from now on: presets *Bambu Lab A1 0.2 nozzle*, *0.10mm Standard @BBL A1 0.2 nozzle*, *Bambu PLA
  Basic @BBL A1 0.2 nozzle* (in `slice_args.txt`; also the new `slice_bambu.py` defaults). Every height is a multiple
  of 0.1 mm. The inlay stays 0.4 mm thick for opacity, so it's now 4 layers: expect about twice the filament swaps
  and a longer print than v2. The old `initial_layer_speed=30` / `initial_layer_infill_speed=60` overrides are
  dropped, because they would have sped up the 0.2 preset's slower first layer (16 / 28 mm/s). The art keeps its 0.4 mm
  line rules (`BEAD` 0.45): they print fine on the 0.2 nozzle, and finer art is now possible but wasn't asked for.
- `assembly_check()` now checks the fits on the parts as printed: the tongue and pin sit 0.15 mm inside their grooves,
  the hub has 0.40 mm, and all 9 values are centred in the window.
- **Fonts**: Georgia and Bahnschrift are Windows fonts. Their outlines are cached in `text_cache.json` (recovered
  from the v2 STLs; the front art came out unchanged). A build without the fonts uses the cache, and a build with
  them refreshes it.

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
  Joint (v3): `TONGUE_W` / `TONGUE_H`, `TONGUE_CLR` (fit), `TONGUE_INSET`, `TONGUE_GAP` (where it breaks at the
  wheel), `TONGUE_MIN_LEN`. (The v1.2 detent notes above are history; v3 removed the detent.)

## Files (`out/`)
- `vampire_counter_A1.3mf`: **removed in v3** (it held the v2 parts on the 0.4 nozzle). Re-slice on the Windows PC
  (see Rebuild), open it in Bambu Studio, map slots 1–4 to black, red, copper and white, and print from there.
- `parts/`: the 19 colour-part STLs (`<front|back|power|toughness>_<n>_<colour>.stl`, mm, mirrored and laid out as printed)
  plus `slice_args.txt`.
- `counter_preview.png`: the face at 1/1, 3/5 and 9/9, a nozzle simulation, and the back.
- `parts_preview.png`: the back (spacer, tongue, pins), the front's underside (groove, pin sockets), a joint section and both wheels.
- No STEP: the parts are shapely polygons extruded into meshes (as in vampire-dial).

## Printing
- Use a **clean** Textured PEI plate (wash it with dish soap). The whole face is the first layer.
- The 0.2 nozzle preset already runs the first layer slowly (16 mm/s walls). Leave it there.

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
- 2026-11-17: v3, detent removed (the wheel's friction holds it); the 6 pegs are replaced by a tongue and groove
  round the edge (219 mm); hub clearance 0.25 → 0.4 mm; switched to the **0.2 mm nozzle** (0.10 mm layers, 0.2
  nozzle presets); fonts cached in `text_cache.json`. Front art unchanged. Not yet sliced: the 3MF must be
  regenerated on the Windows PC. **Reprint all three parts.**
- 2026-11-17: v4, power and toughness on **separate wheels** (1–9 each, 8 mm digits), rims out of the left and right
  edges, windows in the footer's corners with a bat-shaped "/" between them; card widened to **70.5 mm**; scene
  re-anchored to the wider plate. Not yet sliced. **Reprint all four parts.**
