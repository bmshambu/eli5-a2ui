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

from agent import a2ui, agent as eli5, brand, charts, document, explainer, llm, pdf, render, validate, visuals
from agent.schema import Chart, Diagram, DiagramNode, Explanation, Series, Stat

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
    assert comps["root"]["component"] == "Canvas" and comps["root"]["children"] == ["frame", "pdf", "sources"]
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
    assert page.count("data-q=") == 1 + 3 + 4  # simpler, follow-ups, the 4 other themes
    assert "ELI10" not in page and "Go deeper" not in page and "a2ui_action" in page
    ctx = json.loads(explainer.html.unescape(page.split('class="primary"')[1].split('data-ctx="')[1].split('"')[0]))
    assert ctx == {"prompt": "Explain it in a simpler way: " + Q, "level": "eli5", "question": Q}
    assert "ELI5" not in page and "like I'm 5" not in page


def test_eli5_page_offers_expert():
    ctx = json.loads(explainer.html.unescape(explainer.page(SKY, [], Q, "eli5").split('class="primary"')[1].split('data-ctx="')[1].split('"')[0]))
    assert ctx["level"] == "expert"


def test_section_photos_capped_and_never_repeat_cover():
    sections = [s.model_copy(update={"photo": SKY.hero_photo if i == 0 else s.photo}) for i, s in enumerate(SKY.sections)]
    page = explainer.page(SKY.model_copy(update={"sections": sections}), [], Q)
    assert page.count('class="banner"') == explainer.MAX_SECTION_PHOTOS
    assert page.count(brand.photo_uri(SKY.hero_photo)) == 1


def test_kpmg_themes_have_no_emoji_but_creative_does():
    assert not any(ord(ch) >= 0x1F300 for ch in explainer.page(SKY.model_copy(update={"theme": "corporate"}), SOURCES, Q))
    assert "\U0001F4A1" in explainer.page(SKY, SOURCES, Q)  # the default creative look


def test_page_escapes_model_text():
    evil = SKY.model_copy(update={"title": "<script>alert(1)</script>", "follow_ups": ['a" onclick="x']})
    page = explainer.page(evil, [], Q)
    assert "<script>alert(1)" not in page and 'onclick="x' not in page


DIAGRAM_TYPES = ["flow", "cycle", "parts", "compare", "funnel", "roadmap", "timeline", "staircase", "pyramid", "matrix", "pillars"]


@pytest.mark.parametrize("kind", DIAGRAM_TYPES)
def test_every_diagram_type_draws(kind):
    nodes = [DiagramNode(label=f"Node {i}", note=f"note {i}", value=f"{(5 - i) * 100}", side="left" if i % 2 else "right")
             for i in range(5)]
    out = visuals.render(Diagram(type=kind, caption="c", nodes=nodes, left_title="L", right_title="R",
                                 x_axis="Ease", y_axis="Value"), "Hub")
    shown = 4 if kind in ("matrix", "pillars") else 5  # 2x2 and pillar rows take at most 4
    assert out.startswith("<figure") and all(f"Node {i}" in out for i in range(shown))
    assert all(f"note {i}" in out for i in range(shown))


def test_schema_offers_every_drawn_diagram_type():
    assert set(Diagram.model_fields["type"].annotation.__args__) == set(DIAGRAM_TYPES)


def test_funnel_shows_stage_conversion():
    nodes = [DiagramNode(label=l, note="n", value=v) for l, v in [("Leads", "10,000"), ("Deals", "4,200")]]
    assert "42%" in visuals.render(Diagram(type="funnel", caption="c", nodes=nodes), "t")


def test_key_stat_icons_are_inline_and_follow_colour():
    stats = [Stat(value="680", label="people", icon="people-group"), Stat(value="1.6", label="revenue")]
    page = explainer.page(SKY.model_copy(update={"key_stats": stats}), [], Q)
    assert page.count('class="ic"') == 1 and 'stroke="currentColor"' in page
    for icon in brand.ICON_IDS:
        svg = brand.icon_svg(icon)
        assert svg.startswith("<svg") and "metadata" not in svg and "currentColor" in svg


def test_welcome_and_error_cards_validate():
    validate.check(render.welcome_card())
    validate.check(render.error_card("Why?"))


LAST = {"question": Q, "level": "expert"}


@pytest.mark.parametrize("text,last,expected", [
    ("hi", None, None),
    ("  ", None, None),
    (Q, None, (Q, "expert")),
    ("Explain it like I'm 5: " + Q, None, (Q, "eli5")),
    ("Explain it in a simpler way: " + Q, None, (Q, "eli5")),
    ("explain black holes in simple terms", None, ("black holes", "eli5")),
    ("explain inflation in plain English", None, ("inflation", "eli5")),
    ("simpler", LAST, (Q, "eli5")),
    ("make it simpler", LAST, (Q, "eli5")),
    ("simpler", None, None),
    ("What is simple interest?", None, ("What is simple interest?", "expert")),
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
    text, messages, remember, page, files, _ = asyncio.run(eli5.respond(_text_content("Why?")))
    validate.check(messages)
    assert remember is None and page is None
    assert eli5.parse(_components(messages)["retry"]["action"]["event"]["context"]["prompt"], None) == ("Why?", "expert")


def test_agent_remembers_question_for_level_requests(fake):
    async def run():
        runner = InMemoryRunner(agent=eli5.root_agent, app_name="eli5")
        session = await runner.session_service.create_session(app_name="eli5", user_id="u")
        out = []
        for msg in (_text_content(Q), _text_content("simpler")):
            out.append([e async for e in runner.run_async(user_id="u", session_id=session.id, new_message=msg)])
        return out

    first, second = asyncio.run(run())
    parts = [p for e in first if e.content for p in e.content.parts]
    assert parts[0].text.startswith("**Why is the sky blue?** (Expert)")
    assert len([p for p in parts if p.inline_data]) == 2
    assert second[0].content.parts[0].text.startswith("**Why is the sky blue?** (Simpler)")
    assert "new to the topic" not in fake.calls[0][0] and "new to the topic" in fake.calls[1][0]


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
    ("Explain this document in a simpler way", ("Explain this document", "eli5")),
    ("summarise the attached pdf", ("Explain this document", "expert")),
    ("what does section 3 say about fees?", ("what does section 3 say about fees?", "expert")),
])
def test_parse_document_questions(text, expected):
    assert eli5.parse(text, None) == expected


def test_bare_upload_explains_the_document_without_search(fake):
    docs = document.from_content(_upload("policy.pdf", "application/pdf", b"%PDF-1.7 ..."))
    text, messages, remember, page, files, _ = asyncio.run(eli5.respond(_upload("policy.pdf", "application/pdf", b"%PDF"), None, docs))
    validate.check(messages)
    assert remember == {"question": "Explain this document", "level": "expert"}
    contents, config = fake.calls[0]
    assert not config.tools and config.response_schema is Explanation
    parts = contents[0].parts
    assert parts[0].inline_data.mime_type == "application/pdf" and "faithfully and completely" in parts[-1].text
    page = _components(messages)["frame"]["htmlContent"]
    assert "Document explained · Expert" in page and "Based on your document" in page and "policy.pdf" in page
    ctx = json.loads(explainer.html.unescape(page.split('class="primary"')[1].split('data-ctx="')[1].split('"')[0]))
    assert ctx["prompt"] == "Explain this document in a simpler way" and ctx["level"] == "eli5"


def test_section_shows_where_it_comes_from():
    sections = [SKY.sections[0].model_copy(update={"doc_ref": "Section 2.1"})]
    page = explainer.page(SKY.model_copy(update={"sections": sections}), [], Q, documents=["a.pdf"])
    assert "From the document: Section 2.1" in page


def test_follow_up_uses_the_uploaded_document(fake):
    async def run():
        runner = InMemoryRunner(agent=eli5.root_agent, app_name="eli5")
        session = await runner.session_service.create_session(app_name="eli5", user_id="u")
        for msg in (_upload("terms.docx", document.DOCX, DOCX_BYTES), _text_content("simpler")):
            [e async for e in runner.run_async(user_id="u", session_id=session.id, new_message=msg)]

    asyncio.run(run())
    first, second = (c[0][0].parts for c in fake.calls)
    assert "The fee is 2.5%." in first[0].text and "The fee is 2.5%." in second[0].text
    assert "new to the topic" in second[-1].text and not fake.calls[1][1].tools


def test_page_no_longer_prints_itself():
    page = explainer.page(SKY, [], Q)
    assert "window.print" not in page and "@media print" not in page and "Save as PDF" not in page


def test_page_has_motion_poster_that_respects_reduced_motion():
    page = explainer.page(SKY, [], Q)
    assert "@keyframes kb" in page and 'class="frames"' in page and 'class="sweep"' in page
    assert "IntersectionObserver" in page and "requestAnimationFrame" in page  # scroll reveal, KPI count-up
    assert "prefers-reduced-motion:reduce" in page and "cover.classList.add('go')" in page
    assert 'id="motion"' in page and "Play motion" in page  # opt-in when Windows animation effects are off


def test_card_has_native_download_pdf_button():
    comps = _components(render.explanation_card(SKY, SOURCES, Q, "eli5"))
    assert comps["pdf"]["label"] == "Download PDF" and "pdf" in comps["root"]["children"]
    assert comps["pdf"]["action"]["event"] == {"name": "pdf", "context": {"question": Q, "level": "eli5", "theme": "creative"}}
    assert comps["root"]["cardTitle"].endswith("· Simpler")


def _all_kinds():
    """SKY with every chart and several diagram types, to exercise the PDF layouts."""
    sections = list(SKY.sections)
    kinds = list(CHARTS.values()) + [None]
    nodes = [DiagramNode(label=f"Node {i}", note=f"note {i}", value=str(i), side="left" if i % 2 else "right") for i in range(4)]
    for i, s in enumerate(sections):
        sections[i] = s.model_copy(update={"chart": kinds[i % len(kinds)],
                                           "diagram": Diagram(type=DIAGRAM_TYPES[i * 3 % 11], caption="c", nodes=nodes,
                                                              left_title="L", right_title="R", center="Hub")})
    return SKY.model_copy(update={"sections": sections})


def test_pdf_is_branded_and_complete():
    data = pdf.build(_all_kinds(), SOURCES, "expert", ["policy.pdf"])
    assert data.startswith(b"%PDF") and 20_000 < len(data) < 600_000  # well under GE's ~1 MB part limit
    assert b"LiberationSans" in data  # embedded font, so symbols like the lambda in 1/x4 render
    assert pdf.filename("Why is the sky blue?") == "Why-is-the-sky-blue.pdf"


def _pdf_click(question=Q, level="expert"):
    return _click_content({"name": "pdf", "context": {"question": question, "level": level}})


def test_download_pdf_reuses_the_explanation_in_session(fake):
    async def run():
        runner = InMemoryRunner(agent=eli5.root_agent, app_name="eli5")
        session = await runner.session_service.create_session(app_name="eli5", user_id="u")
        out = []
        for msg in (_text_content(Q), _pdf_click()):
            out.append([e async for e in runner.run_async(user_id="u", session_id=session.id, new_message=msg)])
        return out

    _, second = asyncio.run(run())
    parts = second[0].content.parts
    assert parts[0].text.startswith("Here is **Why is the sky blue?** (Expert) as a PDF")
    blob = parts[1].inline_data
    assert blob.mime_type == "application/pdf" and blob.display_name == "Why-is-the-sky-blue.pdf" and blob.data.startswith(b"%PDF")
    assert len(fake.calls) == 1  # no second model call: rebuilt from session state


def test_download_pdf_for_an_old_card_explains_again(fake):
    reply = asyncio.run(eli5.respond(_pdf_click("Why is grass green?", "eli5"), None, None, []))
    assert reply.files[0].inline_data.mime_type == "application/pdf" and len(fake.calls) == 1
    assert "new to the topic" in fake.calls[0][0]


def test_download_pdf_failure_is_a_message(monkeypatch):
    _use(monkeypatch, FakeModels(fail=True))
    reply = asyncio.run(eli5.respond(_pdf_click(), None, None, []))
    assert reply.text.startswith("Sorry, I couldn't make the PDF") and not reply.files


CHARTS = {
    "bar": Chart(type="bar", title="Scattering vs wavelength", unit="x", labels=["Violet 400 nm", "Blue 450 nm", "Red 700 nm"],
                 series=[Series(name="Relative", values=[9.4, 5.9, 1])], caption="Short waves scatter far more.", source="Table 1"),
    "line": Chart(type="line", title="Fee by year", unit="£m", labels=["2023", "2024", "2025", "2026"],
                  series=[Series(name="Fee", values=[1.2, 1.5, 2.25, 3])], caption="Fees more than doubled."),
    "donut": Chart(type="donut", title="Air by volume", unit="%", labels=["Nitrogen", "Oxygen", "Other"],
                   series=[Series(name="Share", values=[78, 21, 1])], caption="Nitrogen dominates."),
}


@pytest.mark.parametrize("kind", list(CHARTS))
def test_every_chart_type_draws_with_exact_values(kind):
    out = charts.render(CHARTS[kind])
    assert out.startswith('<figure class="chart"') and CHARTS[kind].caption in out
    expected = {"bar": ["9.4x", "5.9x", "1x"], "line": ["£1.2m", "£2.25m", "£3m"], "donut": ["78%", "21%", "1%"]}[kind]
    assert all(v in out for v in expected)


def test_chart_with_mismatched_series_is_skipped():
    bad = Chart(type="bar", title="t", labels=["a", "b", "c"], series=[Series(name="s", values=[1])], caption="c")
    assert charts.render(bad) == "" and charts.render(None) == ""


def test_chart_appears_in_its_section():
    sections = [SKY.sections[0].model_copy(update={"chart": CHARTS["donut"]})] + SKY.sections[1:]
    page = explainer.page(SKY.model_copy(update={"sections": sections}), [], Q)
    assert page.count('<figure class="chart"') == 1 and "Nitrogen" in page


# --- KPMG theme recipes (brand/extract/08-themes) ----------------------------------------

@pytest.mark.parametrize("theme", list(brand.THEMES))
def test_every_theme_styles_the_page_and_pdf(theme):
    x = SKY.model_copy(update={"theme": theme, "hero_photo": brand.THEMES[theme].heroes[0]})
    page = explainer.page(x, [], Q)
    assert f'<body class="t-{theme}"' in page
    assert all(h in brand.PHOTO_IDS for h in brand.THEMES[theme].heroes)
    assert pdf.build(x, [], "expert").startswith(b"%PDF")


def test_finance_theme_puts_three_figures_on_the_cover():
    page = explainer.page(SKY.model_copy(update={"theme": "finance-data"}), [], Q)
    cover = page.split("</header>")[0]
    assert 'class="cstats' in cover and all(s.value in cover for s in SKY.key_stats[:3])
    assert page.count('class="kpi"') == max(len(SKY.key_stats) - 3, 0) and 'class="tabs"' in page


def test_theme_defaults_to_creative_and_is_offered_to_the_model(fake):
    assert Explanation.model_validate_json(SKY.model_copy(update={}).model_dump_json(exclude={"theme"})).theme == "creative"
    asyncio.run(llm.explain(eli5._client, Q))
    assert "finance-data" in json.dumps(Explanation.model_json_schema())
    assert "Art direction" in fake.calls[0][0]


def test_page_offers_the_other_themes():
    page = explainer.page(SKY.model_copy(update={"theme": "ai"}), [], Q)
    bar = page.split('class="themes"')[1].split("</div>")[0]
    assert 'aria-current="true">AI<' in bar and bar.count('data-action="theme"') == 4
    ctx = json.loads(explainer.html.unescape(bar.split('data-ctx="')[1].split('"')[0]))
    assert ctx == {"prompt": "Show this in the KPMG Creative theme", "theme": "creative", "question": Q, "level": "expert"}


def _theme_click(theme, question=Q, level="expert"):
    return _click_content({"name": "theme", "context": {"prompt": "x", "theme": theme, "question": question, "level": level}})


def test_theme_switch_reuses_the_explanation_without_a_model_call(fake):
    async def run():
        runner = InMemoryRunner(agent=eli5.root_agent, app_name="eli5")
        session = await runner.session_service.create_session(app_name="eli5", user_id="u")
        out = []
        for msg in (_text_content(Q), _theme_click("finance-data"), _pdf_click(), _text_content("switch to the AI theme")):
            out.append([e async for e in runner.run_async(user_id="u", session_id=session.id, new_message=msg)])
        return out

    _, switched, pdf_reply, typed = asyncio.run(run())
    assert len(fake.calls) == 1  # only the first answer called the model
    assert switched[0].content.parts[0].text == "**Why is the sky blue?** in the KPMG Finance Data theme."
    page = _components([json.loads(p.inline_data.data[len(a2ui.TAG_START):-len(a2ui.TAG_END)])["data"]
                        for p in switched[0].content.parts[1:]])["frame"]["htmlContent"]
    assert '<body class="t-finance-data"' in page and brand.photo_uri("finance-dollar") in page
    assert pdf_reply[0].content.parts[1].inline_data.mime_type == "application/pdf"
    assert typed[0].content.parts[0].text.endswith("in the KPMG AI theme.")


def test_with_theme_keeps_a_fitting_cover_photo():
    x = SKY.model_copy(update={"hero_photo": "glass-towers"})
    assert eli5.with_theme(x, "finance-data").hero_photo == "glass-towers"
    assert eli5.with_theme(x, "ai").hero_photo == brand.THEMES["ai"].heroes[0]


@pytest.mark.parametrize("text,theme", [
    ("switch to the AI theme", "ai"), ("use the KPMG finance data theme", "finance-data"),
    ("please show it in the AI platform look", "ai-platform"), ("change to corporate style", "corporate"),
    ("What is the corporate style guide?", None), ("How does the AI theme of the report land?", None),
])
def test_typed_theme_switch(text, theme):
    m = eli5._THEME_TEXT.match(text)
    assert (eli5._theme_id(m.group(1)) if m else None) == theme


# --- the default Creative look ---------------------------------------------------------------

def _creative(**upd):
    secs = [s.model_copy(update={"emoji": "☀️", "photo": p}) for s, p in zip(SKY.sections, ["neon-silk", "glass-rings", None, None])]
    return SKY.model_copy(update={"sections": secs, "emoji": "\U0001F324️", "theme": "creative", **upd})


def test_creative_is_the_default_with_accent_emoji_and_motion():
    page = explainer.page(_creative(accent="magenta"), [], Q)
    assert '<body class="t-creative" style="--a1:#AB0D82' in page and "class=blobs" in page
    assert 'class="big-emoji"' in page and 'class="emo"' in page and "cover cv-poster" in page


def test_mosaic_cover_moves_section_photos_into_the_cover():
    page = explainer.page(_creative(cover_style="mosaic"), [], Q)
    assert "cover cv-mosaic" in page and page.count('class="banner"') == 0
    assert page.count(brand.photo_uri("neon-silk")) == 1  # in the cover, not repeated as a banner
    few = SKY.model_copy(update={"theme": "creative", "cover_style": "mosaic",
                                 "sections": [x.model_copy(update={"photo": None}) for x in SKY.sections]})
    assert "cover cv-poster" in explainer.page(few, [], Q)


def test_emoji_fields_are_sanitised_and_left_out_of_the_pdf():
    assert explainer._emoji("<b>") == "" and explainer._emoji("rocket") == "" and explainer._emoji("\U0001F680") == "\U0001F680"
    assert pdf._x("\U0001F680 Launch") == "Launch"
    assert pdf.build(_creative(cover_style="split", accent="purple"), [], "expert").startswith(b"%PDF")


def test_theme_switch_is_remembered_for_new_answers(fake):
    async def run():
        runner = InMemoryRunner(agent=eli5.root_agent, app_name="eli5")
        session = await runner.session_service.create_session(app_name="eli5", user_id="u")
        out = []
        for msg in (_text_content(Q), _theme_click("ai"), _text_content("How do rainbows form?")):
            out.append([e async for e in runner.run_async(user_id="u", session_id=session.id, new_message=msg)])
        return out

    first, _, third = asyncio.run(run())
    frame = lambda ev: _components([json.loads(p.inline_data.data[len(a2ui.TAG_START):-len(a2ui.TAG_END)])["data"]  # noqa: E731
                                    for p in ev[0].content.parts[1:]])["frame"]["htmlContent"]
    assert '<body class="t-creative"' in frame(first) and '<body class="t-ai"' in frame(third)
