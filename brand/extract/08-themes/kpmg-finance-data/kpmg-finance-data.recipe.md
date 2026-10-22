---
theme: kpmg-finance-data
name: KPMG Finance Data
mode: light
tagline: Numbers and charts
use_for: banking and capital markets, financial results, sector outlooks, KPI packs, annual-report style tables
preview: kpmg-finance-data.demo.tsx
sources:
  - KPMG China Hong Kong Banking Outlook 2026 (Jan 2026), sources-2026/hong-kong-banking-report-2026.pdf
  - KPMG Denmark Annual Report FY2024/25 (Jan 2026): financial highlights page
  - KPMG Global tech report 2026: column chart styles
---

# KPMG Finance Data

The numbers lead. A Cobalt cover carries three headline figures, and inner pages are white with tinted chart panels, clean tables and a thin photo header strip.

## Palette

| Role | Colour | Hex |
|---|---|---|
| Cover | Cobalt with glowing finance photo on the right | `#1E49E2` |
| Header strip tabs | Pacific / Purple / Light Blue thirds, 6 px | `#00B8F5` `#7213EA` `#76D2FF` |
| Page titles | Cobalt | `#1E49E2` |
| Primary chart series, earlier years | Pacific Blue | `#00B8F5` |
| Latest year / focus series | KPMG Blue | `#00338D` |
| Highlighted table column | Blue Tint 20 | `#D2DBF9` |
| Chart panels | Blue Tint 5 with Tint 20 border | `#F3F6FF` / `#D2DBF9` |
| Gridlines, row rules | Grey 10 | `#E5E5E5` |
| Source lines, units | Grey 60 | `#666666` |
| Stat panels (right-hand column) | Cobalt panel, Pacific Blue rings, white text | `#1E49E2` |

## Typography

- **Cover figures:** KPMG Bold 50–56 px White, with a 3 px Pacific Blue rule above and a 14 px Pale Blue label under each.
- **Page titles:** KPMG Bold 44 px Cobalt (Hong Kong Banking Outlook uses Cobalt, not KPMG Blue, for titles).
- **Tables:** Arial 12–13 px KPMG Blue, numbers right-aligned, bold for totals and for the latest year.
- **Axis labels:** Arial 11 px, Grey 60 for values, KPMG Blue for categories.

## Imagery

- Cover: glowing dollar sign over a city `04-photos/08-finance-and-banking/hk-banking-outlook-2026_p01_002.jpg`.
- Header strips and section dividers: glass towers `hk-banking-outlook-2026_p03_007.jpg`, diagonal blue light `_p02_006`, `_p04_013`, `_p13_064`.
- Data textures: 3D bar landscape `_p12_062`, dot field `_p03_008`, wave mesh `_p07_030`, glass rings `_p14_070`.
- Section divider (HK report): full-bleed tower photo with a translucent Cobalt label box and a Pacific Blue underline.

## Layout rules

1. **Cover:** title two lines, three stats in a row under it. Always label sample or illustrative figures.
2. **Data page:** photo header strip (56 px) with three coloured tabs, title, then a chart panel left and a table or stat panel right.
3. **Bars:** flat, no gradients or 3D, value label on top, the latest period in KPMG Blue and the rest in Pacific Blue.
4. **Tables:** heavy KPMG Blue rule under the header row, Grey 10 between rows, latest column shaded Tint 20.
5. **Stat panel:** Cobalt box with ring stats (Pacific Blue arc) and dashed rounded outlines around each row (HK report p5, p9).
6. **Quotes:** big Pacific Blue quote marks on a Cobalt or purple-gradient panel, white text.
7. Every chart gets a units line ("USD m") and a Grey 60 source line.

## Components from the library

- `07-diagrams/from-pdfs/charts/` (column, paired, stacked bar styles)
- `07-diagrams/templates/kpi-row-6-icons.svg`
- `05-layouts/dk-annual-report-2025/page-07.jpg` (financial highlights reference)

## Do and don't

- Do round consistently and right-align numbers.
- Do keep one highlighted series or column per chart.
- Don't use pie charts with more than four slices.
- Don't publish the preview's sample numbers. They are placeholders.

## One-sentence brief

> KPMG finance data: Cobalt cover with a glowing finance photo and three headline figures, white pages with a tower-photo header strip, Cobalt titles, flat Pacific Blue bars with the latest year in KPMG Blue, and Tint 20 highlighted table columns.
