"""Builds the small web versions of the KPMG brand photos the explainer page can show.

Source: brand/extract (the KPMG 2026 asset library). Output: agent/assets/brand/<id>.jpg,
800 x 320 banner crops (the 2.5:1 card-banner shape of the thought-leadership decks), small
enough to inline several per page under GE's per-message limit. Run from the repo root:
    python tools/build_brand_assets.py
The catalogue (ids, descriptions, themes) lives in agent/brand.py. Also writes the line icons
from 07-diagrams/icons to agent/assets/icons.
"""
import pathlib
import re
import sys

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from agent.brand import PHOTOS  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "brand" / "extract" / "04-photos"
OUT = ROOT / "agent" / "assets" / "brand"
W, H = 800, 320


def crop(im: Image.Image, focus_x: float, focus_y: float = 0.5) -> Image.Image:
    """Scale to cover W x H, then crop around focus_x / focus_y (0 = left/top edge, 1 = right/bottom)."""
    scale = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left = round((im.width - W) * focus_x)
    top = round((im.height - H) * focus_y)
    return im.crop((left, top, left + W, top + H))


def icons() -> None:
    """The six line icons from 07-diagrams, cleaned for inline use: metadata and fixed size
    removed, stroke set to currentColor so they follow the page's colour (and dark mode)."""
    out = ROOT / "agent" / "assets" / "icons"
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted((ROOT / "brand" / "extract" / "07-diagrams" / "icons").glob("icon-*-blue.svg")):
        s = re.sub(r"<metadata>.*?</metadata>|<!--.*?-->", "", f.read_text(encoding="utf-8"), flags=re.S)
        s = re.sub(r'\s+xmlns:c2pa="[^"]*"', "", s)
        s = re.sub(r'\s(width|height)="[^"]*"', "", s, count=2).replace('stroke="#00338D"', 'stroke="currentColor"')
        (out / f"{f.name[5:-9]}.svg").write_text(re.sub(r">\s+<", "><", s).strip(), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for p in PHOTOS:
        im = Image.open(SRC / p.source).convert("RGB")
        crop(im, p.focus_x, p.focus_y).save(OUT / f"{p.id}.jpg", quality=72, optimize=True, progressive=True)
    total = sum(f.stat().st_size for f in OUT.glob("*.jpg"))
    print(f"{len(PHOTOS)} photos, {total // 1024} KB")
    icons()


if __name__ == "__main__":
    main()
