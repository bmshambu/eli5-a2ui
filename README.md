# eli5-a2ui

An "Explain Like I'm 5" agent for Gemini Enterprise (inspired by [eli5.cc](https://eli5.cc/)), built with Python ADK on Vertex AI Agent Engine and A2UI v0.9. Each answer is a self-contained, KPMG-branded HTML briefing (cover, key stats, several sections with diagrams and brand photos, caveats, glossary, sources, follow-up questions) shown in an `IFrameSrcdoc` inside a `Canvas` side panel. The simple "Explain it like I'm 5" version is a follow-up.

Plan: [ELI5 agent for Gemini Enterprise: plan](https://claude.ai/artifact/6p718dbtsRv8oHJahiHeQp)

## Status

- **Step 0 probe: done.** JavaScript and `postMessage` clicks work inside `IFrameSrcdoc` in GE, in chat and in a `Canvas`. Results: [PROBE.md](PROBE.md).
- **Pipeline and explainer page: working in GE** (first test 2026-10-22). Now Expert first (a detailed multi-section briefing), ELI5 as a follow-up, styled with the KPMG 2026 brand library.

## How a turn works

1. The question and level come from the typed text, or from an `ask` click (a level button, "Go deeper" or a follow-up chip inside the page, or a native example button). A new question gets the **Expert** briefing. "Explain it like I'm 5" (the button at the end of the page, or typed) gives the simple version of the last question, which is kept in session state; "expert" or "go deeper" goes back. There is no ELI10 or ELI15 any more ("like I'm 10" is read as ELI5). Greetings get a welcome card.
2. `llm.explain`: one Gemini call with Google Search grounding and a `response_schema` returns the `Explanation` for that one level (`schema.py`), with low thinking for speed. If the model can't combine search and a schema (a 400), it switches for good to two calls: research, then write.
3. `render.explanation_card`: a `Canvas` (opener card in chat, side panel) holding the explainer page in an `IFrameSrcdoc`, plus the source links natively below it. Every reply goes through `validate.check()`.

The page (`explainer.py`) follows the layout patterns in `brand/extract/05-layouts`: a Cobalt-to-KPMG-Blue cover with the white logo and a duotone brand photo, a strip of key stats, an executive summary and takeaways, numbered contents, 4 or 5 sections (paragraphs, a banner photo on up to two, a diagram, key points), caveats, a glossary, sources, then the ELI5 button and follow-up questions. Diagrams (`visuals.py`: flow, cycle, parts or compare) use square numbered markers and the brand palette instead of emoji. The model picks photos by id from the catalogue in `brand.py`, so only curated brand images can appear. If a model call fails the user gets a card with a retry button, not a broken turn.

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
- An upload with no text, or with "explain this", gets the Expert briefing. "Explain this document like I'm 5" (the ELI5 button) and later questions in the same session reuse the latest uploaded document, which is found in the session history.
- Each turn logs the kinds of parts it received (`turn parts: [...]`), so the first GE test shows exactly how GE delivers uploads.

## Charts

A section can carry a `chart` (bar, line or donut) when it turns on 3 or more comparable numbers. The prompt allows only numbers stated in the document or the sources, exactly as given, with a `source` note such as "Table 2, p. 7"; if the numbers are not there, there is no chart. Bars and labels are HTML so text stays at 14px or more at any panel width; series that don't match the labels are dropped rather than drawn wrong.

## Layout

```
agent/
  agent.py         root_agent: finds question + level, explains, renders (AGENT_MODE=probe serves the probe)
  llm.py           the Gemini call: Google Search grounding + structured output, one level at a time
  schema.py        Explanation: cover, key stats, sections (diagram, photo id), caveats, glossary, follow-ups
  explainer.py     the KPMG-branded HTML page and its ELI5 / follow-up buttons
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
tools/build_brand_assets.py  rebuilds agent/assets/brand from brand/extract (needs Pillow)
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
