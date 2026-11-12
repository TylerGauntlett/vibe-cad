# Vampire cathedral token

## Request
"Use models/vampire-arcana and models/vampire-counter as inspiration to build a new model. It should follow the
font, border, main character, etc. as the existing 2 while introducing a new background and character details."

Asked (2026-11-12):
- Style: **hybrid**: a woodcut figure (arcana) on a flat-colour background (counter).
- Background: **cathedral rose window**.
- Details: **spiked crown** and **high-collared cape**.

v2 request: "consider how more elements of the 2 can be blended together instead of having the background from one
with the character from the other. Could the sword from one be taken while the robes from the other are taken?
Should both be completely re-imagined?" Asked; chosen: a **rule-based blend** (below), not a full re-imagining.

## Spec (as built)
| Parameter | Value |
|---|---|
| Card, frame, title, dial, back, mechanism | **shared**: vampire-counter's frame (63 × 88 × 4.8 mm, 1.8 mm black edge, 1.2 mm rules, "VAMPIRE" in Georgia 6.0 mm caps), back, and the shared vampire-counter dial: 1/1 … 9/9 in 7.5 mm digits, a bevelled window standing on the card's bottom edge with a bat either side, and the wheel's thumb rim poking 2 mm out of the **bottom edge** (push it right to count up) |
| Blend rule | **flat colour for cloth, glass and gold** (vampire-counter's language); **woodcut line for skin, hair, steel and stone** (vampire-arcana's) |
| Figure | the shared knight, assembled from parts: counter's **red cloak with black tapered folds** (on arcana's cloak silhouette, outlined); arcana's outlined, hatched **armour**; the shared face and hair in arcana's inking; a **merged sword**: arcana's blade with blood down the fuller and its gold guard and pommel, with the counter's **copper grip and two black bands**; plus: |
| — crown | gold circlet over the hairline with 5 spikes (tips 13.0–15.4 mm above the face centre), outlined 0.55 black, a blood-red gem at the front |
| — collar | a tall vampire collar rising to a point beside each temple: black outline, **red lining**, 5 black stays fanned up from the neck |
| Background | an **engraved white stone nave** (arcana's ragged hatching, 0.55 at 1.25 pitch, running in 3–7 mm from the moulding, cut around the window, candles and cloak) under a pointed two-centred arch (R 34, springing at y 40.8, gold 0.8 mm moulding and capitals); black stone spandrels and piers, a **white bat** in each spandrel; a **rose window** haloing the head (Ø 35.2: a black leaded disc, one gold ring r 14.4–16.6 split by 12 black spokes, a black rim); a woodcut candle either side (outlined wax and gold flame, black pricket stand, ≥ 1 mm clear of the moulding, asserted) |
| Colours | 1 ink `#1E1A18`, 2 blood `#9B1B1E`, 3 gold `#B87333`, 4 paper `#F4F1EA` (the siblings' 4 spools) |
| Face colour shares | ink 42.8 %, blood 5.0 %, gold 5.0 %, paper 47.2 % |
| Line rules | arcana's: outlines 0.7, strokes 0.55, sub-bead slivers of white, red and gold merged into neighbours (18.6 mm² total), no island under 1 mm² |
| Print | face-down flat inlay, 0.4 mm of colour; vampire-counter `SLICER_SET` (Arachne, slow first layer), Textured PEI 65 °C |
| Plate | 1: front, back and wheel (one object, 21 parts) |
| Sliced | **1 h 06 min, 28.6 g, 6 filament swaps (~2.3 g purge)**; per slot ink 1.95, blood 0.42, gold 0.90, paper 25.36 g, no slicer warnings (only the harmless enclosure advisory). v3 is not printed yet |

## Decisions & interpretations
### v2: a rule-based blend
- **One rule decides each element's style**, so the mix reads as designed rather than patched: cloth, glass and
  gold are flat colour; skin, hair, steel and stone are woodcut line. Each element is taken from whichever sibling
  already draws it that way: the counter's red cloak, arcana's hatched steel, both cards' face. The two cards'
  swords differ only in the grip, so the sword takes arcana's blood-run blade and the counter's banded grip.
- **Why not re-imagine from scratch** (the other option offered): the three cards are a set. The face, hair, beard
  and silhouette are what make them read as the same knight, and a new figure would lose that.
- **The nave turned from red to engraved white** because of the rule (stone is line work). It also had to: the red
  cloak would have vanished against a red wall. The hatching is shorter than arcana's sky lines (3–7 mm in from the
  arch), so the wall is shaded at its edges and calm behind the figure, after v1.1's "too much happening".
- **Stroke clean-up.** The strokes are cut around the window, candles and cloak (each plus a 0.7 mm halo) before
  they are drawn. Only the piece touching the moulding is kept, and it is dropped if under 2 mm, so no stub or
  floating dash is left. Halos are clipped to the white wall: unclipped, they drew white lines along the cloak on
  the black piers and cut the gold moulding.
- **Candles lowered 2.6 mm**: their flames ran into the arch's moulding and cut it on the right. The build now
  asserts ≥ 1 mm of clearance.
- **Shared parts, not copies.** `vampire-arcana`'s `knight()` is now split into `knight_cloak()`,
  `knight_armour()`, `knight_head()` and `knight_sword(grip=...)` (plus `cloak_shape()`/`CLOAK_FOLDS`). Arcana
  still calls them in the original order, and its 17 STLs are byte-identical after the split. This card calls
  armour, head and sword (with its own grip) and paints its own cloak. vampire-counter is untouched.

### v1
- **What "follow the existing two" means here.** Everything outside the art plate is imported, not copied: frame,
  title, footer, back, mechanism and build come from `vampire-counter` (`vc`), and the knight from `vampire-arcana`.
  A frame or figure change in a sibling also lands here.
- **v1 layering** (superseded by v2): a flat-colour background (red nave), then the collar, arcana's whole knight
  and the crown.
- **Collar lining red, not black.** A black collar merged into the rose window's black leading and disappeared
  (first render). The red lining is the hybrid's flat-colour accent on the figure. It is also the classic vampire
  collar. The stays fan from the neck, not from beside the hair: a focus beside the hair made the lowest stays
  converge into a fishbone of small red wedges.
- **Rose window centre black.** The centre sits behind the head. With red glass there, the crown's outlines
  fused into a black zigzag. On black, only the crown's gold silhouette counts, so the spikes can be wide.
- **Plain window (v1.1).** v1's 16 pointed petals started at r 12.4, right where the crown's spikes end (r ~12.8),
  and its 16 white roundels added more points, so window and crown read as one tangled crown. Now one gold ring
  starts 1.6 mm beyond the tallest spike, leaving a clear black band, and a spoke sits behind the centre spike.
- **Stone black.** `vc.frame()` leaves the art plate white, so the stone is painted black and the nave
  is cut back into it. The spandrels merge with the card's black edge, which reads as a carved arched frame,
  the tarot look of the siblings. The arch's apex lies above the plate, so the nave meets the title rule with a
  9 mm opening instead of a sub-bead point.
- **Slivers in every colour.** Flat red and gold meet outlines and the moulding at shallow angles, so this
  card's `finish()` runs `vc.fill_slivers()` for red and gold as well as white (1.6 and 3.3 mm² moved in v2).
- Tunables: `COURSE_Y0` / `COURSE_L` (wall hatching), `CLOAK` / `CLOAK_FOLD_W`, `GRIP_BANDS`, `ARCH_RHO` / `SPRING` (arch shape), `ROSE_*` (ring radius, `ROSE_SEGMENTS`, `ROSE_SPOKE`), `CANDLES`,
  `COLLAR_LINING`, `COLLAR_FAN`, `CROWN_SPIKES`.

## Printing and assembly
Same as vampire-arcana:
- Use a clean Textured PEI plate. Open `out/vampire_cathedral_A1.3mf` in Bambu Studio, map slots 1–4 to black,
  red, copper and white, and print from there.
- Flip the front and wheel over. Seat the wheel on the pin with "1/1" at the bottom, check it clicks through all
  9 values, then glue the front on with CA on the 6 pegs only.

## Files (`out/`)
- `vampire_cathedral_A1.3mf`: the sliced A1 project, 4 AMS slots.
- `parts/`: 21 STLs, one per colour and height band (mm, mirrored and laid out as printed) plus `slice_args.txt`.
- `section_preview.png`: side section through the window and axle, from the printed parts re-assembled.
- `cathedral_preview.png`: the face at 1/1, 5/5 and 9/9, a nozzle simulation, and the back.
- `cathedral_detail.png`: the left half of the art plate at print scale (stone, candle, window, crown, cloak,
  hilt), plain and nozzle-simulated.
- No STEP (shapely polygons extruded into meshes, as in the siblings).

## Rebuild
```powershell
.venv\Scripts\python.exe models\vampire-cathedral\vampire_cathedral.py
cd models\vampire-cathedral\out\parts
..\..\..\..\.venv\Scripts\python.exe ..\..\..\..\tools\check_mesh.py (Get-ChildItem *.stl).Name
python ..\..\..\..\tools\slice_bambu.py <contents of slice_args.txt> -o ..\vampire_cathedral_A1.3mf
```
Imports `models/vampire-arcana`, which imports `models/vampire-counter`. Rebuild this card after changing either.

## History
- 2026-11-12: v1, the arcana knight with a spiked crown and a red-lined high collar, before a flat-colour
  cathedral: red nave, black stone arch with spandrel bats, gold rose window, candles. 1 h 05 min, 28.6 g,
  6 swaps, no warnings. All 17 meshes have open_edges=0; the as-printed assembly check passes.
- 2026-11-12: v1.1, simpler rose window ("too much happening between the crown and window"): one gold ring of
  12 segments clear of the crown, instead of 16 petals and 16 roundels. 1 h 04 min, 28.7 g, 6 swaps, no warnings.
- 2026-11-12: v2, rule-based blend of the siblings (flat colour for cloth, glass and gold; woodcut for skin, hair, steel
  and stone): the counter's red cloak, arcana's hatched armour, a merged sword (arcana's blade, the counter's grip), an
  engraved white nave; candles lowered clear of the arch. arcana's knight split into parts (output byte-identical).
  1 h 05 min, 28.7 g, 6 swaps, no warnings; 17 meshes open_edges=0; the as-printed assembly check passes.
- 2026-11-12: v3, vampire-counter v3's dial (shared code; here only `finish()` changed, to clear the window's
  bevelled mouth): wheel centred, thumb rim at the **bottom edge** (push right to count up), window on the centre
  line, bevelled, standing on the bottom edge; 7.5 mm digits; reeded rim. 1 h 06 min, 28.6 g, 6 swaps, no warnings;
  21 meshes open_edges=0; the as-printed check (now with collisions) passes. Not printed yet.
