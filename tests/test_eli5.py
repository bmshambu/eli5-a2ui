import asyncio
import json
import pathlib
from types import SimpleNamespace

import pytest
from google.adk.runners import InMemoryRunner
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from agent import a2ui, agent as eli5, brand, explainer, llm, render, validate, visuals
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
    messages = render.explanation_card(SKY, SOURCES, Q)
    validate.check(messages)
    comps = _components(messages)
    assert comps["root"]["component"] == "Canvas" and comps["root"]["children"] == ["frame", "sources"]
    assert comps["root"]["cardTitle"].endswith("Expert")
    assert a2ui.message_bytes(messages[1]) < 400_000  # cover + 2 banner photos inline


def test_worst_case_page_stays_under_limit():
    """Biggest photos on every slot still fits GE's per-message budget."""
    big = sorted(brand.PHOTO_IDS, key=lambda i: len(brand.photo_uri(i)), reverse=True)
    sections = [s.model_copy(update={"photo": big[i + 1]}) for i, s in enumerate(SKY.sections)]
    messages = render.explanation_card(SKY.model_copy(update={"hero_photo": big[0], "sections": sections}), SOURCES, Q)
    validate.check(messages)
    assert a2ui.message_bytes(messages[1]) < 800_000


def test_every_brand_photo_exists():
    for p in brand.PHOTOS:
        assert (brand.ASSETS / "brand" / f"{p.id}.jpg").is_file(), p.id
    assert brand.logo_svg().startswith("<svg") and "metadata" not in brand.logo_svg()


def test_expert_page_is_branded_and_offers_eli5():
    page = explainer.page(SKY, SOURCES, Q)
    assert 'class="logo"' in page and "Explained · Expert" in page and "KPMG. Make the Difference." in page
    assert page.count('<section id="s') == 4 and page.count('class="kpi"') == 4
    assert "Glossary" in page and "Caveats" in page and "Contents" in page
    assert page.count("data-q=") == 1 + 3  # ELI5, follow-ups
    assert "ELI10" not in page and "Go deeper" not in page and "a2ui_action" in page
    ctx = json.loads(explainer.html.unescape(page.split('data-ctx="')[1].split('"')[0]))
    assert ctx == {"prompt": "Explain it like I'm 5: " + Q, "level": "eli5", "question": Q}


def test_eli5_page_offers_expert():
    ctx = json.loads(explainer.html.unescape(explainer.page(SKY, [], Q, "eli5").split('data-ctx="')[1].split('"')[0]))
    assert ctx["level"] == "expert"


def test_section_photos_capped_and_never_repeat_cover():
    sections = [s.model_copy(update={"photo": SKY.hero_photo if i == 0 else s.photo}) for i, s in enumerate(SKY.sections)]
    page = explainer.page(SKY.model_copy(update={"sections": sections}), [], Q)
    assert page.count('class="banner"') == explainer.MAX_SECTION_PHOTOS
    assert page.count(brand.photo_uri(SKY.hero_photo)) == 1


def test_page_has_no_emoji():
    assert not any(ord(ch) >= 0x1F300 for ch in explainer.page(SKY, SOURCES, Q))


def test_page_escapes_model_text():
    evil = SKY.model_copy(update={"title": "<script>alert(1)</script>", "follow_ups": ['a" onclick="x']})
    page = explainer.page(evil, [], Q)
    assert "<script>alert(1)" not in page and 'onclick="x' not in page


@pytest.mark.parametrize("kind", ["flow", "cycle", "parts", "compare"])
def test_every_diagram_type_draws(kind):
    nodes = [DiagramNode(label=f"Node {i}", note="a short note", side="left" if i % 2 else "right") for i in range(5)]
    out = visuals.render(Diagram(type=kind, caption="c", nodes=nodes, left_title="L", right_title="R"), "Hub")
    assert out.startswith("<figure") and out.count("Node ") == (10 if kind == "cycle" else 5)  # cycle: ring + legend


def test_welcome_and_error_cards_validate():
    validate.check(render.welcome_card())
    validate.check(render.error_card("Why?"))


LAST = {"question": Q, "level": "expert"}


@pytest.mark.parametrize("text,last,expected", [
    ("hi", None, None),
    ("  ", None, None),
    (Q, None, (Q, "expert")),
    ("Explain it like I'm 5: " + Q, None, (Q, "eli5")),
    ("explain black holes like I am five years old", None, ("black holes", "eli5")),
    ("ELI expert: how do vaccines work?", None, ("how do vaccines work?", "expert")),
    ("like im 5", LAST, (Q, "eli5")),
    ("like im 10", LAST, (Q, "eli5")),
    ("like im 5", None, None),
    ("go deeper", {"question": Q, "level": "eli5"}, (Q, "expert")),
])
def test_parse(text, last, expected):
    assert eli5.parse(text, last) == expected


@pytest.mark.parametrize("action,expected", [
    ({"name": "ask", "context": {"prompt": "x", "level": "eli5", "question": Q}}, (Q, "eli5")),
    ({"name": "ask", "context": {"prompt": "Why are sunsets red?"}}, ("Why are sunsets red?", "expert")),
    ({"name": "ask", "context": {"prompt": "x", "level": "eli10", "question": Q}}, ("x", "expert")),
    ({"name": "other", "context": {"prompt": "x"}}, None),
])
def test_click_routing(action, expected):
    assert eli5.question_for(_click_content(action)) == expected


def test_one_grounded_call_per_answer(fake):
    expl, sources = asyncio.run(llm.explain(eli5._client, Q))
    assert len(fake.calls) == 1 and [s["uri"] for s in sources] == [s["uri"] for s in SOURCES]
    contents, config = fake.calls[0]
    assert config.tools[0].google_search is not None and config.response_schema is Explanation
    assert config.thinking_config.thinking_level == "LOW"
    assert "specialist reader" in contents and "Question: " + Q in contents
    assert "- frames-in-clouds:" in contents  # the photo catalogue


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
    assert eli5.parse(_components(messages)["retry"]["action"]["event"]["context"]["prompt"], None) == ("Why?", "expert")


def test_agent_remembers_question_for_level_requests(fake):
    async def run():
        runner = InMemoryRunner(agent=eli5.root_agent, app_name="eli5")
        session = await runner.session_service.create_session(app_name="eli5", user_id="u")
        out = []
        for msg in (_text_content(Q), _text_content("like I'm 5")):
            out.append([e async for e in runner.run_async(user_id="u", session_id=session.id, new_message=msg)])
        return out

    first, second = asyncio.run(run())
    parts = [p for e in first if e.content for p in e.content.parts]
    assert parts[0].text.startswith("**Why is the sky blue?** (Expert)")
    assert len([p for p in parts if p.inline_data]) == 2
    assert second[0].content.parts[0].text.startswith("**Why is the sky blue?** (ELI5)")
    assert "5-year-old" not in fake.calls[0][0] and "5-year-old" in fake.calls[1][0]
