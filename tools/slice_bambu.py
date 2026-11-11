#!/usr/bin/env python3
"""
Slice STL files into a ready-to-print Bambu Studio project (.3mf) using the
installed Bambu Studio's own system presets. Each STL that doesn't share a
plate goes onto its own plate (auto-arrange).

Usage:
    python tools\\slice_bambu.py part1.stl [part2.stl ...] -o out\\name_A1.3mf
        [--machine "Bambu Lab A1 0.4 nozzle"]
        [--process "0.20mm Standard @BBL A1"]
        [--filament "Bambu PLA Basic @BBL A1"]
        [--bed "Textured PEI Plate"]

Stdlib only - runs with any Python 3.8+.

Why this script exists (lessons from the first project):
  * bambu-studio.exe is a GUI-subsystem binary: --help prints nothing, so we
    judge success from the exit code and result.json.
  * System presets use an 'inherits' chain; the CLI wants standalone files, so
    we flatten them first.
  * Without --curr-bed-type the CLI defaults to "Cool Plate" (35 C bed for PLA),
    which is wrong for the A1's stock Textured PEI plate (65 C).
  * The CLI also drops plate_N.gcode and result.json into --outputdir; we slice
    in a temp dir and keep only the .3mf (which already contains the gcode).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

BAMBU_EXE = Path(r"C:\Program Files\Bambu Studio\bambu-studio.exe")
PRESET_ROOT = Path(os.environ.get("APPDATA", "")) / "BambuStudio" / "system" / "BBL"


def flatten_preset(kind, name, dest):
    index = {}
    for f in (PRESET_ROOT / kind).rglob("*.json"):
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(j, dict) and "name" in j:
            index[j["name"]] = j
    if name not in index:
        close = [n for n in index if name.split("@")[0].strip().lower() in n.lower()][:10]
        sys.exit(f"{kind} preset '{name}' not found. Similar: {close}")
    chain, cur = [], index[name]
    while True:
        chain.append(cur)
        parent = cur.get("inherits")
        if not parent:
            break
        cur = index[parent]
    merged = {}
    for layer in reversed(chain):
        merged.update(layer)
    merged.pop("inherits", None)
    merged.update(name=name, **{"from": "system", "instantiation": "true"})
    dest.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return dest


def summarize(path_3mf):
    z = zipfile.ZipFile(path_3mf)
    cfg = json.loads(z.read("Metadata/project_settings.config"))
    print(f"printer : {cfg.get('printer_settings_id')}")
    print(f"process : {cfg.get('print_settings_id')}  (layer {cfg.get('layer_height')} mm, "
          f"infill {cfg.get('sparse_infill_density')}, walls {cfg.get('wall_loops')})")
    print(f"filament: {cfg.get('filament_settings_id')}")
    print(f"bed     : {cfg.get('curr_bed_type')}")
    info = z.read("Metadata/slice_info.config").decode()
    total_s, total_g, ok = 0, 0.0, True
    for plate in re.findall(r"<plate>(.*?)</plate>", info, re.S):
        g = lambda k: (re.search(rf'key="{k}" value="([^"]*)"', plate) or [None, ""])[1]
        objs = re.findall(r'<object [^>]*name="([^"]+)"', plate)
        secs, grams = int(g("prediction") or 0), float(g("weight") or 0)
        total_s, total_g = total_s + secs, total_g + grams
        outside = g("outside") == "true"
        ok &= not outside
        warns = re.findall(r'<warning msg="([^"]+)"', plate)
        print(f"plate {g('index')}: {', '.join(objs)}  {secs // 3600}h{secs % 3600 // 60:02d}m  "
              f"{grams:.0f} g{'  OUTSIDE BED!' if outside else ''}"
              + (f"  warnings: {warns}" if warns else ""))
    print(f"total   : {total_s // 3600}h{total_s % 3600 // 60:02d}m  {total_g:.0f} g")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl", nargs="+")
    ap.add_argument("-o", "--output", required=True, help="destination .3mf")
    ap.add_argument("--machine", default="Bambu Lab A1 0.4 nozzle")
    ap.add_argument("--process", default="0.20mm Standard @BBL A1")
    ap.add_argument("--filament", default="Bambu PLA Basic @BBL A1")
    ap.add_argument("--bed", default="Textured PEI Plate",
                    help='"Textured PEI Plate", "Cool Plate", "Engineering Plate", "High Temp Plate"')
    a = ap.parse_args()

    if not BAMBU_EXE.exists():
        sys.exit(f"Bambu Studio not found at {BAMBU_EXE}")
    stls = [str(Path(s).resolve()) for s in a.stl]
    out = Path(a.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        m = flatten_preset("machine", a.machine, tmp / "machine.json")
        p = flatten_preset("process", a.process, tmp / "process.json")
        f = flatten_preset("filament", a.filament, tmp / "filament.json")
        cmd = [str(BAMBU_EXE), "--arrange", "1", "--orient", "0",
               "--curr-bed-type", a.bed,
               "--load-settings", f"{m};{p}", "--load-filaments", str(f),
               "--slice", "0", "--outputdir", str(tmp),
               "--export-3mf", out.name, *stls]
        rc = subprocess.run(cmd, cwd=tmp).returncode
        result = tmp / "result.json"
        msg = json.loads(result.read_text()).get("error_string") if result.exists() else "(no result.json)"
        produced = tmp / out.name
        if rc != 0 or not produced.exists():
            sys.exit(f"Slicing failed: exit {rc}, {msg}")
        shutil.move(str(produced), out)

    print(f"sliced  : {msg} -> {out}")
    if not summarize(out):
        sys.exit("A part is outside the printable area - split or rotate it.")
    print("note    : open the .3mf in Bambu Studio and print from there (the CLI leaves "
          "printer_model_id blank). 'bed_temperature_too_high_than_filament' is an "
          "enclosure advisory and can be ignored on the open-frame A1.")


if __name__ == "__main__":
    main()
