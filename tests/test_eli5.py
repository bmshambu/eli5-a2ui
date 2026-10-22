import asyncio
import io
import json
import pathlib
import zipfile
from types import SimpleNamespace

import pytest
from google.adk.runners import InMemoryRunner
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from agent import a2ui, agent as eli5, brand, document, explainer, llm, render, validate, visuals
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


# --- uploaded documents ---------------------------------------------------------------

def _office(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, xml in files.items():
            z.writestr(name, xml)
    return buf.getvalue()


DOCX_BYTES = _office({"word/document.xml": "<w:document><w:body>"
                      "<w:p><w:r><w:t>Fees &amp; charges</w:t></w:r></w:p>"
                      "<w:p><w:r><w:t>The fee is </w:t></w:r><w:r><w:t>2.5%.</w:t></w:r></w:p></w:body></w:document>"})


def _upload(name, mime, data, text=None):
    parts = [genai_types.Part(inline_data=genai_types.Blob(mime_type=mime, data=data, display_name=name))]
    if text:
        parts.append(genai_types.Part(text=text))
    return genai_types.Content(role="user", parts=parts)


def test_office_text_reads_word_powerpoint_and_excel():
    assert document.office_text(DOCX_BYTES, document.DOCX) == "Fees & charges\nThe fee is 2.5%."
    pptx = _office({f"ppt/slides/slide{i}.xml": f"<p:sld><a:p><a:r><a:t>Slide text {i}</a:t></a:r></a:p></p:sld>"
                    for i in (2, 10, 1)})
    assert document.office_text(pptx, document.PPTX) == "[Slide 1]\nSlide text 1\n\n[Slide 2]\nSlide text 2\n\n[Slide 3]\nSlide text 10"
    xlsx = _office({"xl/sharedStrings.xml": "<sst><si><t>Revenue</t></si></sst>",
                    "xl/worksheets/sheet1.xml": '<sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1"><v>42</v></c></row></sheetData>'})
    assert document.office_text(xlsx, document.XLSX) == "[Sheet 1]\nRevenue | 42"


def test_documents_found_in_turn_and_clicks_skipped():
    content = _upload("policy.pdf", "application/pdf", b"%PDF-1.7 ...", "explain this")
    content.parts += _click_content({"name": "ask", "context": {"prompt": "x"}}).parts
    docs = document.from_content(content)
    assert [d.name for d in docs] == ["policy.pdf"]
    assert docs[0].part.inline_data.display_name is None  # rebuilt clean for the model
    word = document.from_content(_upload("terms.docx", "application/octet-stream", DOCX_BYTES))
    assert "The fee is 2.5%." in word[0].part.text and word[0].name == "terms.docx"
    assert document.from_content(_upload("x.zip", "application/zip", b"PK..")) == []


@pytest.mark.parametrize("text,expected", [
    ("Explain this document like I'm 5", ("Explain this document", "eli5")),
    ("summarise the attached pdf", ("Explain this document", "expert")),
    ("what does section 3 say about fees?", ("what does section 3 say about fees?", "expert")),
])
def test_parse_document_questions(text, expected):
    assert eli5.parse(text, None) == expected


def test_bare_upload_explains_the_document_without_search(fake):
    docs = document.from_content(_upload("policy.pdf", "application/pdf", b"%PDF-1.7 ..."))
    text, messages, remember = asyncio.run(eli5.respond(_upload("policy.pdf", "application/pdf", b"%PDF"), None, docs))
    validate.check(messages)
    assert remember == {"question": "Explain this document", "level": "expert"}
    contents, config = fake.calls[0]
    assert not config.tools and config.response_schema is Explanation
    parts = contents[0].parts
    assert parts[0].inline_data.mime_type == "application/pdf" and "faithfully and completely" in parts[-1].text
    page = _components(messages)["frame"]["htmlContent"]
    assert "Document explained · Expert" in page and "Based on your document" in page and "policy.pdf" in page
    ctx = json.loads(explainer.html.unescape(page.split('data-ctx="')[1].split('"')[0]))
    assert ctx["prompt"] == "Explain this document like I'm 5" and ctx["level"] == "eli5"


def test_section_shows_where_it_comes_from():
    sections = [SKY.sections[0].model_copy(update={"doc_ref": "Section 2.1"})]
    page = explainer.page(SKY.model_copy(update={"sections": sections}), [], Q, documents=["a.pdf"])
    assert "From the document: Section 2.1" in page


def test_follow_up_uses_the_uploaded_document(fake):
    async def run():
        runner = InMemoryRunner(agent=eli5.root_agent, app_name="eli5")
        session = await runner.session_service.create_session(app_name="eli5", user_id="u")
        for msg in (_upload("terms.docx", document.DOCX, DOCX_BYTES), _text_content("like I'm 5")):
            [e async for e in runner.run_async(user_id="u", session_id=session.id, new_message=msg)]

    asyncio.run(run())
    first, second = (c[0][0].parts for c in fake.calls)
    assert "The fee is 2.5%." in first[0].text and "The fee is 2.5%." in second[0].text
    assert "5-year-old" in second[-1].text and not fake.calls[1][1].tools
