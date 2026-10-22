# KPMG corporate asset library (2026)

Open **index.html** in a browser for the visual catalogue. **asset-index.csv** lists every asset with its source PDF and page.

## Sources (all in the parent kpmg-branding folder)
| Short name | PDF | Published |
|---|---|---|
| global-tech-report-2026 | KPMG Global tech report 2026 (KPMG Switzerland) | Jan 2026 |
| dk-annual-report-2025 | KPMG Denmark Annual Report FY2024/25 | Jan 2026 |
| thought-leadership-mar-2026 | KPMG Thought Leadership, March 2026 (KPMG Thailand) | Mar 2026 |
| thought-leadership-may-2026 | KPMG Thought Leadership, May 2026 (KPMG Thailand) | Jun 2026 |
| cn-impact-plan-2026 | KPMG China: Our Impact Plan 2026, achievements at a glance | Jun 2026 |

## Folders
- **01-colors/**: observed 2026 palette (JSON, CSS variables, tab-separated list, swatch sheet), plus the legacy palette from the KPMG branding skill for comparison
- **02-typography/**: typefaces, size scale and usage rules measured from the PDFs
- **03-logos/**: KPMG logo rebuilt from the vector artwork in the tech report, in blue / white / black as SVG, transparent PNG (600 dpi) and PDF. Also the raster logo found in the annual report and the logo from the branding skill
- **04-photos/**: 84 unique photos extracted from the PDFs, deduplicated and sorted
  - 01-executive-portraits (18), 02-people-at-work (16), 03-architecture-and-places (11), 04-technology-and-abstract (17), 05-blue-duotone-banners (18), 06-objects-and-textures (4)
- **05-layouts/**: every page of every PDF as a thumbnail, plus layout-patterns.md describing the 8 recurring layouts
- **06-graphics/publication-thumbnails/**: newsletter covers shown in the thought-leadership decks
- **07-diagrams/**: funnels, roadmaps, timelines and process flows (see 07-diagrams/README.md)
  - templates (14): editable KPMG-styled SVG + PNG preview: 3 funnels, 3 roadmaps, milestone timeline, chevron process, cycle, maturity staircase, pyramid, gradient pillar cards, 2x2 matrix, KPI row with icons
  - icons (6): line icons traced as vectors from the annual report, in blue / cobalt / white
  - from-pdfs (23): high-res crops of the agenda roadmap, gradient cards, maturity charts, stat callouts, chart styles and Impact Plan infographic panels

- **08-themes/**: theme recipes. Open 08-themes/index.html. Four flavours (KPMG Corporate, KPMG AI, KPMG AI Platform, KPMG Finance Data), each a recipe .md plus a live preview .demo.tsx
- **04-photos/07-ai-neon-backgrounds** (8) and **08-finance-and-banking** (12): added from the KPMG US AI Pulse Q4 2025 deck and the Hong Kong Banking Outlook 2026 (PDFs in ../sources-2026)

## Notes
- 2026 KPMG material uses the refreshed palette (Cobalt `#1E49E2`, Pacific Blue `#00B8F5`, Purple `#7213EA`) alongside KPMG Blue `#00338D`. The older Medium Blue / Violet / Green palette in the branding skill did not appear in these PDFs.
- QR codes (24), a repeated set of 5 publication thumbnails and tiny icons under 150 px were left out. Exact duplicates across pages were removed.
- KPMG Bold and Univers fonts are licensed and not included.
- Photos come from public KPMG publications; stock licences may restrict reuse outside KPMG.
