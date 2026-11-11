# vibe-cad

Parametric 3D-printable models written in Python ([build123d](https://github.com/gumyr/build123d)),
checked automatically and sliced into ready-to-print projects for a **Bambu Lab A1**.

## Models
| Model | Folder |
|---|---|
| Wave jewelry-box insert | [models/wave-insert](models/wave-insert/README.md) |

## Quickstart
```powershell
# one-time setup (recreates the Python environment)
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# start a new model
python tools\new_model.py ring-tray "Ring tray insert"
.venv\Scripts\python.exe models\ring-tray\ring_tray.py

# check it (watertight, size, fits the 256 mm bed) and render a preview
.venv\Scripts\python.exe tools\check_mesh.py models\ring-tray\out\ring_tray.stl --png models\ring-tray\out\preview.png

# slice into a Bambu A1 project (PLA Basic, 0.20 mm Standard, Textured PEI)
python tools\slice_bambu.py models\ring-tray\out\ring_tray.stl -o models\ring-tray\out\ring_tray_A1.3mf
```
Open the `.3mf` in Bambu Studio, check the plates, and print.

## Requirements
- Windows, Python 3.11
- Bambu Studio installed at `C:\Program Files\Bambu Studio\`
- Optional: Claude Code with the `build123d@vibecad` plugin. `CLAUDE.md` holds the full methodology for AI sessions.
