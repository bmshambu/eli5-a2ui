import asyncio
import json
import pathlib
from types import SimpleNamespace

import pytest
from google.adk.runners import InMemoryRunner
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from agent import a2ui, agent as eli5, explainer, llm, render, validate, visuals
from agent.schema import Diagram, DiagramNode, Explanation

SKY = Explanation.model_validate_json((pathlib.Path(__file__).parent / "fixtures" / "sky.json").read_text())
Q = "Why is the sky blue?"
SOURCES = [
    {"title": "NASA: Why is the sky blue?", "uri": "https://example.org/nasa"},
    {"title": "Rayleigh scattering [Wikipedia]", "uri": "https://example.org/rayleigh"},
]


class FakeModels:
    """Answers like Gemini: grounded + structured in one call, unless combined=False (400)."""

    def __init__(self, fail=False, combined=True):
        self.calls, self.fail, self.combined = [], fail, combined

    async def generate_content(self, model, contents, config):
        self.calls.append((contents, config))
        if self.fail:
            raise RuntimeError("quota")
        if config.tools and config.response_schema and not self.combined:
            raise genai_errors.ClientError(400, {"error": {"message": "tools with response schema unsupported"}})
        chunks = [SimpleNamespace(web=SimpleNamespace(uri=s["uri"], title=s["title"])) for s in SOURCES]
        chunks.append(chunks[0])  # duplicate is dropped
        grounded = [SimpleNamespace(grounding_metadata=SimpleNamespace(grounding_chunks=chunks))] if config.tools else []
        if config.response_schema is Explanation:
            return SimpleNamespace(parsed=SKY, text=SKY.model_dump_json(), candidates=grounded)
        return SimpleNamespace(text="notes", candidates=grounded)


def _use(monkeypatch, models):
    monkeypatch.setattr(eli5, "_client", SimpleNamespace(aio=SimpleNamespace(models=models)))
    monkeypatch.setattr(llm, "_combined_ok", None)
    return models


@pytest.fixture
def fake(monkeypatch):
    return _use(monkeypatch, FakeModels())


def _text_content(text):
    return genai_types.Content(role="user", parts=[genai_types.Part(text=text)])


def _click_content(action):
    wrapped = json.dumps({"kind": "data", "data": {"version": "v0.9", "action": action}})
    blob = genai_types.Blob(mime_type="text/plain", data=b"<a2a_datapart_json>" + wrapped.encode() + b"</a2a_datapart_json>")
    return genai_types.Content(role="user", parts=[genai_types.Part(inline_data=blob)])


def _components(messages):
    return {c["id"]: c for c in messages[1]["updateComponents"]["components"]}


def test_explanation_card_validates_and_fits():
    messages = render.explanation_card(SKY, SOURCES, Q, "eli10")
    validate.check(messages)
    comps = _components(messages)
    assert comps["root"]["component"] == "Canvas" and comps["root"]["children"] == ["frame", "sources"]
    assert comps["root"]["cardTitle"].endswith("ELI10")
    assert a2ui.message_bytes(messages[1]) < 100_000


def test_page_has_ladder_deeper_and_chips():
    page = explainer.page(SKY, SOURCES, Q, "eli5")
    assert '<button aria-current="true" disabled>ELI5</button>' in page
    assert page.count("data-q=") == 3 + 1 + 3  # other levels, go deeper, follow-ups
    assert "Go deeper: Explain it like I&#x27;m 10" in page and "a2ui_action" in page
    ctx = json.loads(explainer.html.unescape(page.split('data-ctx="')[1].split('"')[0]))
    assert ctx == {"prompt": "Explain it like I'm 10: " + Q, "level": "eli10", "question": Q}


def test_expert_page_has_no_go_deeper():
    assert "Go deeper" not in explainer.page(SKY, [], Q, "expert")


def test_page_escapes_model_text():
    evil = SKY.model_copy(update={"title": "<script>alert(1)</script>", "follow_ups": ['a" onclick="x']})
    page = explainer.page(evil, [], Q)
    assert "<script>alert(1)" not in page and 'onclick="x' not in page


@pytest.mark.parametrize("kind", ["flow", "cycle", "parts", "compare"])
def test_every_diagram_type_draws(kind):
    nodes = [DiagramNode(emoji="🔵", label=f"Node {i}", note="a short note", side="left" if i % 2 else "right")
             for i in range(5)]
    out = visuals.render(Diagram(type=kind, caption="c", nodes=nodes, left_title="L", right_title="R"), "Hub")
    assert out.startswith("<figure") and out.count("Node ") == (10 if kind == "cycle" else 5)  # cycle: ring + legend


def test_welcome_and_error_cards_validate():
    validate.check(render.welcome_card())
    validate.check(render.error_card("Why?"))


LAST = {"question": Q, "level": "eli5"}


@pytest.mark.parametrize("text,last,expected", [
    ("hi", None, None),
    ("  ", None, None),
    (Q, None, (Q, "eli5")),
    ("Explain it like I'm 10: " + Q, None, (Q, "eli10")),
    ("explain black holes like I am 15 years old", None, ("black holes", "eli15")),
    ("ELI expert: how do vaccines work?", None, ("how do vaccines work?", "expert")),
    ("Explain it like I'm an expert", LAST, (Q, "expert")),
    ("like im 10", LAST, (Q, "eli10")),
    ("like im 10", None, None),
    ("go deeper", {"question": Q, "level": "eli10"}, (Q, "eli15")),
    ("go deeper", {"question": Q, "level": "expert"}, (Q, "expert")),
])
def test_parse(text, last, expected):
    assert eli5.parse(text, last) == expected


@pytest.mark.parametrize("action,expected", [
    ({"name": "ask", "context": {"prompt": "x", "level": "eli15", "question": Q}}, (Q, "eli15")),
    ({"name": "ask", "context": {"prompt": "Why are sunsets red?"}}, ("Why are sunsets red?", "eli5")),
    ({"name": "other", "context": {"prompt": "x"}}, None),
])
def test_click_routing(action, expected):
    assert eli5.question_for(_click_content(action)) == expected


def test_one_grounded_call_per_answer(fake):
    expl, sources = asyncio.run(llm.explain(eli5._client, Q, "eli10"))
    assert len(fake.calls) == 1 and [s["uri"] for s in sources] == [s["uri"] for s in SOURCES]
    contents, config = fake.calls[0]
    assert config.tools[0].google_search is not None and config.response_schema is Explanation
    assert config.thinking_config.thinking_level == "LOW"
    assert "10-year-old" in contents and "Question: " + Q in contents


def test_falls_back_to_two_calls_when_model_cannot_combine(monkeypatch):
    models = _use(monkeypatch, FakeModels(combined=False))
    expl, sources = asyncio.run(llm.explain(eli5._client, Q))
    assert expl == SKY and len(sources) == 2 and len(models.calls) == 3  # rejected, research, write
    asyncio.run(llm.explain(eli5._client, Q))
    assert len(models.calls) == 5  # remembers: no more combined attempts


def test_respond_failure_gives_retry_card(monkeypatch):
    _use(monkeypatch, FakeModels(fail=True))
    text, messages, remember = asyncio.run(eli5.respond(_text_content("Why?")))
    validate.check(messages)
    assert remember is None
    assert eli5.parse(_components(messages)["retry"]["action"]["event"]["context"]["prompt"], None) == ("Why?", "eli5")


def test_agent_remembers_question_for_level_requests(fake):
    async def run():
        runner = InMemoryRunner(agent=eli5.root_agent, app_name="eli5")
        session = await runner.session_service.create_session(app_name="eli5", user_id="u")
        out = []
        for msg in (_text_content(Q), _text_content("like I'm 15")):
            out.append([e async for e in runner.run_async(user_id="u", session_id=session.id, new_message=msg)])
        return out

    first, second = asyncio.run(run())
    parts = [p for e in first if e.content for p in e.content.parts]
    assert parts[0].text.startswith("**Why is the sky blue?** (ELI5)")
    assert len([p for p in parts if p.inline_data]) == 2
    assert second[0].content.parts[0].text.startswith("**Why is the sky blue?** (ELI15)")
    assert "15-year-old" not in fake.calls[0][0] and "high-school" in fake.calls[1][0]
