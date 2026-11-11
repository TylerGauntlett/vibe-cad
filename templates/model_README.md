# __TITLE__

## Request
<!-- What was asked for, in the user's words. Attach/describe reference images. -->

## Spec (as built)
| Parameter | Value |
|---|---|
| Overall size | |
| Material / printer | Bambu PLA Basic on Bambu Lab A1 (0.4 mm), Textured PEI |
| Parts / plates | |

## Decisions & interpretations
<!-- Every ambiguity resolved and how (asked the user, or the default chosen). -->

## Files (`out/`)
- `__MODULE__.stl`: print mesh (mm)
- `__MODULE__.step`: solid for CAD/CNC
- `__MODULE___A1.3mf`: sliced Bambu A1 project

## Rebuild
```powershell
.venv\Scripts\python.exe models\__SLUG__\__MODULE__.py
.venv\Scripts\python.exe tools\check_mesh.py models\__SLUG__\out\__MODULE__.stl --png models\__SLUG__\out\preview.png
python tools\slice_bambu.py models\__SLUG__\out\__MODULE__.stl -o models\__SLUG__\out\__MODULE___A1.3mf
```

## History
- __DATE__: created
