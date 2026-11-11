#!/usr/bin/env python3
"""
Scaffold a new model folder from templates/.

Usage:
    python tools\\new_model.py ring-tray "Ring tray insert"
Creates models\\ring-tray\\{ring_tray.py, README.md, out\\}
"""
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    slug = re.sub(r"[^a-z0-9]+", "-", sys.argv[1].lower()).strip("-")
    title = sys.argv[2] if len(sys.argv) > 2 else slug.replace("-", " ").title()
    module = slug.replace("-", "_")
    dest = ROOT / "models" / slug
    if dest.exists():
        sys.exit(f"{dest} already exists")
    (dest / "out").mkdir(parents=True)
    subs = {"__TITLE__": title, "__SLUG__": slug, "__MODULE__": module,
            "__DATE__": datetime.date.today().isoformat()}
    for src, name in (("model_template.py", f"{module}.py"), ("model_README.md", "README.md")):
        text = (ROOT / "templates" / src).read_text(encoding="utf-8")
        for k, v in subs.items():
            text = text.replace(k, v)
        (dest / name).write_text(text, encoding="utf-8")
    print(f"Created {dest}\n  edit   models\\{slug}\\{module}.py\n  build  .venv\\Scripts\\python.exe models\\{slug}\\{module}.py")


if __name__ == "__main__":
    main()
