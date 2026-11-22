# iPhone Duo travel MagSafe stand (print-in-place, folds flat)

## Request
Two reference products (an adjustable clamp stand and a fixed "Minimal MagSafe Dock" for the iPhone Duo), neither
of which collapses. Design a new stand that folds flat for travel, holds a MagSafe charger placed for the
**unfolded** Duo, has working hinges for quick setup and tear-down, favours compactness and stability, and has the
clearances worked out so the moving parts print separated.

Answers from the user: third-party puck **Ø56 × 7 mm**, **print-in-place** hinges, **bare phone** (no case).

## How it works
One 8 mm slab, printed assembled, made of three bodies:

| Body | Role |
|---|---|
| **Base** | Front bar with a trough that carries the phone's bottom edge, plus two rails that lie on the table |
| **Panel** | Hinged to the base (hinge A). Holds the puck behind a front lip; cable tunnel out the back |
| **Leg** | Hinged to the panel's top-left (hinge K). Its ear drops into one of four saddles on the left rail |

- **Open:** lift the panel by its top-right corner (finger gap beside the right rail) until it is upright, flick
  the leg's foot backward, lower the panel. The ear slides back along the rail and drops into the first saddle
  (73°). Lift a little and move it back a saddle for 70°, 65° or 60°.
- **Close:** lift the panel, fold the leg into it until it clicks, lay the panel down until it clicks.
- **Why it suits the unfolded Duo:** the MagSafe ring sits in one half only, so on an ordinary stand the open phone
  hangs off-centre and tips. Here the puck is offset to the ring, the phone's weight rests in the trough along its
  bottom edge instead of on the magnets, and the leg and hinge K sit behind the cover-screen half, so nothing
  stands in front of the camera half above the ring.

## Spec (as built)
| Parameter | Value |
|---|---|
| Folded size | 122.0 × 109.7 × 8.0 mm (the folded Duo is 117.8 × 84.1 × 11.3 mm) |
| Phone | iPhone Duo unfolded, landscape: 164.6 × 117.8 × 5.2 mm, 254 g |
| Viewing angles | 60° / 65° / 70° / 73° from horizontal |
| Puck pocket | Ø56.3 through-hole, loaded from the back, 4 crush ribs (0.15 mm interference), front lip 0.8 mm |
| Puck position | Centre 41.15 mm right of the phone's centre and 58.9 mm above its bottom edge (assumed, see below) |
| Phone position | Centred 17.3 mm left of the stand's centre: overhangs 38.6 mm on the left, 4 mm on the right |
| Cable tunnel | 13 × 29 mm, 6.8 mm high, from the pocket toward the left, open at the back, roofed at the front |
| Hinges | Ø4 pin in Ø4.8 bore (0.4 mm radial), knuckles 0.4 mm apart, axes at mid-thickness |
| Part-to-part gap | 0.5 mm in plan; 0.32 mm at the two detents |
| Material / printer | Bambu PLA Basic on Bambu Lab A1 (0.4 mm), Textured PEI, 0.20 mm Standard, no supports |
| Parts / plates | 1 piece, 1 plate: **1 h 13 min, 41.9 g** |
| Stability (estimate, 65°) | Tips back at about 2.5 N pushed on the phone's top edge; 5 N pressed on its far-left edge |

## Clearances and how they were checked
`assembly_check()` in the model runs on every build and must print `ALL CHECKS PASSED`:
- Folded: each body is one valid solid, no pair overlaps, minimum gap 0.50 mm (0.32 mm inside the detent dimples),
  everything within z = 0..8.
- Opening: panel with the leg folded in clears the base from 0° to 95° (minimum 0.40 mm).
- Leg swing: with the panel upright the leg clears base and panel on its way back (ear passes 1.3 mm over the ledge).
- Each of the four angles: leg seated in its saddle, no body collides with another, with the phone or with the puck,
  and the phone's bottom corner sits in the trough.

Hinge details that make print-in-place work:
- Knuckles are round with a 45° foot so they start on the bed without a curled first layer.
- Pins have a flat underside on a layer line, 0.6 mm (3 layers) above the bore floor, and bridge 8.8 mm at most.
- Bore roofs are truncated teardrops, so they do not sag onto the pin.
- Detents are 45° cones, printable without support.

## Decisions & interpretations
- **Single slab, parts nested in plan** rather than stacked plates: 8 mm folded, and nothing prints over a gap.
- **One leg, on the left.** A leg on each side needs hinge K to run across the top of the puck, right where the
  camera plateau may sit. The panel is stiff enough (8 mm) to be propped at one corner; hinge A spans its full width.
- **Leg length 86 mm** is the most that still swings through under an upright panel; that caps the steepest
  angle at 73°. Flatter than 60° would need longer rails.
- **Puck loads from the back against a front lip**, because pulling the phone off pulls the puck forward with it.
  The puck face ends up about 0.85 mm behind the panel face (less than a thin case).
- **Cable leaves through the panel toward the left**, behind the cover-screen half, and drops out the open back of
  the base. A USB-C plug fits the tunnel; unplug it (or let a fixed cable hang out the back) to fold.
- **Ring on the viewer's right.** `RING_SIDE = -1` mirrors the whole stand.
- **Right rail is as long as the left** for tip-back stability; the space it leaves above the panel's low right
  corner is the finger pull.

## Assumptions to check before printing
1. **Ring position.** Apple does not publish it; the model assumes the middle of one half (41.15 mm from the phone's
   centre, 58.9 mm above the bottom edge). Measure with the puck snapped on and set `RING_X` / `RING_Z`.
2. **Puck.** "56 × 7" was given; measure the diameter to 0.1 mm. `POCKET_CLEAR` / `RIB` set the fit. If it is
   loose, a strip of double-sided tape on the rim fixes it.
3. **Camera plateau.** The panel's right side stops 28 mm below the phone's top edge and hinge K starts left of the
   phone's spine, so a plateau anywhere above the ring on the ring half is clear. Not verified against a phone.

## Printing and first use
- Open `duo_travel_stand_A1.3mf` in Bambu Studio and print from there. No supports, no brim.
- Free the joints before forcing anything: flex the panel a few degrees up and down first, then the leg. The first
  movement breaks a few strands under the pins.
- If a joint is fused, raise `HG` and `GAP` by 0.1 mm and rebuild.
- Stick-on silicone dots under the rails and front bar help on slick tables.

## Files (`out/`)
- `duo_travel_stand.stl`: print mesh, folded, all three bodies (mm)
- `duo_travel_stand.step`: the same as exact solids
- `duo_travel_stand_deployed_view.step`: opened at 65°, for viewing only
- `duo_travel_stand_A1.3mf`: sliced Bambu A1 project
- `preview.png` (folded), `deployed.png` (opened, phone ghosted)

## Rebuild
```powershell
.venv\Scripts\python.exe models\duo-travel-stand\duo_travel_stand.py
.venv\Scripts\python.exe tools\check_mesh.py models\duo-travel-stand\out\duo_travel_stand.stl --png models\duo-travel-stand\out\preview.png
python tools\slice_bambu.py models\duo-travel-stand\out\duo_travel_stand.stl -o models\duo-travel-stand\out\duo_travel_stand_A1.3mf
```

## History
- 2026-11-16: v1 created and sliced. Not printed.
