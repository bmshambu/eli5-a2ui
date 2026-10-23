"""A2UI v0.9 cards for the explainer agent: the explainer (Canvas + IFrameSrcdoc), welcome and error."""
from . import a2ui, explainer, maker
from .schema import DEFAULT_LEVEL, KINDS, LEVELS, Creation, Explanation

FRAME_HEIGHT = 1100  # the page scrolls inside the frame when it is longer
PDF_ACTION = "pdf"  # the agent builds the PDF (pdf.py) and sends it back as a file in chat

EXAMPLES = (
    "Why is the sky blue?",
    "How do vaccines work?",
    "What is a black hole?",
    "How does the internet work?",
    "Create a poster for our AI training week",
    "Draft an email inviting the team to a town hall",
)


def _text(cid: str, text: str, hint: str = "body") -> dict:
    return {"id": cid, "component": "MaterialText", "text": text, "usageHint": hint}


def _md_label(text: str) -> str:
    """Link text safe inside markdown [..](..)."""
    return text.replace("[", "(").replace("]", ")")


def _ask_button(cid: str, question: str) -> dict:
    """A native button that sends the same action as the in-page chips."""
    return {"id": cid, "component": "MaterialButton", "label": question, "variant": "stroked",
            "action": {"event": {"name": explainer.ASK_ACTION, "context": {"prompt": question}}}}


def _card(prefix: str, children: list[dict]) -> list[dict]:
    comps = [
        {"id": "root", "component": "MaterialCard", "children": ["col"]},
        {"id": "col", "component": "MaterialColumn", "align": "stretch", "children": [c["id"] for c in children]},
        *children,
    ]
    return a2ui.surface(prefix, comps)


def explanation_card(e: Explanation, sources: list[dict], question: str, level: str = DEFAULT_LEVEL,
                     documents: list[str] = ()) -> list[dict]:
    """Opener card in chat; the explainer page opens in the side panel. Source links are repeated
    natively under the frame because links inside the sandboxed frame may not open. "Download PDF"
    is a native button too: the frame can't print or download, so the agent makes the file."""
    children = ["frame", "pdf"]
    comps = [
        {"id": "frame", "component": "IFrameSrcdoc", "htmlContent": explainer.page(e, sources, question, level, documents), "height": FRAME_HEIGHT},
        {"id": "pdf", "component": "MaterialButton", "label": "Download PDF", "variant": "stroked", "leadingIcon": "download",
         "action": {"event": {"name": PDF_ACTION, "context": {"question": question, "level": level, "theme": e.theme}}}},
    ]
    if sources:
        links = " · ".join(f"[{i}. {_md_label(s['title'])}]({s['uri']})" for i, s in enumerate(sources, 1))
        comps.append(_text("sources", f"**Sources:** {links}", "caption"))
        children.append("sources")
    root = {"id": "root", "component": "Canvas", "cardTitle": f"{e.title} · {LEVELS[level][0]}", "cardDescription": e.one_liner,
            "cardIcon": "lightbulb", "autoOpen": True, "children": children}
    return a2ui.surface("eli5", [root, *comps])


def creation_card(c: Creation, request: str) -> list[dict]:
    """A poster, email, social post or one-pager in the side panel, with a native Download PDF."""
    comps = [
        {"id": "frame", "component": "IFrameSrcdoc", "htmlContent": maker.page(c, request), "height": FRAME_HEIGHT},
        {"id": "pdf", "component": "MaterialButton", "label": "Download PDF", "variant": "stroked", "leadingIcon": "download",
         "action": {"event": {"name": PDF_ACTION, "context": {"kind": "create", "request": request, "theme": c.theme}}}},
    ]
    root = {"id": "root", "component": "Canvas", "cardTitle": f"{c.title} · {KINDS[c.kind][0]}", "cardDescription": c.tagline,
            "cardIcon": "brush", "autoOpen": True, "children": ["frame", "pdf"]}
    return a2ui.surface("eli5-make", [root, *comps])


def welcome_card() -> list[dict]:
    buttons = [_ask_button(f"ex{i}", q) for i, q in enumerate(EXAMPLES)]
    return _card("eli5-welcome", [
        _text("title", "Explain anything", "h4"),
        _text("intro", "Ask me about anything, or upload a document and ask me to explain it. I'll write a detailed, illustrated briefing. "
                       "Then ask me to explain it in a simpler way if you want the short, plain-English version. "
                       "I can also create on-brand content: a poster, an email, a social post or a one-pager."),
        *buttons,
    ])


def error_card(question: str) -> list[dict]:
    return _card("eli5-error", [
        _text("title", "I couldn't explain that one", "h4"),
        _text("msg", f"Something went wrong while explaining **{question}**. Try again, or ask it another way."),
        _ask_button("retry", question),
    ])
