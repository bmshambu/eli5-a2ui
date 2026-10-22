# 08-themes: KPMG theme recipes

Open **index.html** in a browser. Each card is a theme: a **recipe** (`.recipe.md`: palette, typography, imagery, layout rules) plus a **live preview** (`.demo.tsx`: a cover and a content slide built with the recipe). Click a card to see both slides full size with the palette.

| Theme | Mode | Use for | Built from |
|---|---|---|---|
| [KPMG Corporate](kpmg-corporate/kpmg-corporate.recipe.md) | light | the everyday KPMG look | all 5 library PDFs |
| [KPMG AI](kpmg-ai/kpmg-ai.recipe.md) | dark | AI and agentic AI topics | KPMG US AI Quarterly Pulse Q4 2025 (Jan 2026), Global tech report 2026 |
| [KPMG AI Platform](kpmg-ai-platform/kpmg-ai-platform.recipe.md) | light (dark cover) | enterprise AI platforms, architectures, pilot-to-scale roadmaps | AI Pulse, Global tech report 2026, China Impact Plan |
| [KPMG Finance Data](kpmg-finance-data/kpmg-finance-data.recipe.md) | light | banking, financial results, KPI packs | KPMG China Hong Kong Banking Outlook 2026, KPMG Denmark Annual Report |

`previews/` holds PNG renders of each theme and of the gallery.

## New source material
The two 2026 PDFs added for this step are in `kpmg-branding/sources-2026`. Their imagery was added to the photo library:
- `04-photos/07-ai-neon-backgrounds/` (8): neon corridors, light waves and tunnels from the AI Pulse deck
- `04-photos/08-finance-and-banking/` (12): finance cover, glass towers, blue diagonal light, data textures from the Hong Kong Banking Outlook

## Using a theme
- **In a prompt:** paste the recipe's "One-sentence brief" or the whole recipe.
- **In code:** each `.demo.tsx` exports `theme` (name, mode, palette), `Cover` and `Content` React components. Shared colours, fonts and the vector logo are in `_shared/kpmg.tsx`.
- **In PowerPoint/Word:** follow the palette and layout tables, and take images from the paths each recipe lists.

## Adding a flavour
1. Copy `_template/` to a new folder, e.g. `kpmg-esg/`, and fill in `_template.recipe.md` (one sentence is enough to start, e.g. "focus on enterprises launching AI platforms").
2. Copy one of the existing `.demo.tsx` files next to it and change its `theme`, `Cover` and `Content`.
3. Add it to the `themes` list in `_shared/gallery.tsx` and rebuild: `npm i react@18.3.1 react-dom@18.3.1 esbuild@0.23.1` then `node build.mjs`.

## Notes
- KPMG Bold and Univers are licensed and not included. Previews fall back to Arial Narrow, or Barlow Condensed when online.
- All figures in the previews are samples for layout only.
- Photos come from public KPMG publications; stock licences may restrict reuse outside KPMG.
