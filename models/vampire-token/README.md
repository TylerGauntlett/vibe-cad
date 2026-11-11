# Vampire token card (4-colour AMS)

## Request
"Take the following image of a pretend Magic: The Gathering token card and make a 3D printable
version out of it. Assume I have 4 colour options (a Bambu Lab A1 printer with AMS)."
Follow-up: "Consider how the .3mf might be optimized to save on colour switching, e.g. different
levels for different colours, or printing all parts of the same colour first (per layer)."

Source art: `source/vampire_token_art.png` (1060 × 1484 px, sepia + red ink style).

## Spec (as built)
| Parameter | Value |
|---|---|
| Card | 63 × 88 mm (standard trading card), 3 mm corner radius |
| Colours (AMS slots) | 1 black `#241B16`, 2 red `#8E1D19`, 3 tan `#B08551`, 4 cream `#F0CB9A` (k-means clusters of the art) |
| Detail limits | strokes ≥ 0.15 mm kept (Arachne widens them to a 0.34 mm bead), specks < 0.04 mm² dropped |
| Material / printer | Bambu PLA Basic, A1 0.4 mm, 0.20 mm Standard + **Arachne walls**, Textured PEI (65 °C) |
| Plates | 1 |

### Two deliverables
| | `flat-light` | `relief` (**fewest swaps**) |
|---|---|---|
| Orientation | face-down: image on the textured PEI side, mirrored | face-up, reads directly |
| Thickness | 1.6 mm, flat | 2.0 mm (1.0 mm cream base + 3 colour bands; black ink raised 1.0 mm) |
| Z bands | 0–0.2 all 4 colours · 0.2–0.4 black/red/cream · 0.4–1.6 cream | 0–1.0 cream · 1.0–1.2 tan · 1.2–1.6 red · 1.6–2.0 black |
| Filament swaps | 5 | **3** (all light → dark) |
| Purge waste | ~1.8 g | **~0.5 g** |
| Print | 41 min, 12.7 g | 42 min, 11.9 g |
| Model grams per slot | black 1.6, red 0.5, tan 0.1, cream 8.8 | black 1.6, red 2.1, tan 1.2, cream 6.9 |
| Look | smooth, textured-PEI sheen, like a printed card | woodcut / linocut, tactile, top-surface line texture |

Baseline for comparison (layout `flat-black`, the first build: 0.6 mm 4-colour face on a black backing): **9 swaps, 2.5 g purge, 57 min, 13.4 g**.

## Decisions & interpretations
- **Size**: real card size, so it works as a game token. For more detail, scale `CARD_W`/`CARD_H`; the nozzle, not the art, limits the detail.
- **Palette**: k = 4 clustering of the art gives black / dark red / tan / cream. The art is sepia, so its "silver" armour is really tan + cream and needs no grey. The hex values are the art's, so in Bambu Studio set each slot to your actual spool (closest PLA Basic: Black, Red or Maroon Red, Gold or Bronze for tan, Beige for cream).
- **Clean-up**: a 0.3 mm morphological opening wiped out the armour highlights and the thin gold frame lines, so it was relaxed to 0.15 mm, with Arachne printing the thin strokes. The cathedral's dark greys merge into black: a 4-colour limit.
- **Colour-swap optimization** (the follow-up):
  - Bambu Studio *already* prints all regions of one filament per layer and chains layers (each layer starts with the previous layer's last filament). So swaps per layer = (filaments in that layer) − 1, and the only real lever is **how many colours share a layer**.
  - The A1 profile has **no prime tower**: every swap purges into the chute, and **dark → light costs about 3× light → dark** (e.g. black → cream ≈ 550 mm³ vs cream → black ≈ 170 mm³).
  - `flat-light`: a cream backing lets light colours read correctly at one layer, so only black and red get a 2nd layer for opacity. That gives 2 mixed layers instead of 3, and 5 swaps instead of 9.
  - `relief`: one Z band per colour, ordered light → dark. No layer has two colours, so there are 3 swaps in total, all in the cheap direction. This is the minimum possible for 4 colours.
  - **Batching amortizes swaps**: swaps happen per layer, not per object, so N tokens on one plate still cost 5 (flat) or 3 (relief) swaps.
- **Flush volumes**: the CLI's default is a flat 280 mm³ for every pair, so `slice_bambu.py --flush auto` writes a colour-aware estimate. For authoritative values, click *Flushing volumes → auto-calculate* in Bambu Studio after setting your real spool colours.
- **No STEP**: this is raster art turned into a mesh (thousands of traced islands). A STEP of it would be huge and useless for CAD, so the deviation from the usual "always export STEP" rule is deliberate. The model is not built with build123d for the same reason: it uses shapely + trimesh.

## Files (`out/`)
- `vampire_token_flat-light_A1.3mf`, `vampire_token_relief_A1.3mf`: sliced A1 projects, 4 AMS slots. Open in Bambu Studio, map slots to your spools, and print from there.
- `flat-light/`, `relief/`: the part STLs (`vt_<band>_<colour>.stl`, mm, shared coordinate frame) plus `slice_args.txt`.
- `colour_preview.png`: original vs. the 4-colour print-resolution face. `relief_preview.png`: Bambu's plate render.

## Rebuild
```powershell
.venv\Scripts\python.exe models\vampire-token\vampire_token.py            # flat-light + relief (add flat-black to compare)
.venv\Scripts\python.exe tools\check_mesh.py models\vampire-token\out\relief\*.stl
cd models\vampire-token\out\relief
python ..\..\..\..\tools\slice_bambu.py <contents of slice_args.txt> -o ..\vampire_token_relief_A1.3mf
```

## History
- 2026-11-11: v1, face-down card with a 0.6 mm 4-colour face on black (9 swaps).
- 2026-11-11: v2, colour-swap optimization: `flat-light` (5 swaps) and `relief` (3 swaps) layouts. `slice_bambu.py` gained `--assemble/--extruders/--colors/--flush/--set`.
