#!/usr/bin/env python3
"""
Slice STL files into a ready-to-print Bambu Studio project (.3mf) using the
installed Bambu Studio's own system presets. Each STL that doesn't share a
plate goes onto its own plate (auto-arrange).

Usage:
    python tools\\slice_bambu.py part1.stl [part2.stl ...] -o out\\name_A1.3mf
        [--machine "Bambu Lab A1 0.4 nozzle"]      (0.4 nozzle is the default)
        [--process "0.20mm Standard @BBL A1"]
        [--filament "Bambu PLA Basic @BBL A1"]
        [--bed "Textured PEI Plate"]
        [--set key=value ...]            override process settings (e.g. wall_generator=arachne)
        [--rotate 45]                    one STL: turn it about Z, centre it on the bed and keep it there
                                         (a 250+ mm part on the bed's diagonal)

Multi-colour (AMS): with --assemble, all STLs become PARTS of ONE object, each on its own slot:
    python tools\\slice_bambu.py black.stl red.stl tan.stl cream.stl -o out\\x_A1.3mf
        --assemble --extruders 1,2,3,4 --colors "#241B16,#8E1D19,#B08551,#F0CB9A" [--flush auto]
  The STLs must already be positioned relative to each other (same coordinate frame).
  The summary reports grams per slot and the number of filament changes.

Stdlib only - runs with any Python 3.8+.

Why this script exists (lessons learned):
  * bambu-studio.exe is a GUI-subsystem binary: --help prints nothing, so we
    judge success from the exit code and result.json.
  * System presets use an 'inherits' chain; the CLI wants standalone files, so
    we flatten them first.
  * Without --curr-bed-type the CLI defaults to "Cool Plate" (35 C bed for PLA),
    which is wrong for the A1's stock Textured PEI plate (65 C).
  * The CLI also drops plate_N.gcode and result.json into --outputdir; we slice
    in a temp dir and keep only the .3mf (which already contains the gcode).
  * Multi-colour: a hand-written input 3MF crashes the CLI (access violation), so
    we let the CLI build the assembly itself (--assemble, export only), patch
    the per-part "extruder" keys in its model_settings.config, then slice that.
  * The CLI's default flush matrix is a flat 280 mm^3 for every colour pair. The
    GUI recomputes it from the colours; --flush auto does a similar estimate here.
  * The CLI slices A1 multi-colour jobs with the prime tower off and centres the
    parts, so a large plate can sit on the tower's stored spot (left rear). Switching
    the tower on in the GUI then fails with "conflicts of gcode paths (WipeTower <->
    Assembly)". For --assemble jobs we check that spot and, if needed, shift the
    parts clear of it and slice again.
  * The CLI's arranger lays a long part square to the bed (a 254 mm part ends up 1 mm
    from two edges), even when the STL itself is diagonal, and the CLI's own --rotate
    slices the wrong geometry (half the layers). So --rotate here turns the mesh itself,
    centres it on the bed and slices with --arrange 0, which keeps STL coordinates.
"""
import argparse
import colorsys
import json
import math
import os
import re
import shutil
import struct
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
        # 'include' pulls in template presets: since Bambu Studio 2.x the A1's real start, end, filament-change,
        # layer-change and time-lapse G-code live there. Without them the generic fdm_machine_common G-code is used.
        for inc in layer.get("include") or []:
            if inc not in index:
                sys.exit(f"{kind} preset '{layer['name']}' includes '{inc}', which was not found")
            merged.update({k: v for k, v in index[inc].items() if k not in ("name", "instantiation")})
        merged.update(layer)
    merged.pop("inherits", None)
    merged.pop("include", None)
    merged.update(name=name, **{"from": "system", "instantiation": "true"})
    dest.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    return dest


def flush_volume(src_hex, dst_hex, lo=110, hi=800):
    """Estimated purge (mm^3) to go from one filament colour to another, in the spirit of Bambu
    Studio's colour-based auto-calc: going dark->light costs much more than light->dark, and a
    hue change adds to it. Use the GUI's "Flushing volumes" auto-calc for the authoritative values."""
    def parse(h):
        h = h.lstrip("#")
        return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    a, b = parse(src_hex), parse(dst_hex)
    la = 0.299 * a[0] + 0.587 * a[1] + 0.114 * a[2]
    lb = 0.299 * b[0] + 0.587 * b[1] + 0.114 * b[2]
    ha, sa, _ = colorsys.rgb_to_hsv(*a)
    hb, sb, _ = colorsys.rgb_to_hsv(*b)
    lumi = (lb - la) ** 0.7 * 560 if lb >= la else (la - lb) * 80
    dh = min(abs(ha - hb), 1 - abs(ha - hb)) * 2  # 0..1
    hs = 230 * min(1.0, ((sa - sb) ** 2 + (dh * min(sa, sb)) ** 2) ** 0.5)
    return int(min(hi, lo + (lumi ** 2 + hs ** 2) ** 0.5))


def summarize(path_3mf):
    z = zipfile.ZipFile(path_3mf)
    cfg = json.loads(z.read("Metadata/project_settings.config"))
    print(f"printer : {cfg.get('printer_settings_id')}")
    print(f"process : {cfg.get('print_settings_id')}  (layer {cfg.get('layer_height')} mm, "
          f"infill {cfg.get('sparse_infill_density')}, walls {cfg.get('wall_loops')}, "
          f"{cfg.get('wall_generator')} walls)")
    print(f"filament: {cfg.get('filament_settings_id')}")
    if len(cfg.get("filament_colour", [])) > 1:
        print(f"colours : {cfg.get('filament_colour')}")
        print(f"flush   : {cfg.get('flush_volumes_matrix')} mm^3 (row = from, col = to)")
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
              f"{grams:.1f} g{'  OUTSIDE BED!' if outside else ''}"
              + (f"  warnings: {warns}" if warns else ""))
        gname = f"Metadata/plate_{g('index')}.gcode"
        n_fil = len(cfg.get("filament_colour", []))
        if n_fil > 1 and gname in z.namelist():
            gc = z.read(gname).decode(errors="ignore")
            # Per-slot weights: the gcode header lists one per slot, except that the CLI sometimes
            # drops a slot and shifts the rest (seen on a face-up relief), so only trust a full list.
            # slice_info.config's <filament> entries are mislabelled in that case too.
            w = re.search(r"^; total filament weight \[g\] : (.*)$", gc, re.M)
            w = w.group(1).split(",") if w else []
            if len(w) == n_fil:
                print("   per slot: " + ", ".join(f"{i + 1}={float(x):.2f} g" for i, x in enumerate(w)))
            else:
                print("   per slot: (CLI header incomplete; see the model script's per-slot grams)")
            # one "M620 S<n>A" per filament switch. The A1's start G-code loads the first filament with one
            # too (and purges it), so count from the end of the start G-code on.
            body = gc.split("; MACHINE_START_GCODE_END", 1)[-1]
            changes = len(re.findall(r"^M620 S\d+A", body, re.M))
            # purge = extrusion inside the FLUSH_START..FLUSH_END blocks (relative E, mm of 1.75 filament)
            purge_mm = sum(float(e) for blk in re.findall(r"; FLUSH_START(.*?); FLUSH_END", body, re.S)
                           for e in re.findall(r"^G1 [^;\n]*E([\d.]+)", blk, re.M))
            purge_g = purge_mm * 3.14159 * 0.875 ** 2 / 1000 * 1.24
            print(f"   filament swaps: {changes}, purge waste ~{purge_g:.1f} g (included in the total)")
    print(f"total   : {total_s // 3600}h{total_s % 3600 // 60:02d}m  {total_g:.1f} g")
    return ok


TOWER_MARGIN = 6.0      # mm kept clear round the tower and its brim (its rib walls reach past the corners)
BED_MARGIN = 2.0        # mm the parts keep from the bed's edge when they are shifted


def tower_clearance(path_3mf):
    """How the parts sit against the prime tower's stored spot.
    Returns (gap, shift, text): gap in mm between the parts' bounding box and the tower zone (tower + brim;
    negative = overlap), the (dx, dy) that would move the parts TOWER_MARGIN clear (None if nothing fits),
    and the zone as text."""
    z = zipfile.ZipFile(path_3mf)
    cfg = json.loads(z.read("Metadata/project_settings.config"))
    x0, y0, x1, y1 = json.loads(z.read("Metadata/plate_1.json"))["bbox_all"]
    area = [tuple(float(v) for v in pt.split("x")) for pt in cfg["printable_area"]]
    bed_x, bed_y = max(a[0] for a in area), max(a[1] for a in area)
    tx, ty = float(cfg["wipe_tower_x"][0]), float(cfg["wipe_tower_y"][0])
    brim = float(cfg.get("prime_tower_brim_width", 3))
    zx1, zy0 = tx + float(cfg.get("prime_tower_width", 35)) + brim, ty - brim     # the zone runs to the rear edge
    gap = max(x0 - zx1, zy0 - y1)
    text = f"tower at x {tx:g}-{zx1 - brim:g}, y {ty:g}+ (brim {brim:g})"
    if x0 < tx - brim:
        return gap, None, text + "; the parts reach past its left side"
    options = []
    dy = min(0.0, zy0 - TOWER_MARGIN - y1)             # toward the front
    if y0 + dy >= BED_MARGIN:
        options.append((0.0, dy))
    dx = max(0.0, zx1 + TOWER_MARGIN - x0)             # toward the right
    if x1 + dx <= bed_x - BED_MARGIN:
        options.append((dx, 0.0))
    shift = min(options, key=lambda o: abs(o[0]) + abs(o[1])) if options else None
    return gap, shift, text


def shift_item(path_3mf, dx, dy):
    """Move the (single) build item of a 3MF by (dx, dy)."""
    zin = zipfile.ZipFile(path_3mf)
    items = {n: zin.read(n) for n in zin.namelist()}
    zin.close()
    model = items["3D/3dmodel.model"].decode()

    def move(mo):
        t = mo.group(2).split()
        t[9], t[10] = f"{float(t[9]) + dx:.5f}", f"{float(t[10]) + dy:.5f}"
        return mo.group(1) + " ".join(t) + mo.group(3)
    model, n = re.subn(r'(<item [^>]*transform=")([^"]+)(")', move, model)
    if n != 1:
        sys.exit(f"expected one build item to move, found {n}")
    items["3D/3dmodel.model"] = model.encode()
    with zipfile.ZipFile(path_3mf, "w", zipfile.ZIP_DEFLATED) as zout:
        for k, v in items.items():
            zout.writestr(k, v)


def rotated_copy(stl, deg, bed, dest):
    """Write a copy of a binary STL turned about Z by deg degrees and centred on the bed (bed = x, y size).
    Returns the smallest gap between its bounding box and the bed's edge."""
    data = Path(stl).read_bytes()
    n = struct.unpack_from("<I", data, 80)[0] if len(data) >= 84 else -1
    if len(data) != 84 + 50 * n:
        sys.exit(f"--rotate needs a binary STL: {stl}")
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    recs = [list(struct.unpack_from("<12fH", data, 84 + 50 * i)) for i in range(n)]
    for r in recs:                                   # normal + 3 vertices, each x, y, z
        for k in range(0, 12, 3):
            r[k], r[k + 1] = c * r[k] - s * r[k + 1], s * r[k] + c * r[k + 1]
    xs = [r[k] for r in recs for k in (3, 6, 9)]
    ys = [r[k + 1] for r in recs for k in (3, 6, 9)]
    size = (max(xs) - min(xs), max(ys) - min(ys))
    gap = min(bed[0] - size[0], bed[1] - size[1]) / 2
    if gap < 0:
        sys.exit(f"turned {deg:g} deg the part is {size[0]:.1f} x {size[1]:.1f} mm: "
                 f"too big for the {bed[0]:g} x {bed[1]:g} mm bed")
    dx, dy = bed[0] / 2 - (min(xs) + max(xs)) / 2, bed[1] / 2 - (min(ys) + max(ys)) / 2
    out = bytearray(data[:84])
    for r in recs:
        for k in (3, 6, 9):
            r[k], r[k + 1] = r[k] + dx, r[k + 1] + dy
        out += struct.pack("<12fH", *r)
    dest.write_bytes(out)
    return gap


def run_cli(args, tmp):
    rc = subprocess.run([str(BAMBU_EXE), *args], cwd=tmp).returncode
    result = tmp / "result.json"
    if not result.exists():
        return rc, "(no result.json)"
    res = json.loads(result.read_text())
    # slicer warnings (e.g. "floating regions") are only reported here, not in the 3MF
    for pl in res.get("sliced_plates", []):
        if pl.get("warning_message"):
            print(f"WARNING (plate {pl.get('id')}): {pl['warning_message']}")
    return rc, res.get("error_string")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stl", nargs="+")
    ap.add_argument("-o", "--output", required=True, help="destination .3mf")
    ap.add_argument("--machine", default="Bambu Lab A1 0.4 nozzle")  
    ap.add_argument("--process", default="0.20mm Standard @BBL A1")  
    ap.add_argument("--filament", default="Bambu PLA Basic @BBL A1")  
    ap.add_argument("--bed", default="Textured PEI Plate",
                    help='"Textured PEI Plate", "Cool Plate", "Engineering Plate", "High Temp Plate"')
    ap.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                    help="override a process setting, e.g. wall_generator=arachne (repeatable)")
    ap.add_argument("--rotate", type=float, default=0.0, metavar="DEG",
                    help="one STL: turn it about Z, centre it on the bed and slice it there "
                         "(45 lays a 250+ mm part on the diagonal)")
    ap.add_argument("--assemble", action="store_true",
                    help="load all STLs as parts of ONE object (multi-colour)")
    ap.add_argument("--extruders", help="comma list: filament slot per STL (default 1,2,3...)")
    ap.add_argument("--colors", help='comma list of filament colours, one per slot, e.g. "#000000,#FF0000"')
    ap.add_argument("--flush", default="auto", help='"auto" (estimate from --colors) or "default" (CLI 280s)')
    a = ap.parse_args()

    if not BAMBU_EXE.exists():
        sys.exit(f"Bambu Studio not found at {BAMBU_EXE}")
    stls = [str(Path(s).resolve()) for s in a.stl]
    out = Path(a.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    colors = [c.strip() for c in a.colors.split(",")] if a.colors else []
    extruders = [int(e) for e in a.extruders.split(",")] if a.extruders else list(range(1, len(stls) + 1))
    if a.assemble and len(extruders) != len(stls):
        sys.exit("--extruders needs one slot per STL")
    if a.rotate and (a.assemble or len(stls) != 1):
        sys.exit("--rotate takes exactly one STL and no --assemble")
    n_fil = max(max(extruders) if a.assemble else 1, len(colors), 1)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        m = flatten_preset("machine", a.machine, tmp / "machine.json")
        p = flatten_preset("process", a.process, tmp / "process.json")
        pj = json.loads(p.read_text(encoding="utf-8"))
        for kv in a.set:
            k, v = kv.split("=", 1)
            pj[k] = v
        if n_fil > 1 and len(colors) >= n_fil and a.flush == "auto":
            pj["flush_volumes_matrix"] = [str(0 if i == j else flush_volume(colors[i], colors[j]))
                                          for i in range(n_fil) for j in range(n_fil)]
        p.write_text(json.dumps(pj, indent=2), encoding="utf-8")
        fils = []
        for i in range(n_fil):  # one copy of the filament preset per AMS slot, recoloured
            fp = flatten_preset("filament", a.filament, tmp / f"filament_{i + 1}.json")
            if i < len(colors):
                fj = json.loads(fp.read_text(encoding="utf-8"))
                fj["filament_colour"] = [colors[i]]
                fp.write_text(json.dumps(fj, indent=2), encoding="utf-8")
            fils.append(str(fp))
        common = ["--curr-bed-type", a.bed, "--load-settings", f"{m};{p}",
                  "--load-filaments", ";".join(fils), "--outputdir", str(tmp)]

        models = stls
        placed = None
        if a.rotate:
            # the CLI's arranger would turn the part square to the bed again, so place the mesh ourselves
            area = [tuple(float(v) for v in pt.split("x"))
                    for pt in json.loads(m.read_text(encoding="utf-8"))["printable_area"]]
            bed = (max(pt[0] for pt in area), max(pt[1] for pt in area))
            (tmp / "rotated").mkdir()
            turned = tmp / "rotated" / Path(stls[0]).name       # same file name = same object name
            gap = rotated_copy(stls[0], a.rotate, bed, turned)
            placed = f"turned {a.rotate:g} deg and centred, {gap:.1f} mm clear of the bed's edge"
            models = [str(turned)]
        if a.assemble:
            # pass 1: let Bambu build the one-object/many-parts assembly (export only, no slicing)
            rc, msg = run_cli(["--assemble", "--arrange", "1", "--orient", "0", *common,
                               "--export-3mf", "assembly.3mf", *stls], tmp)
            asm = tmp / "assembly.3mf"
            if rc != 0 or not asm.exists():
                sys.exit(f"Assembling failed: exit {rc}, {msg}")
            # patch each part's filament slot (parts keep the STL file name)
            slot = {Path(s).name: e for s, e in zip(stls, extruders)}
            zin = zipfile.ZipFile(asm)
            items = {n: zin.read(n) for n in zin.namelist()}
            zin.close()
            cfg = items["Metadata/model_settings.config"].decode()

            def patch(mo):
                block = mo.group(0)
                name = re.search(r'key="name" value="([^"]+)"', block).group(1)
                return re.sub(r'(key="extruder" value=")\d+(")', rf"\g<1>{slot[name]}\g<2>", block)
            cfg, n = re.subn(r"<part .*?</part>", patch, cfg, flags=re.S)
            if n != len(stls):
                sys.exit(f"expected {len(stls)} parts in the assembly, found {n}")
            # the object's own filament (default 1) overrides its FIRST part, so match them
            cfg = re.sub(r'(<object id="\d+">\s*<metadata key="name" value="[^"]*"/>)',
                         rf'\g<1>\n    <metadata key="extruder" value="{extruders[0]}"/>', cfg, count=1)
            items["Metadata/model_settings.config"] = cfg.encode()
            with zipfile.ZipFile(asm, "w", zipfile.ZIP_DEFLATED) as zout:
                for k, v in items.items():
                    zout.writestr(k, v)
            (tmp / "result.json").unlink(missing_ok=True)
            models = [str(asm)]

        # A multi-colour assembly keeps the (centred) position pass 1 gave it, so that a shift off the
        # prime tower below is exact; so does a part placed by --rotate. Everything else is arranged by the CLI.
        keep = (a.assemble and n_fil > 1) or bool(a.rotate)
        rc, msg = run_cli(["--arrange", "0" if keep else "1", "--orient", "0", *common, "--slice", "0",
                           "--export-3mf", out.name, *models], tmp)
        produced = tmp / out.name
        if rc != 0 or not produced.exists():
            sys.exit(f"Slicing failed: exit {rc}, {msg}")
        tower = None
        if n_fil > 1:
            gap, shift, where = tower_clearance(produced)
            if gap >= TOWER_MARGIN:
                tower = f"clear by {gap:.1f} mm ({where})"
            elif a.assemble and shift:
                # move the one object out of the tower's zone and slice again, keeping that position
                produced.unlink()
                (tmp / "result.json").unlink(missing_ok=True)
                shift_item(models[0], *shift)
                rc, msg = run_cli(["--arrange", "0", "--orient", "0", *common, "--slice", "0",
                                   "--export-3mf", out.name, *models], tmp)
                if rc != 0 or not produced.exists():
                    sys.exit(f"Slicing failed after moving the parts off the prime tower: exit {rc}, {msg}")
                gap2, _, where = tower_clearance(produced)
                if gap2 < TOWER_MARGIN - 0.1:
                    bb = json.loads(zipfile.ZipFile(produced).read("Metadata/plate_1.json"))["bbox_all"]
                    sys.exit(f"the parts did not move clear of the prime tower (gap {gap2:.1f} mm; asked for "
                             f"{shift}, parts now at {[round(v, 1) for v in bb]}; {where})")
                tower = (f"parts moved {shift[0]:+.1f}, {shift[1]:+.1f} mm off it; now clear by {gap2:.1f} mm "
                         f"({where})")
            else:
                tower = (f"WARNING: no room: the parts are {gap:.1f} mm from the tower zone ({where}). "
                         "Leave the prime tower off, or re-arrange the plate")
        shutil.move(str(produced), out)

    print(f"sliced  : {msg} -> {out}")
    if not summarize(out):
        sys.exit("A part is outside the printable area - split or rotate it.")
    if placed:
        print(f"placed  : {placed}")
    if tower:
        print(f"tower   : {tower}. It is sliced OFF here; switch it on in Bambu Studio if wanted.")
    print("note    : open the .3mf in Bambu Studio and print from there (the CLI leaves "
          "printer_model_id blank). 'bed_temperature_too_high_than_filament' is an "
          "enclosure advisory and can be ignored on the open-frame A1.")


if __name__ == "__main__":
    main()
