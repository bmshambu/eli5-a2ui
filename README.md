# eli5-a2ui

An "Explain Like I'm 5" agent for Gemini Enterprise (inspired by [eli5.cc](https://eli5.cc/)), built with Python ADK on Vertex AI Agent Engine and A2UI v0.9. Each answer is a self-contained, KPMG-branded HTML briefing (cover, key stats, several sections with diagrams and brand photos, caveats, glossary, sources, follow-up questions) shown in an `IFrameSrcdoc` inside a `Canvas` side panel. The simpler version ("Explain it in a simpler way") is a follow-up. Users never see the name "ELI5"; it survives only in the repo name and internal keys.

Plan: [ELI5 agent for Gemini Enterprise: plan](https://claude.ai/artifact/6p718dbtsRv8oHJahiHeQp)

## Status

- **Step 0 probe: done.** JavaScript and `postMessage` clicks work inside `IFrameSrcdoc` in GE, in chat and in a `Canvas`. Results: [PROBE.md](PROBE.md).
- **Pipeline and explainer page: working in GE** (first test 2026-10-22). Now Expert first (a detailed multi-section briefing), the simpler version as a follow-up, styled with the KPMG 2026 brand library.

## How a turn works

1. The question and level come from the typed text, or from an `ask` click (a level button, "Go deeper" or a follow-up chip inside the page, or a native example button). A new question gets the **Expert** briefing. "Explain it in a simpler way" (the button at the end of the page, or typed: "simpler", "in simple terms", "in plain English", and the old "like I'm 5" all work) gives the simpler version of the last question, which is kept in session state; "expert" or "go deeper" goes back. It is written for a busy professional new to the topic: plain English, no jargon. Greetings get a welcome card.
2. `llm.explain`: one Gemini call with Google Search grounding and a `response_schema` returns the `Explanation` for that one level (`schema.py`), with low thinking for speed. If the model can't combine search and a schema (a 400), it switches for good to two calls: research, then write.
3. `render.explanation_card`: a `Canvas` (opener card in chat, side panel) holding the explainer page in an `IFrameSrcdoc`, plus the source links natively below it. Every reply goes through `validate.check()`.

The page (`explainer.py`) follows the layout patterns in `brand/extract/05-layouts`: a Cobalt-to-KPMG-Blue cover with the white logo and a duotone brand photo, a strip of key stats, an executive summary and takeaways, numbered contents, 4 or 5 sections (paragraphs, a banner photo on up to two, a diagram, key points), caveats, a glossary, sources, then the "Explain it in a simpler way" button and follow-up questions. Diagrams (`visuals.py`: flow, cycle, parts or compare) use square numbered markers and the brand palette instead of emoji. The model picks photos by id from the catalogue in `brand.py`, so only curated brand images can appear. If a model call fails the user gets a card with a retry button, not a broken turn.

**Motion.** The cover works like a motion poster: the brand photo slowly zooms and pans, outlined brand frames drift, a light sweep crosses it once, and the logo, eyebrow, title, lede and tags rise in one after another. Further down, KPI numbers count up when they come into view (years are left alone), and sections, diagrams and charts animate as they scroll into view (diagram nodes pop in, bars grow, donut rings sweep, lines wipe in). It is all CSS transforms and opacity plus a small script, so it adds no download weight. Without JavaScript the page shows in full. When "reduce motion" is on (Windows "Animation effects" off, common on managed laptops), the page keeps only fades and count-ups, and a **Play motion** button on the cover turns the full motion poster on.

## Create: posters, emails, social posts, one-pagers

Besides explaining, the agent makes things on request in the same brand (`agent/maker.py`):
"Create a poster for our AI training week", "Draft an email inviting the team to the town hall",
"Write a LinkedIn post about …", "Make a one-pager on …". One structured model call
(`llm.create`, no web search) writes a `Creation` (schema.py); names, dates, places and links
the user did not give become `[placeholders]`, never invented.

- Each format is laid out as the real thing: a portrait poster, an email as it lands in the
  inbox, a LinkedIn-style post with its image, a one-page flyer. Creative look by default
  (accent, emoji, motion); the theme bar switches it without a model call.
- Emails and posts are also given as plain text, in a copy box on the page and in the chat
  reply, ready to paste into Outlook or LinkedIn.
- **Download PDF** works for creations too (`pdf.build_creation`: an A4 poster, or a branded page).
- Changes edit the last draft: the page's "Change it" buttons, "Turn it into an email", or
  typed changes such as "make it shorter" or "more formal" right after a creation.
- "Turn this into a poster" right after a briefing works from that briefing; with an uploaded
  document, the facts come from the document.
- Session state: `eli5_create` (the last request and draft) and `eli5_mode` (whether the last
  answer was a creation or an explanation, so "make it simpler" goes to the right place).

## Creative look (default)

New answers use the **Creative** look, which mixes the whole brand library instead of following one recipe. The model does the art direction for each topic, so different topics look different:
- an `accent` from the 2026 palette (cobalt, pacific, purple or magenta), which tints the cover gradient, numbers, bullets and diagrams;
- a `cover_style`:
  - `poster`: one big photo;
  - `split`: a colour block beside a slanted photo;
  - `mosaic`: the cover photo plus two section photos as slowly zooming tiles;
- an `emoji` for the cover (large and bobbing), one per section (badge next to the heading) and one per key stat.

Motion is livelier too: drifting colour blobs, a shifting cover gradient, and sections that slide in from alternate sides. It still follows the "reduce motion" rules and the **Play motion** button. Emojis appear only in the Creative look. The PDF leaves them out, because its font cannot draw them, and uses the accent colour on its cover. When the user switches to another theme (below), later answers in that session keep that theme (`eli5_theme` in session state).

## Themes

The theme row also offers the four KPMG theme recipes in `brand/extract/08-themes`. Each recipe is a `.recipe.md` file with a `.demo.tsx` live preview, and `index.html` there shows all four. The model picks the theme with the `theme` field and takes the cover photo from that theme's list in `brand.THEMES`:

| Theme | Used for | On the page |
|---|---|---|
| `corporate` (default) | everyday topics, reports, policies | Cobalt cover, white pages, KPMG Blue text, Pale Blue last words in the title |
| `ai` | AI, agentic AI, GenAI, data and tech | dark: blue neon wash on every page, glowing Pacific Blue numbers, glass panels, capsule buttons, Pacific last words in the title |
| `ai-platform` | platforms, architectures, roadmaps | navy data-city cover, white pages, chevrons ramping Tint 20 → Light Blue → Pacific → Cobalt |
| `finance-data` | banking, results, outlooks, KPI packs | Cobalt cover carrying three headline figures, a Pacific/Purple/Light Blue tab strip, Cobalt titles, single-series bars in Pacific with the latest in KPMG Blue, ruled tables |

**Switching theme.** A row of theme buttons sits under the cover, and "switch to the AI theme" typed in chat works too. Either one re-shows the same explanation in the other theme from session state, with no new model call. The cover photo changes unless it already suits the theme, and Download PDF on that card uses the theme it shows. `explainer.THEME_CSS` holds the page rules and `pdf.COVERS` holds the PDF covers. PDF inner pages stay white in every theme so they print well. The 20 photos from the 2026 AI Pulse deck and the Hong Kong Banking Outlook (`04-photos/07-ai-neon-backgrounds`, `08-finance-and-banking`) are in the catalogue too, which now has 75 photos. To add a theme, follow `08-themes/README.md`, then add an entry to `brand.THEMES`, `THEME_CSS` and `COVERS`.

## Uploaded documents

The main use is KPMG staff uploading a document in GE chat and asking for it to be explained.

- `document.py` picks the file out of the user's turn. GE sends it as `inline_data` (bytes plus a file name) or as `file_data` (a URI).
  - PDF, text and images go to Gemini as they are.
  - Word (.docx), PowerPoint (.pptx) and Excel (.xlsx) are turned into text first. This uses the standard library only.
  - Our own button clicks also arrive as `inline_data`, and they are skipped.
- `llm.explain_documents` makes one structured call over the document, with no web search. The prompt asks the model to:
  - follow the document's own structure, one section per major part, each with `doc_ref` (section, page or slide);
  - keep every key figure, date, obligation and recommendation;
  - add nothing from outside the document, and put anything unclear in the caveats.
- The page says "Document explained", shows "From the document: …" under each section, and names the file where web sources would go.
- An upload with no text, or with "explain this", gets the Expert briefing. "Explain this document in a simpler way" (the button) and later questions in the same session reuse the latest uploaded document, which is found in the session history.
- Each turn logs the kinds of parts it received (`turn parts: [...]`), so the first GE test shows exactly how GE delivers uploads.

## Diagrams

`visuals.py` draws eleven layouts. Eight follow the KPMG templates in `brand/extract/07-diagrams/templates`:
- process chevrons (`flow`)
- `funnel`, which shows stage-to-stage conversion when the values are numbers
- `roadmap` (phase chevrons with dates)
- `timeline` (milestones alternating above and below the line)
- `staircase` (a maturity model)
- `pyramid`
- `matrix` (2x2 prioritisation)
- `pillars` (gradient message cards with a stat each)

The other three are `cycle`, `parts` and `compare`. All of them are built live in HTML and CSS from the model's nodes, so any text fits, and they stack vertically below 600px. Key-stat tiles can carry one of the six brand line icons (`07-diagrams/icons`). The icons are cleaned into `agent/assets/icons` with `stroke="currentColor"`, so they follow the tile colour and dark mode.

## Charts

A section can carry a `chart` (bar, line or donut) when it turns on 3 or more comparable numbers. The prompt allows only numbers stated in the document or the sources, exactly as given, with a `source` note such as "Table 2, p. 7"; if the numbers are not there, there is no chart. Bars and labels are HTML so text stays at 14px or more at any panel width; series that don't match the labels are dropped rather than drawn wrong.

## Download PDF and PowerPoint

GE's chat frame blocks printing and downloads, so the page can't save itself. A native **Download PDF** button sits under the frame. Clicking it sends a `pdf` action with the question and level; the agent rebuilds that explanation from session state (`eli5_pages`, the last 4 shown, so no new model call) and `pdf.py` turns it into a KPMG-branded A4 PDF with reportlab: cover with the brand photo and white logo, key stats, sections with charts (vector bar, line, donut) and diagrams (numbered steps, compare columns, 2x2 matrix), caveats, glossary, document name and sources. It uses the embedded Liberation Sans (Arial-metric, OFL, `agent/assets/fonts`) so symbols such as λ and ⁴ render. The PDF goes back in chat as a file part (`application/pdf`), which ADK sends as an A2A FilePart; a PDF for an old card that is no longer in state is explained again first.

**Download PowerPoint** works the same way (`pptx` action, `slides.py`, python-pptx): a 16:9 deck with the cover (photo in the theme or accent colour), an "at a glance" slide with the key stats, one slide per section (key points on the left; the chart as a native, editable PowerPoint chart, the diagram as shapes, or the photo on the right; the full text in the speaker notes), caveats and glossary, sources, and a closing slide. For created content, a poster is one portrait slide and an email, post or one-pager is a cover and a content slide. It goes back as a file part (`application/vnd.openxmlformats-officedocument.presentationml.presentation`).

## Layout

```
agent/
  agent.py         root_agent: finds question + level, explains, renders (AGENT_MODE=probe serves the probe)
  llm.py           the Gemini call: Google Search grounding + structured output, one level at a time
  schema.py        Explanation: cover, key stats, sections (diagram, photo id), caveats, glossary, follow-ups
  explainer.py     the KPMG-branded HTML page and its "simpler way" / follow-up buttons
  pdf.py           the same explanation as a KPMG-branded A4 PDF (reportlab), for Download PDF
  visuals.py       section diagrams: flow, cycle, parts, compare (HTML/CSS, brand palette)
  brand.py         palette, logo, and the photo catalogue the model chooses from
  assets/          KPMG logos (SVG) and brand/*.jpg web banners (about 515 KB in total)
  document.py      uploaded files from the user's turn -> parts Gemini reads (PDF, text, images, Word, PowerPoint, Excel)
  charts.py        bar, line and donut charts for a section's numbers (HTML bars, SVG line/donut, brand palette)
  render.py        A2UI cards: explainer, welcome, error
  a2ui.py          v0.9 message helpers + the <a2a_datapart_json> DataPart wrapper
  validate.py      offline check against the pinned GE composite catalog
  probe*.py        step 0 probe agent and pages
  schemas/v0_9/    pinned catalog + A2UI v0.9 schemas
brand/extract/     full copy of the KPMG 2026 brand library (colours, type, logos, photos, layouts); reference only, not deployed
tools/build_brand_assets.py  rebuilds agent/assets/brand (photos) and agent/assets/icons from brand/extract (needs Pillow)
tests/             offline tests (pytest), with a fake model client
deploy_to_agent_engine.py
```

## Run tests

```powershell
python -m venv .venv; .venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m pytest tests -q
```

## Deploy

```powershell
copy env.dev.example .env.dev    # fill in project, staging bucket, MODEL
gcloud auth application-default login
.venv\Scripts\python deploy_to_agent_engine.py
```

Register in GE: Admin console, Agents, Add agent, Vertex AI Agent Engine, then paste the `projects/.../reasoningEngines/...` name the deploy prints. Judge rendering only in GE chat: the Agent Engine Playground and `adk web` show raw JSON.

## Rules that keep GE happy

- `"version": "v0.9"` on every message, catalog id = the GE composite catalog URL (`a2ui.CATALOG_ID`).
- One A2UI message per DataPart, each under 800 KB (GE drops a card over about 1 MB without an error).
- A fresh `surfaceId` per card.
- GE rejects a whole surface for one unknown property, so every reply goes through `validate.check()` first.

## Brand assets

`brand/extract` is the KPMG Branding_Assets extract, copied as is. Only `agent/` is deployed, so the agent uses web-sized copies: the two logo SVGs (metadata stripped) and 56 banner crops listed in `agent/brand.py` (about 1.3 MB on disk; at most 3 are inlined per page). To add or change a photo, edit `PHOTOS` in `brand.py` and run `python tools/build_brand_assets.py`. Executive portraits are left out on purpose; people-at-work and stock people photos are in. `focus_x` and `focus_y` set where each banner is cropped. The extract's README notes that its photos come from public KPMG publications and some stock licences may limit reuse outside KPMG.
