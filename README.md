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

`brand/extract` is the KPMG Branding_Assets extract, copied as is. Only `agent/` is deployed, so the agent uses web-sized copies: the two logo SVGs (metadata stripped) and 24 banner crops listed in `agent/brand.py`. To add or change a photo, edit `PHOTOS` in `brand.py` and run `python tools/build_brand_assets.py`. Executive portraits and people photos are left out on purpose. The extract's README notes that its photos come from public KPMG publications and some stock licences may limit reuse outside KPMG.
