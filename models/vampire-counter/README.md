# Vampire counter token

## Request
After a photo of the printed `models/vampire-dial` token: "much of the [art] is visually hard to understand or
read. The numbers in the counter are far too small to read, title and sub title text too small, and image unclear
compared to details on the source photo. Instead of producing a like magic card, reimagine this token visual and
functionality": clear card art in the 4-colour palette, a 1/1 counter dial, simple "vampire" labelling, and all
text large enough to read easily. Follow-up: "The vampire face looks cheesy. How would it be modeled more like
Edgar Markov (a vampire knight)".

## Spec (as built)
| Parameter | Value |
|---|---|
| Card | 63 × 88 mm (standard token size), 3 mm corners, **4.8 mm** thick assembled (back 2.8 + front 2.0) |
| Title | "VAMPIRE" only, Cambria Bold, **6.8 mm caps** (vampire-dial: 4.2 / 3.5 mm), cream letters in a black bar |
| Dial | one wheel, 9 positions × 40°: **1/1 … 9/9**, click detent at each value |
| Digits | Bahnschrift Bold Condensed, **8.0 mm** tall (vampire-dial: 3.0 mm for all of "N/N"), slash cut to digit height |
| Window | 13.7 × 9.3 mm, bottom centre (32.3, 10.3), in a cream mat with a tan rim |
| Wheel | Ø 58.9 mm, digit ring r 21, 9 **V notches** (1.3 deep, 35° flanks, 0.6 mm rounded edges); the rim pokes **2.5 mm** out of the right edge |
| Detent | 26 mm cantilever tapered 1.4 → 2.2 mm, R 3 root fillet, Ø2 nub on both notch flanks with 0.4 mm preload. Holds **0.40 N** seated and 1.47 N over the rim at **0.52 %** peak strain; the pocket wall stops it at 0.73 % |
| Turning | push the rim **up** to count up |
| Art | original vector scene: an elder vampire knight (long white hair, pointed beard, layered pauldrons, gorget, red cloak, sword planted point-down) before a blood moon, with bats, cloud streaks and castle spires |
| Colours | 4 AMS slots: 1 black `#241B16`, 2 red `#8E1D19`, 3 tan `#B08551`, 4 cream `#F0CB9A` (the print used black / red / copper / white) |
| Material / printer | Bambu PLA Basic, A1 0.4 mm, 0.20 mm Standard + Arachne (same `SLICER_SET` as vampire-dial), Textured PEI (65 °C) |
| Plates | 1: front, back and wheel side by side (one object, 16 colour parts) |
| Print | **53 min, 24.5 g, 3 filament swaps (~0.5 g purge)**, no slicer warnings |
| Model grams per slot | black 6.0, red 3.8, tan 2.1, cream 15.4 (solid volume; 15 % infill makes the real total lower) |

### Mechanism
Same sandwich as `models/vampire-dial`, scaled up:
- **Back**: 0.6 mm plate + 2.2 mm spacer with the wheel cavity (0.4 mm radial clearance), a Ø6 axle pin, 6 Ø2
  alignment pegs, and the detent arm on top of the wheel, running left. The arm stands free over a slot through the
  plate. The pocket around it doubles as an over-travel stop.
- **Wheel**: 1.0 mm cream disc + 0.8 mm raised rim, hub and digits (tan → red → black, so the tops are black).
- **Front**: the relief art (cream base 1.0, tan, red, black ink up to 2.0 mm), the window cut through, sockets underneath.

### Assembly
1. Peel the three parts off the plate. Clean any elephant foot off the wheel's hole and rim.
2. Hold the wheel black side up with "1/1" at the bottom, so a notch sits at the top under the nub. Lower it onto
   the pin. If the nub catches, lift the arm's tip outward by about 0.5 mm; the pocket wall stops it before it over-bends.
3. Check the wheel clicks through all 9 values, then return it to 1/1.
4. Lay the front on so the pegs and pin enter its sockets. Put a drop of **CA on the 6 pegs only**, then press flat.

## Decisions & interpretations
- **Shape: card + side wheel** (asked; the other option was a Ø70 round medallion). The card keeps sleeve and
  playmat size.
- **Art: new vector scene** (asked; the alternatives were an enlarged crop of the old art or a single icon).
  Drawn in code (`knight()`, `art()`), so every shape is a deliberate size: outlines and strands ≥ 0.7 mm, rims
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
- **Zero extra swaps**: every part uses the relief Z bands (cream 0–1.0, tan 1.0–1.2, red 1.2–1.6, black 1.6+),
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
- `vampire_counter_A1.3mf`: sliced A1 project, 4 AMS slots. Open in Bambu Studio, map slots to your spools, print from there.
- `parts/`: the 16 colour-part STLs (`<front|back|wheel>_<n>_<colour>.stl`, mm, laid out as on the plate) + `slice_args.txt`.
- `counter_preview.png`: assembled top view at 1/1, 5/5, 9/9 + window close-up.
- `parts_preview.png`: back (spacer, detent, pin, pegs) and wheel.
- No STEP: the parts are shapely polygons extruded into meshes (as in vampire-dial).

## Rebuild
```powershell
.venv\Scripts\python.exe models\vampire-counter\vampire_counter.py
.venv\Scripts\python.exe tools\check_mesh.py models\vampire-counter\out\parts\*.stl
cd models\vampire-counter\out\parts
python ..\..\..\..\tools\slice_bambu.py <contents of slice_args.txt> -o ..\vampire_counter_A1.3mf
```
Uses helpers from `models/vampire-token` (extrusion, palette) and `models/vampire-dial` (glyphs, text layout, slabs).

## History
- 2026-11-12: v1, redesign of vampire-dial for legibility: vector scene, 6.8 mm title, 8 mm N/N dial. Caricature vampire.
- 2026-11-12: v1.1, figure redrawn as an elder vampire knight (armour, white hair, beard, sword); smoother bats; sliver
  clean-up. 53 min, 24.5 g, 3 swaps, no slicer warnings.
- 2026-11-12: v1.2, stronger detent: 26 mm tapered, filleted arm with an over-travel stop; V notches with a
  preloaded Ø2 nub, so the wheel no longer wiggles between values. 53 min, 24.6 g, 3 swaps.
