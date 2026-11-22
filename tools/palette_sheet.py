#!/usr/bin/env python3
"""Compare a vampire card in every tools/filaments.py palette on one sheet.

Build each palette's preview first (the card writes <card>_preview_<P>.png when VAMPIRE_PALETTE=P):
    $env:VAMPIRE_PALETTE="H"; .venv\\Scripts\\python.exe models\\vampire-counter\\vampire_counter.py
then:
    python tools/palette_sheet.py models/vampire-counter/out/counter_preview.png \
        -o models/vampire-counter/out/palettes_preview.png [--palettes original,F,G,H,I]

Columns = palettes: the first face panel, the back, the spools and contrast ratios. The panels are found
by the preview's grey axes background, so the figure size doesn't matter. A palette with no render of its
own is repainted from the original render (each slot is one flat colour, so a pixel is matched to its two
nearest source colours and re-blended between the targets) and marked "recoloured".
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import filaments

AXES_BG = "#9aa0a6"
KEEP = [AXES_BG, "#FFFFFF"]            # axes background and figure margin stay as they are when recolouring


def rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)


def recolour(img, src, dst):
    """Repaint an RGB image from the src hex list to the dst hex list (same order; KEEP colours stay)."""
    a = np.asarray(img.convert("RGB"), float)
    ref = np.stack([rgb(c) for c in src + KEEP])
    tgt = np.stack([rgb(c) for c in dst + KEEP])
    d = np.sqrt(((a[:, :, None, :] - ref[None, None]) ** 2).sum(-1))
    o = np.argsort(d, -1)[..., :2]
    d1 = np.take_along_axis(d, o[..., :1], -1)[..., 0]
    d2 = np.take_along_axis(d, o[..., 1:], -1)[..., 0]
    w = (d2 / (d1 + d2 + 1e-9))[..., None]
    out = w * tgt[o[..., 0]] + (1 - w) * tgt[o[..., 1]]
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


def panels(img):
    """Boxes (x0, y0, x1, y1) of the preview's axes panels, left to right, found by their grey background."""
    a = np.asarray(img.convert("RGB"), int)
    grey = (np.abs(a - rgb(AXES_BG).astype(int)).sum(-1) < 6)
    cols = grey.sum(0) > 3                  # the card leaves a thin grey margin above and below
    rows = np.flatnonzero(grey.sum(1) > 20)
    edges = np.flatnonzero(np.diff(np.r_[0, cols.astype(int), 0]))
    return [(int(x0), int(rows[0]), int(x1), int(rows[-1]) + 1) for x0, x1 in zip(edges[::2], edges[1::2])]


def font(size, bold=False):
    for f in (["DejaVuSans-Bold.ttf", "arialbd.ttf"] if bold else ["DejaVuSans.ttf", "arial.ttf"]):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("preview", help="the card's original-palette preview PNG (<card>_preview.png)")
    ap.add_argument("-o", "--output", required=True, help="comparison sheet PNG")
    ap.add_argument("--palettes", default=",".join(filaments.PALETTES))
    a = ap.parse_args()
    base = Path(a.preview)
    orig = Image.open(base).convert("RGB")
    src = [h for _, h in filaments.palette("original")]
    names = [n.strip() for n in a.palettes.split(",")]

    boxes = panels(orig)
    face, back = boxes[0], boxes[-1]
    cw = 316
    ch = round(cw * (face[3] - face[1]) / (face[2] - face[0]))
    pad, head = 18, 92
    W = pad + len(names) * (cw + pad)
    out = Image.new("RGB", (W, head + 2 * (ch + pad) + 250), "#FAF8F4")
    d = ImageDraw.Draw(out)
    for j, n in enumerate(names):
        x = pad + j * (cw + pad)
        pal = filaments.palette(n)
        f = base if n == "original" else base.with_name(f"{base.stem}_{n}.png")
        if f.exists():
            img, note = Image.open(f).convert("RGB"), ""
        else:
            img, note = recolour(orig, src, [h for _, h in pal]), " (recoloured)"
        d.text((x, 16), ("original" if n == "original" else f"Palette {n}") + note, fill="#222", font=font(26, True))
        d.text((x, 50), filaments.PALETTES[n][1].split(":")[0].split(" (")[0], fill="#555", font=font(17))
        for i, box in enumerate((face, back)):
            out.paste(img.crop(box).resize((cw, ch), Image.LANCZOS), (x, head + i * (ch + pad)))
        y = head + 2 * (ch + pad)
        spools, _, _ = filaments.ams(n)
        for k, s in enumerate(spools):
            _, hx, _ = filaments.FILAMENTS[s]
            d.rectangle((x, y + k * 34, x + 26, y + k * 34 + 26), fill=hx, outline="#888")
            d.text((x + 36, y + k * 34 + 2), f"{s}  {hx}", fill="#333", font=font(17))
        h = dict(pal)
        d.text((x, y + 4 * 34 + 8), f"lines/ground {filaments.contrast(h['ink'], h['paper']):.1f}:1\n"
               f"accent/ground {filaments.contrast(h['gold'], h['paper']):.1f}:1\n"
               f"red/ground {filaments.contrast(h['blood'], h['paper']):.1f}:1", fill="#444", font=font(16))
    out.save(a.output)
    print(f"sheet -> {a.output}")


if __name__ == "__main__":
    main()
