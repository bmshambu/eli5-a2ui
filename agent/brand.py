"""KPMG brand kit for the explainer page, taken from brand/extract (the 2026 asset library).

Colours and logo come from 01-colors and 03-logos; the photos are a curated subset of
04-photos, cropped to banners by tools/build_brand_assets.py. The model picks photos by id
(the ids are an enum in the response schema), so only these can ever appear on a page.
Executive portraits (01-executive-portraits) are deliberately left out (Sharya, 2026-10-22);
people-at-work and stock people photos are in.
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
    focus_y: float = 0.5  # 0 = top, 1 = bottom (people photos sit higher to keep faces in)


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
    # People at work, places, and more banners (added 2026-10-22; no executive portraits)
    Photo("bike-commute", "02-people-at-work/dk-annual-report-2025_p01_01.jpg",
          "two colleagues walking bikes to the office: commuting, sustainability, work-life balance, mobility", 0.5, 0.6),
    Photo("team-lounge", "02-people-at-work/dk-annual-report-2025_p26_15.jpg",
          "three colleagues talking in a lounge: teamwork, meetings, collaboration, advice", 0.5, 0.28),
    Photo("one-to-one", "02-people-at-work/dk-annual-report-2025_p10_05.jpg",
          "two people in a relaxed one-to-one conversation: coaching, feedback, clients, HR, wellbeing", 0.4, 0.35),
    Photo("team-balcony", "02-people-at-work/dk-annual-report-2025_p11_06.jpg",
          "a team chatting on an office balcony: culture, people, engagement, workplace", 0.5, 0.3),
    Photo("overhead-meeting", "02-people-at-work/dk-annual-report-2025_p13_08.jpg",
          "colleagues meeting seen from above in a bright atrium: organisation, governance, decisions", 0.4, 0.45),
    Photo("desk-discussion", "02-people-at-work/dk-annual-report-2025_p14_09.jpg",
          "a team discussing at a desk with screens: projects, analysis, audit work, problem solving", 0.55, 0.35),
    Photo("sofa-chat", "02-people-at-work/dk-annual-report-2025_p16_10.jpg",
          "colleagues laughing together on a sofa: inclusion, diversity, wellbeing, informal learning", 0.5, 0.35),
    Photo("laptop-meeting", "02-people-at-work/dk-annual-report-2025_p16_11.jpg",
          "two colleagues working at a table with laptops: hybrid work, planning, consulting", 0.5, 0.35),
    Photo("garden-walk", "02-people-at-work/dk-annual-report-2025_p20_13.jpg",
          "colleagues walking with bikes through a green courtyard: ESG, environment, healthy cities", 0.5, 0.5),
    Photo("waterfront-walk", "02-people-at-work/dk-annual-report-2025_p21_14.jpg",
          "three people walking along a harbour: strategy talk, leadership, ports, trade", 0.5, 0.4),
    Photo("harbour-stroll", "02-people-at-work/dk-annual-report-2025_p30_16.jpg",
          "two colleagues walking by the water: mentoring, careers, conversation", 0.5, 0.35),
    Photo("kpmg-office", "03-architecture-and-places/dk-annual-report-2025_p03_03.jpg",
          "a KPMG office building seen from below through trees: the firm, offices, corporate", 0.6),
    Photo("office-waterfront", "03-architecture-and-places/dk-annual-report-2025_p06_04.jpg",
          "a brick office building on the waterfront: real estate, property, headquarters, business", 0.4, 0.8),
    Photo("harbour-steps", "03-architecture-and-places/dk-annual-report-2025_p09_05.jpg",
          "aerial view of steps down to dark green water: oceans, water, levels, structure"),
    Photo("rooftops", "03-architecture-and-places/dk-annual-report-2025_p34_09.jpg",
          "zinc rooftops and church spires: cities, heritage, the public sector, regulation"),
    Photo("lounge-above", "03-architecture-and-places/dk-annual-report-2025_p23_07.jpg",
          "people on blue sofas seen from directly above: workplace design, community, networks", 0.5, 0.4),
    Photo("city-rush", "04-technology-and-abstract/global-tech-report-2026_p06_03.jpg",
          "a woman standing still in a blur of moving people: change, pace, focus, the workforce", 0.55, 0.35),
    Photo("skyline-woman", "05-blue-duotone-banners/thought-leadership-mar-2026_p02_01.jpg",
          "a woman looking out over a city skyline on blue: ambition, markets, finance, outlook", 0.85),
    Photo("thoughtful-woman", "05-blue-duotone-banners/thought-leadership-mar-2026_p02_02.jpg",
          "a smiling woman in glasses on blue: people, talent, experience, customers", 0.85),
    Photo("confident-man", "05-blue-duotone-banners/thought-leadership-mar-2026_p02_03.jpg",
          "a man with arms crossed on blue: leadership, confidence, risk, decisions", 0.85),
    Photo("small-business", "05-blue-duotone-banners/thought-leadership-mar-2026_p02_04.jpg",
          "a smiling business owner in an apron on blue: SMEs, entrepreneurs, retail, tax", 0.9),
    Photo("data-profile", "05-blue-duotone-banners/thought-leadership-mar-2026_p03_08.jpg",
          "a profile dissolving into city lights: digital identity, privacy, data, smart cities", 0.75),
    Photo("phone-data", "05-blue-duotone-banners/thought-leadership-mar-2026_p04_09.jpg",
          "a man with a phone emitting data on blue: mobile, apps, payments, digital services", 0.6),
    Photo("phone-glow", "05-blue-duotone-banners/thought-leadership-mar-2026_p04_10.jpg",
          "a woman lit by her phone on blue: consumers, social media, connectivity", 0.75),
    Photo("team-frame", "05-blue-duotone-banners/thought-leadership-may-2026_p03_11.jpg",
          "a framed team meeting on blue: boards, committees, workshops, partnerships", 0.75),
    Photo("man-frame", "05-blue-duotone-banners/thought-leadership-may-2026_p03_12.jpg",
          "a man looking up inside a glowing frame on blue: vision, innovation, the future of work", 0.7),
    Photo("woman-frame", "05-blue-duotone-banners/thought-leadership-may-2026_p03_13.jpg",
          "a smiling woman inside a glowing frame on blue: opportunity, careers, transformation", 0.9),
    Photo("portrait-blur", "05-blue-duotone-banners/thought-leadership-may-2026_p03_14.jpg",
          "a calm portrait over blurred motion on blue: resilience, identity, wellbeing", 0.55),
    Photo("commuter-crowd", "05-blue-duotone-banners/thought-leadership-may-2026_p04_16.jpg",
          "a man in a busy station crowd on blue: workforce, transport, scale, population", 0.6),
    Photo("city-phone", "05-blue-duotone-banners/thought-leadership-may-2026_p04_17.jpg",
          "a woman with a phone in a city at night on blue: urban life, mobility, digital", 0.75),
    Photo("digital-team", "05-blue-duotone-banners/thought-leadership-may-2026_p04_18.jpg",
          "a team at night with glowing data: AI at work, cyber operations, analytics teams", 0.6),
    Photo("handshake-poster", "06-objects-and-textures/dk-annual-report-2025_p08_02.jpg",
          "a framed poster of a handshake in light: partnership, trust, deals, M&A", 0.3),
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
