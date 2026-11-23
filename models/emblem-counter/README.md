# Emblem counter: generic P/T token with 12 mm digits

## Request
With a screenshot of an ad for the "Soul Dial" (an LCD power/toughness counter that sits over a card's text box):
"Design a token counter using similar theming to the vampire token counters but without a direct vampire theme.
It should be versatile with a handful of designs. Each power and toughness should be individually controllable.
Consider ways to changing it like a wheel or slider. Prioritize readability by making the font large (consider
using all of the space in the description of the mtg card). Provide 5 different designs uses the 6 new colors."

Answers to the spec questions:
- Mechanism: "Consider whatever design best uses the space highlight in this image". No second image arrived, so
  this is read as the text-box area the counter covers in the screenshot.
- The 5 designs: 5 ornamental emblems (no creatures, so any card suits any token).
- Title: none.
- Values: 0–9 on each wheel.

## Spec (as built)
| Parameter | Value |
|---|---|
| Card | 63 × 88 mm (standard), 3 mm corners, **6.6 mm** thick, plus 2.5 mm of wheel rim past the left and right edges |
| Counter | power and toughness on **separate wheels, 0–9 each, 12 mm digits** (Bahnschrift Bold Condensed, 6.4 mm wide) |
| Display plate | 59.4 × 28.9 mm at the bottom of the face (a card's text box). Power window upper-left at (18.5, 22.6), toughness lower-right at (44.5, 11.9), a slash between them: a diagonal "7 / 5". A sword marks the power end, a shield the toughness end |
| Windows | 8.0 × 13.2 mm at the wheels. Face openings 9.6 × 14.8 (power) and 9.6 × 16.8 (toughness), each in a 0.7 mm mat and 0.7 mm rule docked to the plate's border |
| Wheels | Ø 50.4 mm, 1.6 mm thick, digit ring r 16.2, knurled rim (60 teeth, 0.7 mm deep), hubs Ø6.8 on Ø6 pins |
| Levels | power is the **front** wheel (rim out of the left edge, y 27–49), toughness the **rear** wheel (rim out of the right edge, y 17–38). They overlap in plan with a 0.8 mm divider between |
| Turning | push either rim **up** to count up. No detent: friction holds the value, so line it up by eye |
| Depth of the digits | power 1.2 mm below the face, toughness 4.0 mm (plus up to 0.4 mm of play). The toughness well's bottom side is bevelled 45° for 2.8 mm, so the whole digit shows up to about 35° off vertical, and 1 mm of its foot is hidden at 45° |
| Joint | one tongue, 1.2 × 1.4 mm, in 13 dashes (143 mm): it stands on the back, passes through slots in the divider and ends 0.6 mm into the front's groove (0.15 mm per side). Both axle pins end in sockets |
| Art plate | 59.4 × 54.3 mm above the display, one emblem per design |
| Back | ink edge and an eight-point star in the design's second accent |
| Inlay | face-down, 0.4 mm (2 layers) of colour on the front, back and wheels; one filament above that |
| Material / printer | Bambu PLA Matte, A1 0.4 mm nozzle, 0.20 mm Standard + Arachne, slow first layer, Textured PEI |
| Plate | one per design, 201 × 145 mm: front, back, divider in a row, the two wheels behind them |

### The five designs
Slots are ink / accent A / accent B / ground, in AMS order 1–4. All six spools are used across the set.

| Design | AMS 1 ink | AMS 2 | AMS 3 | AMS 4 ground | Print | Swaps (purge) |
|---|---|---|---|---|---|---|
| sun: sixteen rays over hills | Dark Chocolate | Terracotta | Caramel | Ivory White | 1 h 20 min, 38.5 g | 6 (2.1 g) |
| moon: crescent and stars over cloud | Charcoal | Ivory White | Caramel | Desert Tan | 1 h 21 min, 38.4 g | 6 (2.1 g) |
| tree: fruiting tree on a mound | Dark Chocolate | Terracotta | Caramel | Desert Tan | 1 h 20 min, 38.4 g | 7 (2.0 g) |
| flame: fire in a footed bowl | Charcoal | Terracotta | Caramel | Ivory White | 1 h 19 min, 38.9 g | 6 (2.5 g) |
| mountain: peaks, sun and waves | Charcoal | Terracotta | Ivory White | Desert Tan | 1 h 23 min, 39.4 g | 7 (3.0 g) |

No slicer warnings on any plate (only the open-frame bed-temperature advisory). Nothing is printed yet: the fits
are the clearances used on vampire-counter (0.15 mm per side in the joint, 0.4 mm wheel play).

### Parts (z from the card's back face when assembled)
- **back** (printed as it sits): 0–0.6 base with the back art, 0.6–2.6 spacer round the toughness cavity, the
  toughness pin, the tongue dashes.
- **toughness wheel** (face-down): 0.6–2.2.
- **divider** (printed as it sits): 2.6–3.4 plate with the toughness window, the tongue's slots and a hole for
  the toughness pin; the power pin stands on it.
- **power wheel** (face-down): 3.4–5.0.
- **front** (face-down): 3.4–5.4 spacer round the power cavity, 5.4–6.6 face plate with the art, both openings,
  the groove and the power pin's socket.

### Assembly
1. Peel the parts. Front and wheels come off face-down. Clean any elephant foot off the wheel holes, the tongue
   and the pins.
2. Lay the back down, cavity up. Drop the **toughness** wheel on its pin, digits up. (On the plate the power wheel
   is the left one behind the cards, toughness the right; their digits run opposite ways round.)
3. Lower the divider over the tongue dashes and the pin. Its own pin points up.
4. Drop the **power** wheel on the divider's pin, digits up.
5. Dry-fit the front: the dashes should seat in its groove with the pin in its socket, and both wheels turn.
6. Glue: thin CA on the back's spacer top (not near the cavity), divider on; then CA in the front's groove and
   on its spacer face, front on. Keep glue away from the wheels and pins. Press flat while it sets.

## Decisions & interpretations
- **A full token card, not a lay-on gadget.** A counter the size of the text box alone (about 59 × 28 mm)
  could only hold 6 mm digits, because a wheel has to fit inside it. A card can hide the wheels behind the art.
- **Wheels, not sliders.** A sliding number strip needs 19 digit pitches of travel, so a slider can only point
  at a small printed scale (about 4.5 mm numerals). A wheel is the only printed mechanism that shows one large
  digit, and its rim at the card edge is moved with a thumb much like a slider.
- **How the digits got to 12 mm on a 63 mm card.** A 0–9 wheel is about 4.2 × the digit height across:
  - side by side, two wheels allow about 7 mm digits at 63 mm (the vampire cards went to 70.5 mm for 8 mm);
  - overlapping on two levels with both windows in a row, 10 mm: the rear window has to sit outside the front
    wheel's cavity;
  - with the front wheel 10.7 mm higher than the rear one, **12 mm**. The windows then sit on a diagonal, which
    is also what fills the text-box area: power high on the left, toughness low on the right.
  At 13–14 mm the two digits end up nearly one above the other and the display grows to 35–39 mm tall.
  `DIGIT_H` and `WIN_TILT` are parameters; the layout re-solves and the checks re-run.
- **Power in front.** The rear wheel's window must clear the front wheel's cavity. With power in front and
  higher, the layout comes out symmetric about the card's centre line and each rim is on its own digit's side.
- **Cost of the stack**: 6.6 mm thick (the vampire cards are 4.8), five parts instead of four, and the
  toughness digit sits 2.8 mm deeper than power. The deep well is bevelled on its bottom side only: that is the
  side a player looks over, and the other sides are near the power cavity.
- **Window boxes docked to the border.** The toughness opening's bevel reaches 0.7 mm from the plate's bottom
  edge, so its box uses the border as its fourth side; the power box hangs from the top rule to match.
- **Sword and shield** (my addition): they fill the plate's ends and say which number is which.
- **No detent**, as asked on the vampire cards. The rims are knurled instead of notched: with no clicks the nine
  V notches had no job, and 0.7 mm teeth cost less wheel radius.
- **Divider in the ground colour.** Any other colour would add a filament to every layer up to 3.4 mm.
- **Palettes**: three designs on Ivory White or Desert Tan with Dark Chocolate or Charcoal lines; the moon card
  uses Ivory as an accent on tan, so the lights are brighter than the ground. Each plate needs four spools.
- **Art rules** as on vampire-arcana: outlines 0.7 mm, lines 0.55 mm at 1.25 mm pitch, 0.7 mm halos round
  shapes drawn over line fields, islands under 1 mm² absorbed.
- Reuse: drawing helpers from `vampire_arcana` (and through it `vampire_counter`, `vampire_dial`,
  `vampire_token`). Nothing in those models changed; this model has its own mechanism.
- **`models/sleeve-counter` imports this file** and re-sizes the mechanism with `configure()`. After changing
  anything here, rebuild both and compare this model's STL hashes if it was meant to stay put.

## Checks the build runs
- Design frame: rims poke 2.5 mm; 1.61 mm wall between the toughness well and the power cavity; 1.95 mm of spacer
  under the rear cavity; neighbours of every value hidden; the tongue on solid spacer in both trays.
- `assembly_check()` stacks the parts **as printed** (face-down parts turned over) and asserts: the tongue is
  0.15 mm inside the divider's slots and the front's groove and doesn't bottom out; both pins fit their sockets;
  hubs have 0.4 mm; each wheel clears its cavity; the aperture the printed parts leave over each wheel is its
  window; all ten values of both wheels sit centred in it.
- `check_mesh.py`: all 165 STLs (33 per design) have `open_edges=0` and fit the bed. Solid volume 34 cm³ (42 g),
  against a hand estimate of 35 cm³.

## Files (`out/`)
- `emblem_counter_<design>_A1.3mf`: the sliced plate for each design. Open it in Bambu Studio, load the four
  spools in the order above, and print from there.
- `<design>/`: the 33 part STLs (`<object>_<n>_<slot>.stl`, mm, laid out as printed) and `slice_args.txt`.
- `designs_preview.png`: the five faces at different values, a nozzle simulation and the back.
- `<design>_preview.png`: one design at larger scale, with its nozzle simulation.
- `parts_preview.png`: back, divider, front underside, both wheels, and a section through the toughness well.
- `text_cache.json` (next to the script): the digit outlines, for builds without the Windows font.
- No STEP: the parts are shapely polygons extruded into meshes, as in the other card models.

## Printing
- Use a clean Textured PEI plate: the whole face is the first layer.
- The plates are sliced with the prime tower off. Switch it on in Bambu Studio if you want one: the parts sit
  clear of the tower's spot (left rear of the bed).

## Rebuild
```powershell
.venv\Scripts\python.exe models\emblem-counter\emblem_counter.py          # all five; or name designs: ... sun moon
cd models\emblem-counter\out\sun
..\..\..\..\.venv\Scripts\python.exe ..\..\..\..\tools\check_mesh.py (Get-ChildItem *.stl).Name
$a = Get-Content slice_args.txt
Invoke-Expression "python ..\..\..\..\tools\slice_bambu.py $a -o ..\emblem_counter_sun_A1.3mf"
```

## History
- 2026-11-22: v1. Two overlapping wheels (power in front, toughness behind) with 12 mm digits, 0–9 each, read as
  a diagonal fraction in a 59.4 × 28.9 mm display plate; five emblem faces in the six Matte spools. Each plate
  about 1 h 20 min, 38–39 g, 6–7 swaps; no slicer warnings. Not printed yet.
- 2026-11-22: derived values moved into `configure()` so `models/sleeve-counter` can reuse the mechanism at
  another size. All 165 STLs are byte-identical, so the 3MFs stand.
- 2026-11-22: re-sliced with the prime tower check in `slice_bambu.py`. The parts were already clear of the tower's
  spot (now by 16.8 mm); geometry, times and weights unchanged.
