import asyncio
import json
import pathlib
from types import SimpleNamespace

import pytest
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

from agent import a2ui, agent as eli5, explainer, llm, render, svg, validate
from agent.schema import Diagram, DiagramNode, Explanation

SKY = Explanation.model_validate_json((pathlib.Path(__file__).parent / "fixtures" / "sky.json").read_text())
SOURCES = [
    {"title": "NASA: Why is the sky blue?", "uri": "https://example.org/nasa"},
    {"title": "Rayleigh scattering [Wikipedia]", "uri": "https://example.org/rayleigh"},
    {"title": "Met Office", "uri": "https://example.org/met"},
]


class FakeModels:
    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    async def generate_content(self, model, contents, config):
        self.calls.append(config)
        if self.fail:
            raise RuntimeError("quota")
        if config.response_schema is Explanation:
            return SimpleNamespace(parsed=SKY, text=SKY.model_dump_json())
        chunks = [SimpleNamespace(web=SimpleNamespace(uri=s["uri"], title=s["title"])) for s in SOURCES]
        chunks.append(chunks[0])  # duplicate is dropped
        meta = SimpleNamespace(grounding_chunks=chunks)
        return SimpleNamespace(text="notes", candidates=[SimpleNamespace(grounding_metadata=meta)])


@pytest.fixture
def fake(monkeypatch):
    models = FakeModels()
    monkeypatch.setattr(eli5, "_client", SimpleNamespace(aio=SimpleNamespace(models=models)))
    return models


def _text_content(text):
    return genai_types.Content(role="user", parts=[genai_types.Part(text=text)])


def _click_content(action):
    wrapped = json.dumps({"kind": "data", "data": {"version": "v0.9", "action": action}})
    blob = genai_types.Blob(mime_type="text/plain", data=b"<a2a_datapart_json>" + wrapped.encode() + b"</a2a_datapart_json>")
    return genai_types.Content(role="user", parts=[genai_types.Part(inline_data=blob)])


def _components(messages):
    return {c["id"]: c for c in messages[1]["updateComponents"]["components"]}


def test_explanation_card_validates_and_fits():
    messages = render.explanation_card(SKY, SOURCES)
    validate.check(messages)
    comps = _components(messages)
    assert comps["root"]["component"] == "Canvas" and comps["root"]["children"] == ["frame", "sources"]
    assert a2ui.message_bytes(messages[1]) < 100_000


def test_page_has_levels_chips_and_safe_citations():
    page = explainer.page(SKY, SOURCES)
    for label in ("ELI5", "ELI10", "ELI15", "Expert"):
        assert f">{label}</button>" in page
    assert page.count('class="chip"') == 3 and "a2ui_action" in page and '"ask"' in page
    assert 'href="#src2"' in page and "[9]" not in page  # citation to a missing source is dropped
    assert "<svg" in page and "connect" not in page.lower()


def test_page_escapes_model_text():
    evil = SKY.model_copy(update={"title": "<script>alert(1)</script>", "follow_ups": ['a" onclick="x']})
    page = explainer.page(evil, [])
    assert "<script>alert(1)" not in page and 'onclick="x' not in page


@pytest.mark.parametrize("kind", ["flow", "parts", "compare"])
def test_every_diagram_type_draws(kind):
    nodes = [DiagramNode(label=f"Node {i}", note="a short note that may need to wrap onto two lines",
                         side="left" if i % 2 else "right") for i in range(5)]
    out = svg.render(Diagram(type=kind, caption="c", nodes=nodes, left_title="L", right_title="R"), "Hub")
    assert out.startswith("<svg") and out.count("Node ") == 5


def test_welcome_and_error_cards_validate():
    validate.check(render.welcome_card())
    validate.check(render.error_card("Why?"))


@pytest.mark.parametrize("content,expected", [
    (_text_content("hi"), None),
    (_text_content("  "), None),
    (_text_content("Why is the sky blue?"), "Why is the sky blue?"),
    (_click_content({"name": "ask", "context": {"prompt": "Why are sunsets red?"}}), "Why are sunsets red?"),
    (_click_content({"name": "other", "context": {"prompt": "x"}}), None),
])
def test_question_routing(content, expected):
    assert eli5.question_for(content) == expected


def test_research_dedupes_sources(fake):
    notes, sources = asyncio.run(llm.research(eli5._client, "q"))
    assert notes == "notes" and [s["uri"] for s in sources] == [s["uri"] for s in SOURCES]
    assert fake.calls[0].tools[0].google_search is not None


def test_respond_explains(fake):
    text, messages = asyncio.run(eli5.respond(_text_content("Why is the sky blue?")))
    assert text.startswith("**Why is the sky blue?**")
    assert _components(messages)["root"]["component"] == "Canvas"
    assert fake.calls[1].response_schema is Explanation


def test_respond_failure_gives_retry_card(monkeypatch):
    monkeypatch.setattr(eli5, "_client", SimpleNamespace(aio=SimpleNamespace(models=FakeModels(fail=True))))
    text, messages = asyncio.run(eli5.respond(_text_content("Why?")))
    validate.check(messages)
    assert _components(messages)["retry"]["action"]["event"]["context"]["prompt"] == "Why?"


def test_agent_end_to_end(fake):
    async def run():
        runner = InMemoryRunner(agent=eli5.root_agent, app_name="eli5")
        session = await runner.session_service.create_session(app_name="eli5", user_id="u")
        msg = _click_content({"name": "ask", "context": {"prompt": "Why is the sky blue?"}})
        return [e async for e in runner.run_async(user_id="u", session_id=session.id, new_message=msg)]

    parts = [p for e in asyncio.run(run()) if e.content for p in e.content.parts]
    assert parts[0].text.startswith("**Why is the sky blue?**")
    assert len([p for p in parts if p.inline_data]) == 2
