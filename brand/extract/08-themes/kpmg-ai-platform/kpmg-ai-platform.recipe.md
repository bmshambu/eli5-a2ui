---
theme: kpmg-ai-platform
name: KPMG AI Platform
mode: light
tagline: Building-block diagrams
use_for: enterprise AI platform strategy, target architectures, operating models, pilot-to-scale roadmaps
preview: kpmg-ai-platform.demo.tsx
sources:
  - KPMG US AI Quarterly Pulse Survey Q4 2025 (Jan 2026): "leaders are converging on platform standards" page, capsule labels
  - KPMG Global tech report 2026: data-city imagery, 2026 agenda, maturity figures
  - KPMG China Our Impact Plan 2026: "secure, trusted AI-powered platform" panel
---

# KPMG AI Platform

A dark, data-city cover that says "technology at scale", then light pages built around **building blocks**: layered stacks, chevron roadmaps and side rails for governance. Use it when the story is how the pieces fit together.

## Palette

| Role | Colour | Hex |
|---|---|---|
| Cover background | Ink Navy → deep blue | `#050B2E` → `#0A1E7A` |
| Cover key line ("AI platform") | Pacific Blue | `#00B8F5` |
| Core platform layer blocks | Cobalt, white text | `#1E49E2` |
| Agent / connector blocks | White with Pacific Blue outline | `#00B8F5` |
| Supporting blocks | Blue Tint 10 fill, Tint 20 border | `#E9EDFC` / `#D2DBF9` |
| Cross-cutting rails (governance, risk) | Purple, Dark Purple | `#7213EA`, `#510DBC` |
| Roadmap chevrons, left to right | Tint 20 → Light Blue → Pacific → Cobalt | `#D2DBF9` `#76D2FF` `#00B8F5` `#1E49E2` |
| Text | KPMG Blue | `#00338D` |

## Typography

- **Display:** KPMG Bold. Cover 80–90 px over three lines, last line Pacific Blue. Page titles 44–48 px KPMG Blue.
- **Block labels:** Arial Bold 13–15 px, centred in the block.
- **Layer names:** Arial Bold 13 px in Cobalt, left of each row.

## Imagery

- Cover: light-streak data city `04-photos/04-technology-and-abstract/global-tech-report-2026_p26_08.jpg`, fading into navy on the left.
- Alternatives: glowing cubes (building blocks) `thought-leadership-may-2026_p01_13.jpg`, light-line tunnel `ai-pulse-q4-2025_p06.jpg`.
- Inner pages carry diagrams, not photos.

## Layout rules

1. **Stack diagram:** 4–6 horizontal layers, 3 blocks each, 8 px gaps. Top = what users touch, bottom = infrastructure. Cross-cutting concerns are vertical rails on the right, in purple.
2. **Roadmap strip:** 3–5 overlapping chevrons above the diagram, numbered 01–05, colour ramps from light to Cobalt as maturity grows.
3. **One colour per layer type:** Cobalt for the core platform, outline for agents, tint for everything else. Never mix within a row.
4. **Square corners** on blocks (KPMG uses square shapes; save rounded capsules for the AI theme).
5. Cover follows the Corporate cover layout (logo, eyebrow, title bottom-left, strap line).

## Components from the library

- `07-diagrams/templates/process-5-step-chevrons.svg`, `roadmap-4-phase-chevrons.svg`, `maturity-staircase-5-level.svg`, `pyramid-5-level.svg`
- `07-diagrams/from-pdfs/roadmaps-and-timelines/` (tech report 2026 agenda)

## Do and don't

- Do label every block with a noun, two or three words.
- Do keep the diagram on white so it prints and pastes into Word cleanly.
- Don't add glow or gradients to blocks. The glow stays on the cover.
- Don't draw more than 18 blocks on one page.

## One-sentence brief

> KPMG enterprise AI platform: navy data-city cover with a Pacific Blue last line, then white pages with square Cobalt / outline / tint building blocks, chevron roadmap on top and purple governance rails.

Note: a dedicated KPMG US enterprise-AI-platform PDF was not available for download, so this recipe is built from the AI Pulse deck and the tech report. Add one to `sources-2026` to refine it.
