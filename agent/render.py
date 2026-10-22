"""A2UI v0.9 cards for the ELI5 agent: the explainer (Canvas + IFrameSrcdoc), welcome and error."""
from . import a2ui, explainer
from .schema import LEVELS, Explanation

FRAME_HEIGHT = 960  # the page scrolls inside the frame when it is longer

EXAMPLES = (
    "Why is the sky blue?",
    "How do vaccines work?",
    "What is a black hole?",
    "How does the internet work?",
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


def explanation_card(e: Explanation, sources: list[dict], question: str, level: str = "eli5") -> list[dict]:
    """Opener card in chat; the explainer page opens in the side panel. Source links are repeated
    natively under the frame because links inside the sandboxed frame may not open."""
    children = ["frame"]
    comps = [
        {"id": "frame", "component": "IFrameSrcdoc", "htmlContent": explainer.page(e, sources, question, level), "height": FRAME_HEIGHT},
    ]
    if sources:
        links = " · ".join(f"[{i}. {_md_label(s['title'])}]({s['uri']})" for i, s in enumerate(sources, 1))
        comps.append(_text("sources", f"**Sources:** {links}", "caption"))
        children.append("sources")
    root = {"id": "root", "component": "Canvas", "cardTitle": f"{e.title} · {LEVELS[level][0]}", "cardDescription": e.one_liner,
            "cardIcon": "lightbulb", "autoOpen": True, "children": children}
    return a2ui.surface("eli5", [root, *comps])


def welcome_card() -> list[dict]:
    buttons = [_ask_button(f"ex{i}", q) for i, q in enumerate(EXAMPLES)]
    return _card("eli5-welcome", [
        _text("title", "Explain like I'm 5", "h4"),
        _text("intro", "Ask me about anything. I'll explain it like you're 5, with a picture. "
                       "Then you can go up to 10, 15 or expert level."),
        *buttons,
    ])


def error_card(question: str) -> list[dict]:
    return _card("eli5-error", [
        _text("title", "I couldn't explain that one", "h4"),
        _text("msg", f"Something went wrong while explaining **{question}**. Try again, or ask it another way."),
        _ask_button("retry", question),
    ])
