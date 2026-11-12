# Vampire token with P/T dial wheel

## Request
"`models/vampire-token/out/vampire_token_relief_A1.3mf` already describes a well built vampire token. Create a
new model in a .3mf file that also has a scrolling wheel inside that can be turned to adjust the power
and toughness between 1/1 - 9/9. Note that the height of the card might need to be increased slightly
to allow for such a wheel. Ideally the wheel numbers are visible from around the same areas of the
existing 1/1 but that can change if needed."

## Spec (as built)
| Parameter | Value |
|---|---|
| Card | 63 × **92** mm (art 63 × 88 + 4 mm extra black border at the bottom), 3 mm corners |
| Thickness | **4.8 mm** assembled: back 2.8 (0.6 plate + 2.2 wheel cavity) + front 2.0 (the v3 relief) |
| Dial | one wheel, 9 positions × 40°: **1/1 … 9/9** (power = toughness), detent click per value |
| Window | 7.4 × 3.8 mm, centred in the art's P/T box (same place as the printed 1/1) |
| Digits | DejaVu Sans Bold +0.05 mm bold, 3.0 mm tall, black tops, raised 0.8 mm in a cream channel |
| Wheel | Ø 33 mm, 9 thumb scallops; the rim protrudes **2.4 mm** (valleys 1.2 mm) past the right edge |
| Turning | push the rim **up** to count up, down to count down |
| Colours | the same 4 AMS slots as the token: 1 black `#241B16`, 2 red `#8E1D19`, 3 tan `#B08551`, 4 cream `#F0CB9A` |
| Material / printer | Bambu PLA Basic, A1 0.4 mm, 0.20 mm Standard + Arachne walls, Textured PEI (65 °C) |
| Plates | 1: front, back and wheel side by side (one object, 16 colour parts) |
| Art | simplified for a 0.4 mm nozzle: every colour ≥ 0.5 mm wide, no islands < 1 mm² (face: 0.45 mm / 0.4 mm²); frame lines and set symbol thickened 0.1 mm per side, title letters 0.2 mm |
| Type line | re-set as vector text, Bahnschrift SemiBold Condensed (+0.04 mm bold, +0.45 mm letter spacing), 2.7 mm cap height |
| Print | **56 min, 25.9 g, 3 filament swaps, ~0.5 g purge** |
| Model grams per slot | black 9.1, red 4.8, tan 2.5, cream 14.8 (solid volume; the 15 % infill makes the real total lower) |

### Mechanism
```
 side section (not to scale)                         z (mm)
 ┌───────────── front: relief art, window ───────┐  2.8–4.8
 │░░░░░░░░░░░░░░░░░░ sockets ▼    ▼ ░░░░░░░░░░░░░│
 └───────────────────────────────────────────────┘
  ▐peg▌      ▐ wheel 1.8 thick ▌ ▐pin▌   ▐rim ▌→ pokes out of the right edge
 ┌──────────┐ ═══════════════════════════ ┌──────┐  0.6–2.8 spacer frame + detent arm
 └───────────────── back plate ──────────────────┘  0–0.6
```
- **Back**: plate + spacer frame with the wheel cavity (0.4 mm radial clearance), a Ø5 axle pin, 4 Ø2
  alignment pegs, and a **detent spring**: a 14 × 1 mm cantilever left of the wheel whose nub
  (R 1.2, 0.2 mm preload) sits in one of the wheel's 9 scallops. The arm stands free over a slot cut
  through the back plate, so it isn't fused to it (the slot is visible on the back of the card).
  Full deflection is about 1% strain, well inside PLA's limit.
- **Wheel**: 1.0 mm cream disc, plus a 0.8 mm raised rim, hub and "N/N" digits (tan → red → black, so
  their tops are black). Hub hole: 0.25 mm radial clearance on the pin. 0.4 mm axial play in the cavity.
- **Front**: the relief art (same Z bands as v3: cream base 1.0, tan, red, black ink 1.6–2.0, but simplified, see below), the window cut
  through it, and 0.6 mm-deep sockets underneath for the pegs and the pin top.

### Assembly
1. Peel the three parts off the plate. Clean any brim or elephant-foot off the wheel's hole and rim.
2. Drop the wheel onto the back's pin, black side up. Push the detent arm aside slightly so the nub
   lands in a scallop.
3. Turn the wheel until "1/1" sits where the window will be (bottom right; its tops face the front's P/T box).
4. Lay the front on top so the pegs and pin enter its sockets. Glue with a drop of **CA on the 4 pegs only**
   (not the pin, and keep glue away from the wheel). Press flat while it sets.

## Decisions & interpretations
- **One linked wheel (N/N)**, not separate power and toughness wheels: "a scrolling wheel" and the
  "1/1 – 9/9" range read as one value. That also suits vampire tokens, which mostly grow with
  +1/+1 counters. Two independent wheels would need two digit rings and roughly twice the area.
- **Why the card grew 4 mm (in height)**: the 1/1 box is only 4.6 mm above the bottom edge and 8.8 mm from the
  right one. To keep 9 values apart, the digit ring needs a radius of at least ~10.7 mm, and the rim and
  scallops sit outside that ring. A layout search found the wheel can't stay inside 63 × 88 with the
  window at the box. It fits by either (a) adding 4 mm of border below the art or (b) moving the window
  ~5 mm left and up into the type line. (a) was chosen: the window stays on the art's P/T box, as asked.
  The extra rows are black border, inserted inside the art's existing bottom border.
- **Rim out of the right edge**: a thumb needs something to push. 9 deep scallops serve as the grip
  and as the detent notches, so each click lands on a value. Push up to count up.
- **Zero extra colour swaps**: every part uses the relief token's Z bands (cream 0–1.0, tan 1.0–1.2,
  red 1.2–1.6, black 1.6+). Each layer of the whole plate is still a single filament: **3 swaps**, all
  light → dark, the same as the plain relief token. The cost is that the back's and wheel's edges are
  striped (cream/tan/red/black), and the wheel had to be 1.8 mm thick so its digits reach the black band.
- **Front base kept at 1.0 mm cream** (as v3) rather than thinner. Thin cream PLA over the black
  wheel would ghost the wheel's rim and digits through the type line.
- **Parts, not print-in-place**: printing the front over the wheel would need a 33 mm bridge across an
  air gap. Three flat parts that stack in their printed orientation are more reliable.
- **No STEP**: the front is raster art turned into a mesh (see `models/vampire-token`). The back and
  wheel are built with shapely in the same script, so their parameters are all at the top of `vampire_dial.py`.
- Tunables if the fit is off: `PIN_CLR`, `WHEEL_CLR`, `AX_CLR` (looseness), `PRELOAD` / `ARM_T` (detent
  force), `SCALLOP_DEPTH` (grip and click depth), `SOCKET_D_CLR` (peg fit).

- **Art simplification (v1.2)**: the v3 clean-up kept strokes ≥ 0.25 mm and specks ≥ 0.04 mm². Arachne prints
  0.25–0.4 mm strokes as broken single beads, so the print showed hundreds of stray dots and dashes. The front now
  has its own zoned clean-up (`ART`, `DETAIL`, `ZONES` in the script):
  - Illustration: majority blur σ 0.12 mm, every colour opened to 0.5 mm, islands < 1 mm² absorbed.
    The 0.5 mm² setting left thin spears as dotted dashes, which are fragments too, so 1 mm² it is.
    Islands per colour went from 86–229 to 45–57, and none are under 0.05 mm².
  - Face: a milder 0.45 mm / 0.4 mm², so the eyes, nose and mouth survive.
  - Frames, title, set symbol and P/T border: the light v3 clean, then thin colours grown 0.1 mm per side. Opening
    would delete these lines; growing them turns 0.3 mm lines into solid 0.5 mm beads.
- **Type line (v1.2)**: the art's serif lettering has a 2.1 mm cap height with ~0.3 mm crossbars and serifs. Arachne
  printed only the stems (no T bar, half a V). It is erased and re-set as vector text.
  - A font search scored each candidate by whether its strokes (≥ 0.42 mm) and its counters and gaps (≥ 0.3 mm)
    survive a 0.4 mm nozzle. At this width, regular-width fonts fill in the counters of e and a. The condensed
    Bahnschrift gets 2.7 mm caps in 43.5 mm.
  - Bahnschrift is a Windows variable font; the script cuts a static SemiBold Condensed instance with fontTools.
    It falls back to DejaVu Sans Bold if the font is missing.
  - The new text is black and raised to the top (1.6–2.0 mm), like all ink.
- **Checked against a real print of the v3 token** (black/red/copper/white spools): it showed the illegible type line
  and 1/1, fragmented black/red blobs, and black specks on the white areas.
  - The specks are ooze dropped while travelling between black islands on the top layers. Fewer islands means fewer
    travels: top-layer retractions went 1068 → 685 at 2.0 mm and 649 → 344 at 1.8 mm, even though the dial count
    includes the back and wheel.
  - The title's cream letters are 1 mm-deep slots, and on the print their floor barely showed. They now grow
    0.2 mm per side (+28% area).
  - The wheel digits had 17–30% of their ink under a bead (the same failure as the printed 1/1). Emboldening
    them 0.05 mm brings that to ~2%, which is corner rounding only.

## Files (`out/`)
- `vampire_dial_A1.3mf`: sliced A1 project, 4 AMS slots. Open in Bambu Studio, map slots to your spools, and print from there.
- `parts/`: the 16 colour-part STLs (`<front|back|wheel>_<n>_<colour>.stl`, mm, laid out as on the plate) + `slice_args.txt`.
- `dial_preview.png`: assembled top view at 1/1, 4/4 and 9/9, plus a window close-up.
- `parts_preview.png`: back (spacer, detent arm, pin, pegs), detent close-up, wheel top.
- `plate_preview.png`: Bambu's plate render.

## Rebuild
```powershell
.venv\Scripts\python.exe models\vampire-dial\vampire_dial.py
.venv\Scripts\python.exe tools\check_mesh.py models\vampire-dial\out\parts\*.stl
cd models\vampire-dial\out\parts
python ..\..\..\..\tools\slice_bambu.py <contents of slice_args.txt> -o ..\vampire_dial_A1.3mf
```
Depends on `models/vampire-token/vampire_token.py` (art pipeline and source image).

## History
- 2026-11-11: v1, relief token + internal 9-position P/T dial with detent, 63 × 92 × 4.8 mm, 3 swaps, sliced for A1.
- 2026-11-11: v1.1, fixed the missing "/" on 2/2, 4/4, 6/6, 9/9: the shared `extrude()` inset collapsed thin slanted shapes (see `models/vampire-token`). Re-sliced: same 1 h 02 min, 26.1 g, 3 swaps.
- 2026-11-11: v1.2, readable type line (vector Bahnschrift SemiBold Condensed) and simplified art (no specks or slivers under a bead; frame lines thickened). 56 min, 25.9 g, 3 swaps, no slicer warnings.
- 2026-11-11: v1.3, after a photo of the v3 print: wheel digits emboldened 0.05 mm (no sub-bead strokes), title letters grown 0.2 mm. 56 min, 25.9 g, 3 swaps.
