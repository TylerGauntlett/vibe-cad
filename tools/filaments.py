"""Filament library: the spools on hand, and named card palettes built from them.

A palette maps the four art slots the vampire cards draw with (ink, blood, gold, paper) to spools.
Two slots may share a spool (e.g. blood + gold both Caramel): `ams()` then merges them into one AMS
slot, so the print uses fewer spools and fewer swaps.

Hex values are Bambu Lab's published swatch colours (PLA Matte table, store.bambulab.com). The real
filament differs a little; Ivory White in particular is a warm off-white, not #FFFFFF.
"""

# name -> (Bambu product line, swatch hex, Bambu Studio filament preset)
MATTE = "Bambu PLA Matte @BBL A1"
BASIC = "Bambu PLA Basic @BBL A1"
FILAMENTS = {
    # the tan/brown set on hand (Bambu Lab PLA Matte)
    "Ivory White":    ("PLA Matte", "#FFFFFF", MATTE),
    "Desert Tan":     ("PLA Matte", "#E8DBB7", MATTE),
    "Caramel":        ("PLA Matte", "#AE835B", MATTE),
    "Terracotta":     ("PLA Matte", "#B15533", MATTE),
    "Dark Chocolate": ("PLA Matte", "#4D3324", MATTE),
    "Charcoal":       ("PLA Matte", "#000000", MATTE),
    # the original card colours (generic stand-ins for black, red, copper, white)
    "Black":          ("PLA Basic", "#1E1A18", BASIC),
    "Red":            ("PLA Basic", "#9B1B1E", BASIC),
    "Copper":         ("PLA Basic", "#B87333", BASIC),
    "White":          ("PLA Basic", "#F4F1EA", BASIC),
}

SLOTS = ("ink", "blood", "gold", "paper")

# name -> (ink, blood, gold, paper), with a one-line description
PALETTES = {
    "original": (("Black", "Red", "Copper", "White"), "black / red / copper on white"),
    "F": (("Dark Chocolate", "Caramel", "Caramel", "Ivory White"),
          "Ivory Sepia: chocolate lines, caramel accents, ivory ground (3 spools)"),
    "G": (("Dark Chocolate", "Terracotta", "Caramel", "Ivory White"),
          "Ivory Sepia + Terracotta: as F, red details in terracotta (4 spools)"),
    "H": (("Charcoal", "Caramel", "Caramel", "Desert Tan"),
          "Black on Parchment: charcoal lines, caramel accents, tan ground (3 spools)"),
    "I": (("Charcoal", "Dark Chocolate", "Caramel", "Desert Tan"),
          "Black on Parchment + Chocolate: as H, red details in chocolate (4 spools)"),
}


def palette(name):
    """[(slot, hex)] for the four art slots, in SLOTS order."""
    spools, _ = PALETTES[name]
    return [(s, FILAMENTS[f][1]) for s, f in zip(SLOTS, spools)]


def ams(name):
    """(spools in AMS order, 1-based AMS slot for each art slot, filament preset) with shared spools merged."""
    spools, _ = PALETTES[name]
    order = list(dict.fromkeys(spools))
    presets = {FILAMENTS[f][2] for f in order}
    return order, [order.index(f) + 1 for f in spools], presets.pop() if len(presets) == 1 else BASIC


def contrast(a, b):
    """WCAG contrast ratio between two hex colours (1 = none, 21 = black on white)."""
    def lum(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


if __name__ == "__main__":
    for n, (spools, desc) in PALETTES.items():
        hexes = dict(palette(n))
        order, _, preset = ams(n)
        print(f"{n:9s} {desc}\n          AMS: {', '.join(order)}  [{preset}]  lines/ground "
              f"{contrast(hexes['ink'], hexes['paper']):.1f}:1, accent/ground {contrast(hexes['gold'], hexes['paper']):.1f}:1")
