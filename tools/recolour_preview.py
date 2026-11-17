#!/usr/bin/env python3
"""Recolour a vampire-card preview into every tools/filaments.py palette, as one comparison sheet.

The cards' `preview()` paints each art slot (ink, blood, gold, paper) in one flat colour, so a render made
with one palette can be repainted into another pixel by pixel: each pixel is matched to its two nearest
source colours and re-blended between the targets (keeping the anti-aliasing). The geometry and fonts are
exactly the render's, so this needs no rebuild (the full build needs the Windows fonts).

    python tools/recolour_preview.py models/vampire-counter/out/counter_preview.png \
        -o models/vampire-counter/out/palettes_preview.png [--source original] [--palettes original,F,G,H,I]

Writes the sheet (columns = palettes: the 1/1 face, the back, the spools and contrast) and, with --each,
a full recoloured preview per palette next to it (<stem>_<P>.png).
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import filaments

KEEP = ["#9aa0a6", "#FFFFFF"]          # the preview's axes background and figure margin stay as they are
SIZE = (3300, 990)                     # preview(): figsize 22 x 6.6 in at 150 dpi
FACE_1, BACK = (23, 76, 656, 915), (2645, 76, 3279, 915)   # panel boxes in that render


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


def font(size, bold=False):
    for f in (["DejaVuSans-Bold.ttf", "arialbd.ttf"] if bold else ["DejaVuSans.ttf", "arial.ttf"]):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def sheet(img, source, names, path):
    src = [h for _, h in filaments.palette(source)]
    cw, ch, pad, head = 316, 420, 18, 92
    W = pad + len(names) * (cw + pad)
    H = head + 2 * (ch + pad) + 250
    out = Image.new("RGB", (W, H), "#FAF8F4")
    d = ImageDraw.Draw(out)
    for j, n in enumerate(names):
        x = pad + j * (cw + pad)
        pal = filaments.palette(n)
        dst = [h for _, h in pal]
        title, desc = n if n == "original" else f"Palette {n}", filaments.PALETTES[n][1]
        d.text((x, 16), title, fill="#222", font=font(26, True))
        d.text((x, 50), desc.split(":")[0].split(" (")[0], fill="#555", font=font(17))
        for i, box in enumerate((FACE_1, BACK)):
            out.paste(recolour(img.crop(box), src, dst).resize((cw, ch), Image.LANCZOS),
                      (x, head + i * (ch + pad)))
        y = head + 2 * (ch + pad)
        spools, _, _ = filaments.ams(n)
        for k, f in enumerate(spools):
            line, hx, _ = filaments.FILAMENTS[f]
            d.rectangle((x, y + k * 34, x + 26, y + k * 34 + 26), fill=hx, outline="#888")
            d.text((x + 36, y + k * 34 + 2), f"{f}  {hx}", fill="#333", font=font(17))
        h = dict(pal)
        d.text((x, y + 4 * 34 + 8), f"lines/ground {filaments.contrast(h['ink'], h['paper']):.1f}:1\n"
               f"accent/ground {filaments.contrast(h['gold'], h['paper']):.1f}:1\n"
               f"red/ground {filaments.contrast(h['blood'], h['paper']):.1f}:1", fill="#444", font=font(16))
    out.save(path)
    print(f"sheet -> {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("preview", help="a card preview PNG from preview() (3300 x 990)")
    ap.add_argument("-o", "--output", required=True, help="comparison sheet PNG")
    ap.add_argument("--source", default="original", help="palette the preview was rendered with")
    ap.add_argument("--palettes", default=",".join(filaments.PALETTES))
    ap.add_argument("--each", action="store_true", help="also write a full recoloured preview per palette")
    a = ap.parse_args()
    img = Image.open(a.preview).convert("RGB")
    if img.size != SIZE:
        raise SystemExit(f"{a.preview} is {img.size}, expected a preview() render of {SIZE}")
    names = [n.strip() for n in a.palettes.split(",")]
    sheet(img, a.source, names, a.output)
    if a.each:
        src = [h for _, h in filaments.palette(a.source)]
        p = Path(a.preview)
        for n in names:
            if n != a.source:
                f = p.with_name(f"{p.stem}_{n}.png")
                recolour(img, src, [h for _, h in filaments.palette(n)]).save(f)
                print(f"preview -> {f}")


if __name__ == "__main__":
    main()
