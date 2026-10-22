"""KPMG brand kit for the explainer page, taken from brand/extract (the 2026 asset library).

Colours and logo come from 01-colors and 03-logos; the photos are a curated subset of
04-photos, cropped to banners by tools/build_brand_assets.py. The model picks photos by id
(the ids are an enum in the response schema), so only these can ever appear on a page.
Portraits of named people are deliberately left out.
"""
import base64
import functools
import pathlib
from typing import NamedTuple

ASSETS = pathlib.Path(__file__).parent / "assets"

# 2026 palette (brand/extract/01-colors/palette.css)
KPMG_BLUE = "#00338D"
COBALT = "#1E49E2"
DARK_BLUE = "#0C233C"
PACIFIC = "#00B8F5"
LIGHT_BLUE = "#76D2FF"
PALE_BLUE = "#ACEAFF"
PURPLE = "#7213EA"
LIGHT_PURPLE = "#B497FF"
DARK_PURPLE = "#510DBC"
MAGENTA = "#AB0D82"
TINT_20 = "#D2DBF9"
TINT_10 = "#E9EDFC"
TINT_5 = "#F3F6FF"
GREY_60 = "#666666"
GREY_10 = "#E5E5E5"


class Photo(NamedTuple):
    id: str
    source: str  # path under brand/extract/04-photos
    about: str  # what the model reads when choosing
    focus_x: float = 0.5  # where to centre the banner crop, 0 = left, 1 = right


PHOTOS = (
    Photo("flowing-ribbons", "04-technology-and-abstract/cn-impact-plan-2026_p01_17.png",
          "translucent blue and violet ribbons flowing on a light background: flow, waves, change, energy, fluids"),
    Photo("ai-face-data", "04-technology-and-abstract/global-tech-report-2026_p01_01.jpg",
          "a face dissolving into streams of light: artificial intelligence, data, digital identity, the brain", 0.75),
    Photo("neon-portal", "04-technology-and-abstract/global-tech-report-2026_p02_02.jpg",
          "a glowing neon doorway in deep blue space: a new era, gateways, transformation, the future", 0.6),
    Photo("light-swirl", "04-technology-and-abstract/global-tech-report-2026_p11_04.jpg",
          "a figure inside swirling lines of light: networks, signals, electromagnetism, connectivity"),
    Photo("mirror-hall", "04-technology-and-abstract/global-tech-report-2026_p15_05.jpg",
          "glowing glass frames in a mirrored hall: reflection, virtual worlds, digital twins, optics"),
    Photo("walk-through-frames", "04-technology-and-abstract/global-tech-report-2026_p20_06.jpg",
          "a person walking through nested glowing frames: a journey, steps of a process, progress"),
    Photo("frames-in-clouds", "04-technology-and-abstract/global-tech-report-2026_p24_07.jpg",
          "glowing frames floating among clouds: cloud computing, weather, the sky, the atmosphere"),
    Photo("neon-city", "04-technology-and-abstract/global-tech-report-2026_p26_08.jpg",
          "a neon city canyon with a bright gate: cities, infrastructure, internet traffic, speed"),
    Photo("light-tunnel", "04-technology-and-abstract/global-tech-report-2026_p28_09.jpg",
          "light streaks rushing through a frame: speed of light, data transfer, communication, motion"),
    Photo("blue-arcs", "04-technology-and-abstract/thought-leadership-mar-2026_p01_10.jpg",
          "smooth blue concentric arcs: cycles, layers, orbits, sound, abstract structure"),
    Photo("blue-waves", "04-technology-and-abstract/thought-leadership-mar-2026_p04_11.jpg",
          "soft light-blue gradient with thin curves: calm, abstract, general background", 0.8),
    Photo("radar-dial", "04-technology-and-abstract/thought-leadership-mar-2026_p04_12.jpg",
          "a glowing circular dial on deep blue: security, focus, radar, measurement, cybersecurity", 0.7),
    Photo("floating-cubes", "04-technology-and-abstract/thought-leadership-may-2026_p01_13.jpg",
          "floating glossy cubes in blue and magenta: building blocks, data, molecules, blockchain, matter"),
    Photo("medical-hologram", "04-technology-and-abstract/thought-leadership-may-2026_p02_14.jpg",
          "a doctor's hand with a holographic brain and data: medicine, health, biology, the human body"),
    Photo("ribbon-frame", "04-technology-and-abstract/thought-leadership-may-2026_p05_15.jpg",
          "a blue ribbon wave in a frame: sound waves, signals, frequency, flow", 0.85),
    Photo("layered-ribbon", "04-technology-and-abstract/thought-leadership-may-2026_p05_16.jpg",
          "a layered pink and blue ribbon: layers, spectrum, growth, evolution", 0.85),
    Photo("wind-turbines", "05-blue-duotone-banners/thought-leadership-mar-2026_p03_06.jpg",
          "wind turbines by a highway at sunset: energy, electricity, climate, sustainability, transport"),
    Photo("construction-cranes", "05-blue-duotone-banners/thought-leadership-mar-2026_p03_07.jpg",
          "construction cranes at dusk: building, engineering, infrastructure, the economy", 0.8),
    Photo("sprinter", "05-blue-duotone-banners/thought-leadership-mar-2026_p03_05.jpg",
          "a sprinter mid-stride: speed, muscles, the body in motion, competition, performance", 0.75),
    Photo("floating-screens", "05-blue-duotone-banners/thought-leadership-may-2026_p04_15.jpg",
          "floating glowing screens of charts and pictures: dashboards, analytics, media, information", 0.7),
    Photo("knotted-hose", "06-objects-and-textures/dk-annual-report-2025_p12_03.jpg",
          "a metal hose tied in a knot: complexity, tangled problems, tension, materials"),
    Photo("moss-wall", "06-objects-and-textures/dk-annual-report-2025_p02_01.jpg",
          "living moss above wooden slats: nature, plants, ecosystems, sustainability"),
    Photo("glass-atrium", "03-architecture-and-places/dk-annual-report-2025_p29_08.jpg",
          "looking up into a glass atrium roof: structure, engineering, geometry, light"),
    Photo("glass-roofs", "03-architecture-and-places/dk-annual-report-2025_p02_02.jpg",
          "angled glass roofs against the sky: architecture, perspective, geometry"),
)
PHOTO_IDS = tuple(p.id for p in PHOTOS)
DEFAULT_HERO = "blue-arcs"


def catalogue() -> str:
    """The photo list as the model sees it when choosing images."""
    return "\n".join(f"- {p.id}: {p.about}" for p in PHOTOS)


@functools.lru_cache(maxsize=None)
def photo_uri(photo_id: str) -> str:
    data = (ASSETS / "brand" / f"{photo_id}.jpg").read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(data).decode()


@functools.lru_cache(maxsize=None)
def logo_svg(variant: str = "white") -> str:
    """The KPMG logo as inline SVG markup (white for blue backgrounds, blue for white)."""
    svg = (ASSETS / f"kpmg-logo-{variant}.svg").read_text(encoding="utf-8")
    return svg[svg.index("<svg"):]
