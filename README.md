# eli5-a2ui

An "Explain Like I'm 5" agent for Gemini Enterprise (inspired by [eli5.cc](https://eli5.cc/)), built with Python ADK on Vertex AI Agent Engine and A2UI v0.9. Each answer is a self-contained HTML explainer (four depths, a diagram, sources) shown in an `IFrameSrcdoc` inside a `Canvas` side panel.

Plan: [ELI5 agent for Gemini Enterprise: plan](https://claude.ai/artifact/6p718dbtsRv8oHJahiHeQp)

## Status

**Step 0: iframe probe.** The composite catalog, `Canvas` and `IFrameSrcdoc` with inline CSS are already proven in GE (see the v0.9 concierge guidelines, section 8). This probe checks what is left before we build on it: JavaScript inside the frame, `postMessage` clicks back to the agent, and a realistic page size. Steps and results log: [PROBE.md](PROBE.md).

## Layout

```
eli5_agent/
  agent.py         probe agent: answers in a before_model_callback, no model call
  probe.py         one builder per trigger word, plus the "Received" echo card
  probe_pages.py   the HTML pages shown in the iframe (inline CSS/JS/SVG only)
  a2ui.py          v0.9 message helpers + the <a2a_datapart_json> DataPart wrapper
  validate.py      offline check against the pinned GE composite catalog
  schemas/v0_9/    pinned catalog + A2UI v0.9 schemas
tests/             offline tests (pytest)
deploy_to_agent_engine.py
```

## Run tests

```powershell
python -m venv .venv; .venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m pytest tests -q
```

## Deploy

```powershell
copy env.dev.example .env.dev    # fill in project + staging bucket
gcloud auth application-default login
.venv\Scripts\python deploy_to_agent_engine.py
```

Register in GE: Admin console, Agents, Add agent, Vertex AI Agent Engine, then paste the `projects/.../reasoningEngines/...` name the deploy prints. Judge rendering only in GE chat: the Agent Engine Playground and `adk web` show raw JSON.

## Rules that keep GE happy

- `"version": "v0.9"` on every message, catalog id = the GE composite catalog URL (`a2ui.CATALOG_ID`).
- One A2UI message per DataPart, each under 800 KB (GE drops a card over about 1 MB without an error).
- A fresh `surfaceId` per card.
- GE rejects a whole surface for one unknown property, so every reply goes through `validate.check()` first.
