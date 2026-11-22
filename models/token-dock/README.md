# Token dock: reusable 1/1–9/9 counter base + swappable token cards

## Request
"Build a new version of a token counter combining elements from the following sources into a new model":
an AI-rendered infographic (two windows, two sliders, rack → 8T pinion → 64T number gear) and a hand sketch
(a card with a tab at its bottom edge that plugs into a separate stat block with two number windows).

- sliders instead of wheels to control the power/toughness individually
- a detachable base that can be reused with simple token cards (the base holds the stat information)
- print a fixed number of counters and swap them freely between tokens
- the token should attach to the base strongly enough that it feels robust

Answers to the spec questions:
- Stat display: "Could this be a single 1/1 window (no separate windows for power and toughness), with a control
  for it on the bottom (either a slider or wheel)".
- Card size: full 63 × 88 card.
- Joint: tongue + magnets.
- Card to build: Arcana.

After v1 (base 67.3 mm wide, with side rails): "the back of the counter is much larger on the sides than the card
itself. is this a requirement? can they be the same size so it visually doesn't overlap on the left/right?"

## Spec (as built)
| Parameter | Value |
|---|---|
| Base | **63.0** × 69.4 mm (the card's width), plus 2.0 mm of wheel rim below the bottom edge; 6.0 mm thick at the stat block, 4.0 mm at the shelf |
| Card | 63 × 88 × 2.0 mm, one flat part, plus a 1.4 mm toe along the bottom of its back and two Ø9.6 × 1.0 mm magnet bosses |
| Docked | 63.0 × 105.9 mm. The stat block shows 17.7 mm below the card; the shelf backs the card's lower 51.5 mm; card and block are flush, and nothing shows either side of the card |
| Counter | one window, **1/1 … 9/9**, **7.5 mm** digits (the vampire-counter wheel, the same part as in the one-piece cards: Bahnschrift Bold Condensed, click detent at each value) |
| Control | the wheel's rim at the **bottom edge**, exposed over 21.4 mm. Push it **right** to count up |
| Wheel | Ø 59.0 mm, digit ring r 19.75, 9 V notches (1.3 deep, 35° flanks); reeded rim between notches (0.7 mm slits every 4°) |
| Detent | the vampire-counter arm (26 mm, 1.4 → 2.2 mm taper, Ø2 nub, 0.4 mm preload), leaving the wheel at 110°. 0.40 N seated, 1.47 N over the rim, 0.52 % peak strain, stop at 0.73 % |
| Window | 13.0 × 8.8 mm at the wheel, bevelled out to 15.0 × 12.8 mm at the face (45° above and below, one layer per step); 0.8 mm straight above the wheel |
| Joint | 45° cleat (the block's top edge leans 1.6 mm over the card's toe, 1.2 mm caught) + two bosses in Ø10 shelf holes (0.2 mm clearance), which locate the card sideways |
| Magnets | **Ø6 × 2 mm discs: 2 per base, 2 per card** (not printed). 0.6 mm apart when docked. Estimated hold about 2–2.5 N per pair (not measured) |
| Colours | AMS slots as the other vampire cards: 1 ink `#1E1A18`, 2 blood `#9B1B1E`, 3 gold `#B87333`, 4 paper `#F4F1EA`. The base uses only 1 and 4 |
| Material / printer | Bambu PLA Basic, A1 0.4 mm, 0.20 mm Standard + Arachne, slow first layer, Textured PEI (65 °C) |
| Base plate | back, shelf plate, block and wheel: **45 min, 20.7 g, 3 swaps (~1.6 g purge)**, no slicer warnings |
| Card plate | one arcana card: **37 min, 14.4 g, 6 swaps (~2.2 g purge)**, no slicer warnings |

Not print-tested yet: the fits come from the clearances that worked on vampire-counter (0.15 mm per side, 0.4 mm wheel play).

### Parts
- **back** (printed as it sits): 0.6 mm plate + 2.2 mm spacer with the wheel cavity, Ø6 axle pin, detent arm, 7 glue
  pegs, two magnet pockets. Black edge, crescent and bat inlaid on its back.
- **wheel** (face-down): 1.8 mm disc, digits inlaid black.
- **cover** (printed as it sits): the 1.2 mm shelf plate over the wheel. Two Ø10 holes take the card's bosses.
- **block** (face-down): the 3.2 mm stat block. Black frame, two flourishes, bevelled window.
- **card** (face-down): the arcana scene in the family frame; the footer plate carries a gold crescent between two bats.

### Assembly (base, once)
1. Press a magnet into each pocket **from the back** of the back part until it meets the roof. Add a drop of CA
   behind it. Both magnets the same way up.
2. Lower the wheel onto the pin, digits up, "1/1" at the bottom. Check it clicks through all 9 values.
3. Lay the shelf plate on (pegs and pin into its sockets) with CA on the 3 pegs and along the spacer's top.
4. Lay the block on its 4 pegs with CA on the pegs and the two corner pads. Keep glue away from the wheel.

### Each card
Press a magnet into each boss, flush with its face, with a drop of CA. **Check the polarity against the base
first**: the card must be pulled down, not pushed away.

### Docking
Tilt the card, hook its bottom edge under the block's top edge, and lay it down: the bosses drop into the shelf
and the magnets seat it. Lift the card's top edge to release.

## Decisions & interpretations
- **The rendered mechanism can't be printed at card size**, and neither can sliders with one-digit windows:
  - a rack turning a printable pinion (≥ ~4 mm pitch radius) needs about 45 mm of rack run per stat, so two side by
    side don't fit in 63 mm;
  - a sliding number strip needs 19 digit pitches of run, which leaves ~4 mm digits;
  - the render's "8:1 reduction" is also not one: a rack → pinion → gear train moves the gear's rim as far as the rack.
  These went to the user as three options (fader rows, number tape, rack + wheels). The answer was a fourth: one
  1/1 window with a single control on the bottom, slider or wheel.
- **Wheel, not slider** (my choice between the two offered): the wheel has to be there anyway to show large
  "N/N" digits, so exposing its rim adds no parts. A bottom slider would need a rack, a pinion and an extra
  1.8 mm layer to turn it.
- **The base tucks behind the card.** The Ø59 wheel would make a stat block 62 mm tall, and the docked token
  150 mm. Instead only a 17.7 mm block shows, and the wheel housing lies behind the card's lower half as a shelf.
  This also backs 54 mm of the card, which is most of what makes the joint stiff.
- **Rim at the bottom edge** ("a control for it on the bottom"). Consequences:
  - the window sits straight below the axle, so the value is on the base's centre line;
  - the detent moves to 110°: with 9 notches (40° apart) a notch rests at the bottom, under the thumb, only if the
    detent is 160° from it;
  - the rim has to clear the window by the bevel (2.0), a frame strip (1.35) and the protrusion (2.0).
- **Same width as the card (v1.1).** v1's base was 67.3 mm wide: 2 mm rails either side of the card, and a Ø62
  wheel to make room below the window. That was a choice, not a requirement. At 63 mm:
  - the rails go. The two bosses already locate the card sideways (0.2 mm clearance);
  - the wheel is as large as 1.6 mm side walls allow (Ø59). With 8 mm digits (ring r 21) that leaves 2.5 mm for
    bevel + protrusion; **7.5 mm digits** need a ring of only r 19.75 (searched) and leave 4.0 mm, so the 2 mm
    bevel and 2 mm protrusion both stay. The alternative was 8 mm digits with a 1 mm bevel and 1.5 mm of rim;
  - the card's bottom corners are rounded and the block's top corners are square, so a 3 mm sliver of shelf
    shows at each corner of the seam.
- **Reeded rim** (my addition): only 2 mm of rim shows, and at rest one notch. The 0.7 mm slits give the thumb
  grip; the Ø2 nub drops 0.06 mm into one, so they don't act as detents. `GRIP_W = 0` removes them.
- **Bevelled window.** With the card flush, the block is 3.2 mm thick; a straight window that deep would hide the
  bottom third of the digits at 45°. The bevel leaves 0.8 mm of straight wall, less than the counter's 2.0 mm.
- **"Tongue" became a cleat.** A thin tongue at the card's back can't print face-down (it would float), and a
  tongue at the face needs a lip in front of it, so the block would stand proud. A 45° lap prints on both parts
  without support and keeps the faces flush. The bosses stop the card 0.2 mm before the toe could back out
  (asserted), so the cleat can only release when the card's top is lifted.
- **Magnets: Ø6 × 2**, as offered. The base's pockets open at the back and keep a 0.4 mm roof toward the card, so
  undocking pulls the base magnets against plastic. The card's magnets sit in open bosses and rely on the press fit
  and glue. `MAG_D`, `MAG_T`, `MAG_ROOF` are parameters.
- **Card: 2.0 mm with bosses**, not 2.8 mm with blind pockets: less plastic per card and a thinner token. The card
  rests on its two bosses when it lies alone.
- **Card footer**: with the dial gone, the footer plate carries a gold crescent between two bats.
- **Block ornament**: a lozenge on a rule either side of the window, not bats, since the base serves any card.
- **Base in black and white only**: 3 swaps. The slots match the cards, so the AMS mapping doesn't change.
- **Reuse.** `token_dock.py` imports `vampire_arcana` (scene) and through it `vampire_counter` (frame, title and
  the whole dial). Since v1.2 the dial this base introduced (centred wheel, bottom rim, bevelled window, detent at
  110°, reeded rim, collision check) lives in `vampire_counter.py`, and the one-piece cards use it too. This script
  only deepens the window's bevel (`vc.WIN_BEVEL`) for its thicker block, and swaps in a dial-less
  `frame`/`finish` before calling arcana's scene.
- **Another card**: point `card_regions()` at another scene that calls `vc.frame`/`vc.finish` (vampire-counter,
  vampire-cathedral) and set `CARD_NAME`.
- Tunables: `DIGIT_H` with `DIGIT_R`, `SIDE_WALL`, `PROTRUDE`, `BEVEL_X`/`BEVEL_Y`, `BOSS_CLR`, `CLEAT_GAP`, `MAG_FIT`, and the detent
  parameters in vampire-counter (`PRELOAD`, `NOTCH_FLANK`).

## Checks the build runs
- Design frame: wall, peg, magnet and bevel fits; nub preload; arm strain under 0.8 % at its stop.
- `assembly_check()` rebuilds the token from the parts **as printed** (face-down parts turned over) and asserts:
  no two parts overlap in any z range; the nub is centred in a notch; all 9 values are centred in the window; a
  notch rests at the bottom of the rim; the block catches ≥ 1.0 mm of the card's toe; the card's magnets sit over
  the base's.

## Files (`out/`)
- `token_dock_base_A1.3mf`: the sliced base plate. Open it in Bambu Studio and print from there.
- `token_dock_card_arcana_A1.3mf`: the sliced card plate (4 AMS slots: black, red, copper, white).
- `base/`, `card_arcana/`: one STL per z band (`<part>_<n>_<colour>.stl`, mm, laid out as printed) plus `slice_args.txt`.
- `dock_preview.png`: docked at 1/1, 5/5, 9/9, a nozzle simulation, the bare base, the base's back.
- `parts_preview.png`: back, shelf plate and block underside, wheel, card back.
- `section_preview.png`: side sections through the window and axle, the cleat, and a magnet.
- No STEP: the parts are shapely polygons extruded into meshes (as in the other vampire models).

## Rebuild
```powershell
.venv\Scripts\python.exe models\token-dock\token_dock.py
cd models\token-dock\out\base
..\..\..\..\.venv\Scripts\python.exe ..\..\..\..\tools\check_mesh.py (Get-ChildItem *.stl).Name
$a = Get-Content slice_args.txt
Invoke-Expression "python ..\..\..\..\tools\slice_bambu.py $a -o ..\token_dock_base_A1.3mf"
cd ..\card_arcana
$a = Get-Content slice_args.txt
Invoke-Expression "python ..\..\..\..\tools\slice_bambu.py $a -o ..\token_dock_card_arcana_A1.3mf"
```

## History
- 2026-11-12: v1. Base (back, wheel, shelf plate, block) with a bottom-edge thumbwheel and one bevelled 1/1–9/9
  window; arcana token card with a cleat toe and two magnet bosses. Base 50 min, 23.4 g, 3 swaps; card 37 min,
  14.4 g, 6 swaps; no slicer warnings. Not printed yet.
- 2026-11-12: v1.1, base narrowed from 67.3 to 63.0 mm so it no longer shows either side of the card: rails removed,
  wheel Ø62.3 → Ø59.0, digits 8.0 → 7.5 mm (ring r 21 → 19.75) to keep the 2 mm bevel and 2 mm rim protrusion.
  Base 45 min, 20.7 g, 3 swaps; card unchanged in time and weight (its bosses moved with the base's magnets).
  No slicer warnings. Not printed yet.
- 2026-11-12: v1.2, no geometry change: the dial moved into `vampire_counter.py` so the one-piece cards share it.
  All 38 STLs are byte-identical to v1.1, so the v1.1 3MFs stand.
