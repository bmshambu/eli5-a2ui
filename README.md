# eli5-a2ui

An "Explain Like I'm 5" agent for Gemini Enterprise (inspired by [eli5.cc](https://eli5.cc/)), built with Python ADK on Vertex AI Agent Engine and A2UI v0.9. Each answer is a self-contained HTML explainer (four depths, a diagram, sources, follow-up questions) shown in an `IFrameSrcdoc` inside a `Canvas` side panel.

Plan: [ELI5 agent for Gemini Enterprise: plan](https://claude.ai/artifact/6p718dbtsRv8oHJahiHeQp)

## Status

- **Step 0 probe: done.** JavaScript and `postMessage` clicks work inside `IFrameSrcdoc` in GE, in chat and in a `Canvas`. Results: [PROBE.md](PROBE.md).
- **Pipeline and explainer page: working in GE** (first test 2026-10-22). Now one level per answer (ELI5 first) with richer pictures.

## How a turn works

1. The question and level come from the typed text, or from an `ask` click (a level button, "Go deeper" or a follow-up chip inside the page, or a native example button). A new question starts at **ELI5**. "Explain it like I'm 10", "like I'm 15", "expert" or "go deeper" on their own apply to the last question, which is kept in session state. Greetings get a welcome card.
2. `llm.explain`: one Gemini call with Google Search grounding and a `response_schema` returns the `Explanation` for that one level (`schema.py`), with low thinking for speed. If the model can't combine search and a schema (a 400), it switches for good to two calls: research, then write.
3. `render.explanation_card`: a `Canvas` (opener card in chat, side panel) holding the explainer page in an `IFrameSrcdoc`, plus the source links natively below it. Every reply goes through `validate.check()`.

The page has a level ladder (ELI5, ELI10, ELI15, Expert), the analogy, a key fact, the picture (`visuals.py`: flow, cycle, parts or compare, with emoji and colour per node), sources, and buttons to go deeper or ask a follow-up. If a model call fails the user gets a card with a retry button, not a broken turn.

## Layout

```
agent/
  agent.py         root_agent: finds question + level, explains, renders (AGENT_MODE=probe serves the probe)
  llm.py           the Gemini call: Google Search grounding + structured output, one level at a time
  schema.py        Explanation for one level: analogy, body, key fact, diagram, follow-ups
  explainer.py     the HTML page: level ladder, picture, sources, go-deeper and follow-up buttons
  visuals.py       the picture: flow, cycle, parts, compare (HTML/CSS, emoji, colours)
  render.py        A2UI cards: explainer, welcome, error
  a2ui.py          v0.9 message helpers + the <a2a_datapart_json> DataPart wrapper
  validate.py      offline check against the pinned GE composite catalog
  probe*.py        step 0 probe agent and pages
  schemas/v0_9/    pinned catalog + A2UI v0.9 schemas
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
