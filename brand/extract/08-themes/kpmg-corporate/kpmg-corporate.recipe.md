---
theme: kpmg-corporate
name: KPMG Corporate
mode: light
tagline: The everyday KPMG look
use_for: proposals, reports, client decks, newsletters, anything without a stronger flavour
preview: kpmg-corporate.demo.tsx
sources:
  - KPMG Global tech report 2026 (KPMG Switzerland, Jan 2026)
  - KPMG Denmark Annual Report FY2024/25 (Jan 2026)
  - KPMG Thought Leadership, March and May 2026 (KPMG Thailand)
  - KPMG China Our Impact Plan 2026
---

# KPMG Corporate

The default 2026 KPMG look. A bright Cobalt cover, then calm white pages where all text is KPMG Blue. If you are unsure which theme to use, use this one.

## Palette

| Role | Colour | Hex | Share of page |
|---|---|---|---|
| Body text, headlines on white | KPMG Blue | `#00338D` | most text |
| Cover and section backgrounds | Cobalt → KPMG Blue gradient (115°) | `#1E49E2` → `#00338D` | covers, dividers |
| Highlighted words and big numbers | Pacific Blue | `#00B8F5` | under 5% |
| Second-line headline on blue | Pale Blue | `#ACEAFF` | cover only |
| Panels and callouts | Blue Tint 10 / 20 | `#E9EDFC` / `#D2DBF9` | 10–20% |
| Captions, secondary text | Grey 60 | `#666666` | small text |
| Page | White | `#FFFFFF` | 60%+ of content pages |

Gradient cards (tech report p10): Pacific Blue `#00B8F5` → Pale Blue `#ACEAFF`, KPMG Blue text on top.
Do not use the legacy palette (Medium Blue `#005EB8`, Violet `#483698`, Green `#00A3A1`). It did not appear in any 2026 PDF.

## Typography

- **Display:** KPMG Bold (condensed). Fallback Arial Narrow Bold. Covers 100–110 px on a 1280 slide, page titles 44–56 px, tight leading (0.95–1.0).
- **Two-tone cover title:** first line White, following lines Pale Blue `#ACEAFF`, indented one step (about 70 px) from the first line.
- **Body:** Univers Light, fallback Arial, 15–18 px on screen, 9–11 pt in print, KPMG Blue.
- **Section label:** 12 px Cobalt square + bold 14 px label in Cobalt, above the page title.

## Imagery

- Light-architecture photography: glowing nested frames and doorways, people walking through light (`04-photos/04-technology-and-abstract/global-tech-report-2026_p20_06.jpg`, `_p24_07`, `_p28_09`).
- Corporate photography for people pages: `04-photos/02-people-at-work/`, `01-executive-portraits/`.
- Blue duotone banners for card grids: `04-photos/05-blue-duotone-banners/` (1100 × 443).
- On blue covers, blend the photo into the background (screen blend or a left-to-right fade). It sits on the right half, never behind the title.

## Layout rules

1. **Cover:** logo top-left (white, about 7% of slide width), title block bottom-left third, photo right half, "KPMG. Make the Difference." bottom-left, site or publication bottom-right.
2. **Content page:** white, 64 px margins on 1280, section label + title top-left, 2–3 columns, text left-aligned.
3. **Numbers:** a big Cobalt KPMG Bold number with a one-line KPMG Blue explanation underneath, often in a Tint 10 panel with a 4 px Pacific Blue left rule.
4. **Dials:** semicircle gauges, Cobalt on Tint 20 (from the tech report maturity figures).
5. **Footer:** legal line bottom-left at 10 px, "Publication | page" bottom-right.

## Components from the library

- Logo: `03-logos/kpmg-logo-white.svg`, `kpmg-logo-blue.svg`
- Diagrams: `07-diagrams/templates/` (chevrons, roadmaps, pyramid, 2x2, KPI row)
- Icons: `07-diagrams/icons/*-blue.svg` on white, `*-white.svg` on Cobalt
- Colours as code: `01-colors/palette.css`

## Do and don't

- Do keep body text KPMG Blue, not black.
- Do keep one Cobalt cover and mostly white inner pages.
- Don't put text over busy parts of a photo.
- Don't use more than one accent colour (Pacific Blue) per page in this theme.

## One-sentence brief

> Everyday KPMG 2026: Cobalt-to-KPMG-Blue cover with a glowing architectural photo on the right, white inner pages, KPMG Bold headlines and KPMG Blue body text, Pacific Blue for numbers.
