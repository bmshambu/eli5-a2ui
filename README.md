# eli5-a2ui

An "Explain Like I'm 5" agent for Gemini Enterprise (inspired by [eli5.cc](https://eli5.cc/)), built with Python ADK on Vertex AI Agent Engine and A2UI v0.9. Each answer is a self-contained HTML explainer (four depths, a diagram, sources, follow-up questions) shown in an `IFrameSrcdoc` inside a `Canvas` side panel.

Plan: [ELI5 agent for Gemini Enterprise: plan](https://claude.ai/artifact/6p718dbtsRv8oHJahiHeQp)

## Status

- **Step 0 probe: done.** JavaScript and `postMessage` clicks work inside `IFrameSrcdoc` in GE, in chat and in a `Canvas`. Results: [PROBE.md](PROBE.md).
- **Pipeline and explainer page: built, not yet tried in GE.** Next: deploy and test in GE chat.

## How a turn works

1. The question is the typed text, or the `prompt` of an `ask` click (a follow-up chip inside the page, or a native example button). Greetings get a welcome card.
2. `llm.research`: the model answers with Google Search grounding; the grounding chunks become the numbered sources.
3. `llm.write`: the model turns the notes into an `Explanation` (`schema.py`) via structured output.
4. `render.explanation_card`: a `Canvas` (opener card in chat, side panel) holding the explainer page in an `IFrameSrcdoc`, plus the source links natively below it. Every reply goes through `validate.check()`.

If a model call fails the user gets a card with a retry button, not a broken turn.

## Layout

```
agent/
  agent.py         root_agent: routes the turn, runs research -> write -> render (AGENT_MODE=probe serves the probe)
  llm.py           the two Gemini calls (Google Search grounding, then structured output)
  schema.py        Explanation: four levels, diagram, follow-ups
  explainer.py     the HTML page: level tabs, SVG diagram, sources, follow-up chips
  svg.py           diagram layouts: flow, parts, compare
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
