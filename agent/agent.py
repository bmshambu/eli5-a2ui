"""Explainer agent for Gemini Enterprise (the repo's "ELI5" name is internal only).

Each turn: find the question and the level (typed, or an "ask" click from the explainer page
or an example button), explain it at that one level, and reply with one line of text plus the
explainer card (Canvas + IFrameSrcdoc). New questions get a detailed Expert briefing; the
simpler version is made only when asked (the follow-up button, "in a simpler way", "simpler",
or the old "like I'm 5"). The last question and level are kept in session state so "simpler"
alone works, and "go deeper" goes back to Expert.
Documents: when the user uploads a file in GE chat, the page explains that document (no web
search), following its structure. Later turns in the session keep using the latest document.
"Download PDF" and "Download PowerPoint" (native buttons under the page) rebuild the file from
the explanation kept in session state and send it back as a file. Greetings and empty turns get the welcome card. AGENT_MODE=probe serves the step 0 probe.
Create: "create a poster / draft an email / write a LinkedIn post / make a one-pager ..." makes
that thing in the same brand (maker.py) instead of explaining. "Turn this into a poster" after a
briefing works from that briefing; "make it shorter" or a change button after a creation edits it.
"""
import logging
import os
import re
from typing import AsyncGenerator, Callable, NamedTuple

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types as genai_types

from . import a2ui, document, explainer, llm, maker, pdf, render, slides, validate
from .brand import DEFAULT_THEME, THEMES
from .schema import DEFAULT_LEVEL, KINDS, LEVELS, Creation, Explanation

log = logging.getLogger(__name__)

MAX_QUESTION_CHARS = 500
STATE_KEY = "eli5_last"  # {"question": str, "level": str}
THEME_KEY = "eli5_theme"  # the theme the user last switched to; new answers use it (default Creative)
PAGES_KEY = "eli5_pages"  # the last few explanations shown, so "Download PDF" needs no new model call
MAX_PAGES = 4
CREATE_KEY = "eli5_create"  # {"request": str, "creation": dict}: the last thing made, so changes edit it
MODE_KEY = "eli5_mode"  # "create" or "explain": what the last answer was, so "make it shorter" goes to the right place
DOC_QUESTION = explainer.DOC_QUESTION

_GREETING = re.compile(r"^(hi|hello|hey|help|start|menu|what can you do\??|who are you\??)[!. ]*$", re.I)
_LEVEL = re.compile(
    r"\b(?:eli\s*-?\s*(5|10|15|expert)"
    r"|like\s+(?:i'?\s*a?m|i\s+am|i\s+was)\s+(?:a\s+|an\s+)?(5|10|15|five|ten|fifteen|expert)(?:\s*(?:years?[\s-]*old|yo))?"
    r"|(?:at\s+)?(expert)\s+level"
    r"|in\s+(?:a\s+)?(simpler|simple|plain)\s+(?:way|terms|words|english|language)"
    r"|in\s+(plain)\s+(?:english|language|words)"
    r"|(simpler)\s+(?:version|way))\b",
    re.I,
)
# Only Expert and the simpler version ("eli5") exist; "like I'm 10/15" is read as the simpler one.
_WORDS = {"5": "eli5", "five": "eli5", "10": "eli5", "ten": "eli5", "15": "eli5", "fifteen": "eli5", "expert": "expert",
          "simpler": "eli5", "simple": "eli5", "plain": "eli5"}
_SIMPLER = re.compile(r"^(?:make\s+it\s+)?(?:simpler|simplify(?:\s+it)?|simple\s+version|plain\s+english)[!. ]*$", re.I)
_DEEPER = re.compile(r"^(go\s+deeper|deeper|more\s+detail|tell\s+me\s+more|explain\s+more)[!. ]*$", re.I)
_DOC = re.compile(r"^\W*(?:(?:please|can\s+you|could\s+you)\s+)?(?:(?:explain|summari[sz]e|describe)\s+)?"
                  r"(?:the\s+|this\s+|my\s+|attached\s+|uploaded\s+)*(?:document|doc|file|pdf|deck|report|paper|attachment)s?\W*$", re.I)
_FILLER = re.compile(r"^\W*(?:(?:please|can\s+you|could\s+you)\s+)?(?:explain|describe)?\s*(?:it|this|that)?\W*$", re.I)

# Swapped in tests for a fake client; built lazily so the agent pickles for Agent Engine.
client_factory: Callable = llm.make_client
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = client_factory()
    return _client


def _user_text(content) -> str:
    if not content or not getattr(content, "parts", None):
        return ""
    return " ".join(p.text for p in content.parts if getattr(p, "text", None)).strip()


def parse(text: str, last: dict | None) -> tuple[str, str] | None:
    """(question, level) from what the user typed, or None for a greeting or nothing to explain.
    A level with no topic ("like I'm 10", "go deeper") applies to the last question."""
    text = (text or "").strip()
    if not text or _GREETING.match(text):
        return None
    if _DEEPER.match(text) or _SIMPLER.match(text):
        if not last:
            return None
        return last["question"], DEFAULT_LEVEL if _DEEPER.match(text) else "eli5"
    m = _LEVEL.search(text)
    if not m:
        return (DOC_QUESTION if _DOC.match(text) else text[:MAX_QUESTION_CHARS]), DEFAULT_LEVEL
    level = _WORDS[next(g for g in m.groups() if g).lower()]
    topic = (text[:m.start()] + " " + text[m.end():]).strip()
    topic = re.sub(r"^\W*(?:(?:please|can\s+you|could\s+you)\s+)?(?:explain|describe)\s*(?:it|this|that)?\s*[:,\-]?\s*", "", topic, flags=re.I)
    topic = topic.strip(" :,-")
    if not topic or _FILLER.match(topic):
        return (last["question"], level) if last else None
    return (DOC_QUESTION if _DOC.match(topic) else topic[:MAX_QUESTION_CHARS]), level


def question_for(content, last: dict | None = None) -> tuple[str, str] | None:
    """(question, level) this turn asks for, or None for a greeting, empty turn or unknown click."""
    action = a2ui.extract_action(content)
    if action is None:
        return parse(_user_text(content), last)
    if action.get("name") != explainer.ASK_ACTION:
        return None
    ctx = action.get("context") or {}
    if ctx.get("level") in LEVELS and ctx.get("question"):
        return str(ctx["question"])[:MAX_QUESTION_CHARS], ctx["level"]
    return parse(ctx.get("prompt") or "", last)


class Reply(NamedTuple):
    text: str  # the one-line reply
    messages: list[dict]  # A2UI messages
    remember: dict | None = None  # new STATE_KEY value
    page: dict | None = None  # the explanation shown, for PAGES_KEY
    files: tuple = ()  # file parts, e.g. the PDF
    theme: str | None = None  # new THEME_KEY value, when the user switched theme
    made: dict | None = None  # new CREATE_KEY value, when something was created


# "create a poster for ...", "draft an email to ...", "write a LinkedIn post about ...", "turn this into a one-pager"
_CREATE = re.compile(r"^\W*(?:(?:please|pls|kindly|can\s+you|could\s+you|would\s+you)\s+)?(?:help\s+me\s+)?(?:i\s+(?:want|need)\s+(?:you\s+)?(?:to\s+)?)?"
                     r"(?:create|make|design|draft|write|generate|build|prepare|produce|compose|turn|convert|do)\b.{0,80}?"
                     r"\b(poster|banner|e-?mail|mail|newsletter|linkedin|social|post|tweet|one[\s-]?pager|flyer|leaflet|"
                     r"fact\s*sheet|memo|announcement|invite|invitation)s?\b", re.I)
_KIND_WORDS = {"poster": "poster", "banner": "poster", "email": "email", "e-mail": "email", "mail": "email",
               "linkedin": "social", "social": "social", "post": "social", "tweet": "social"}
# A change to the thing just made: "make it shorter", "more formal", "add the date", "use a different photo".
_TWEAK = re.compile(r"^\W*(?:(?:please|pls|can\s+you|could\s+you|now)\s+)?(?:make|more|less|shorter|longer|change|add|remove|drop|"
                    r"use|try|rewrite|redo|another|swap|replace|put|mention|include|fix|keep|turn|convert|bolder|simpler|"
                    r"friendlier|warmer|punchier|formal|casual|tone|translate|shorten|lengthen|update|edit)\b", re.I)


def create_request(text: str) -> tuple[str, str | None] | None:
    """(request, kind or None) when the user asks for something to be made, else None."""
    text = (text or "").strip()
    m = _CREATE.search(text)
    if not m:
        return None
    word = re.sub(r"\s+", "", m.group(1).lower())
    return text[:MAX_QUESTION_CHARS], _KIND_WORDS.get(word, "flyer" if word not in ("invite", "invitation") else None)


# "switch to the AI theme", "use the finance data theme", "show it in the corporate look"
_THEME_TEXT = re.compile(r"^\W*(?:(?:please|can\s+you|could\s+you)\s+)?(?:switch|change|use|show|try|make|put|give)\b.{0,30}?\b(?:kpmg\s+)?"
                         r"(corporate|ai[\s-]*platform|finance(?:[\s-]*data)?|ai)\s+(?:theme|look|style)\b", re.I)


def _theme_id(name: str) -> str:
    name = re.sub(r"[\s-]+", "-", name.lower())
    return "finance-data" if name.startswith("finance") else name


def with_theme(expl: Explanation, theme: str) -> Explanation:
    """The explanation in another theme; the cover photo changes unless it already suits it."""
    heroes = THEMES[theme].heroes
    return expl.model_copy(update={"theme": theme, "hero_photo": expl.hero_photo if expl.hero_photo in heroes else heroes[0]})


async def _shown(question: str, level: str, pages: list | None, docs: list | None) -> tuple[Explanation, list, list]:
    """The explanation shown earlier (from session state), or made again if it is no longer there."""
    shown = next((p for p in reversed(pages or []) if p.get("question") == question and p.get("level") == level), None)
    if shown:
        return Explanation.model_validate(shown["explanation"]), shown["sources"], shown["documents"]
    expl, sources = await llm.explain(_get_client(), question, level, docs)
    return expl, sources, [d.name for d in docs or []]


def _card(expl: Explanation, sources: list, question: str, level: str, names: list) -> tuple[list[dict], dict]:
    messages = render.explanation_card(expl, sources, question, level, names)
    validate.check(messages)
    return messages, {"question": question, "level": level, "explanation": expl.model_dump(mode="json"),
                      "sources": sources, "documents": names}


async def switch_theme(ctx: dict, pages: list | None = None, docs: list | None = None) -> Reply:
    """The same explanation re-shown in another KPMG theme, from session state (no model call)."""
    question = str(ctx.get("question") or "")[:MAX_QUESTION_CHARS]
    level = ctx.get("level") if ctx.get("level") in LEVELS else DEFAULT_LEVEL
    theme = ctx.get("theme")
    if not question or theme not in THEMES:
        return Reply("Sorry, I couldn't tell which theme or explanation you meant. Ask the question again.", [])
    try:
        expl, sources, names = await _shown(question, level, pages, docs)
        expl = with_theme(expl, theme)
        messages, page = _card(expl, sources, question, level, names)
    except Exception:  # noqa: BLE001
        log.exception("theme switch failed for %r to %s", question, theme)
        return Reply("Sorry, I couldn't switch the theme. Try the button again.", [])
    return Reply(f"**{expl.title}** in the {THEMES[theme].name} theme.", messages, {"question": question, "level": level},
                 page, theme=theme)


# Download formats: file builders for an explanation and for a creation, mime type, name, label.
FORMATS = {
    render.PDF_ACTION: (pdf.build, pdf.build_creation, "application/pdf", pdf.filename, "a PDF"),
    render.PPTX_ACTION: (slides.build, slides.build_creation, slides.MIME, slides.filename, "a PowerPoint deck"),
}


def _file(fmt: str, data: bytes, title: str) -> tuple[str, genai_types.Part]:
    name = FORMATS[fmt][3](title)
    log.info("%s %s: %d bytes", fmt, name, len(data))
    return name, genai_types.Part(inline_data=genai_types.Blob(mime_type=FORMATS[fmt][2], data=data, display_name=name))


def _made_card(c: Creation, request: str) -> tuple[list[dict], dict]:
    messages = render.creation_card(c, request)
    validate.check(messages)
    return messages, {"request": request, "creation": c.model_dump(mode="json")}


def _made_text(c: Creation) -> str:
    text = f"**{c.title}** ({KINDS[c.kind][0]}): {c.tagline}"
    if c.kind in ("email", "social"):  # in chat too, so it can be copied from there
        text += "\n\n" + maker.plain_text(c)
    return text


async def make(request: str, kind: str | None, docs: list | None = None, previous: dict | None = None,
               page: dict | None = None, theme: str | None = None) -> Reply:
    """Something made on request (or a change to the last one when `previous` is given)."""
    try:
        c = await llm.create(_get_client(), request, kind, docs, (previous or {}).get("creation"), page)
        c = c.model_copy(update={"theme": theme if theme in THEMES else DEFAULT_THEME})
        if previous:  # the change applies to the original request
            request = previous.get("request") or request
        messages, made = _made_card(c, request)
    except Exception:  # noqa: BLE001  (the user gets a message, not a broken turn)
        log.exception("create failed for %r", request)
        return Reply("Sorry, I couldn't make that. Try again, or say it another way.", [])
    return Reply(_made_text(c), messages, made=made)


def switch_made_theme(made: dict | None, theme: str) -> Reply:
    """The last creation re-shown in another theme (no model call)."""
    if not made or theme not in THEMES:
        return Reply("Sorry, I couldn't tell what to restyle. Ask for it again.", [])
    c = Creation.model_validate(made["creation"]).model_copy(update={"theme": theme})
    messages, made = _made_card(c, made["request"])
    return Reply(f"**{c.title}** in the {THEMES[theme].name} theme.", messages, made=made, theme=theme)


def made_file(made: dict | None, theme: str | None = None, fmt: str = render.PDF_ACTION) -> Reply:
    """The last creation as a PDF or PowerPoint file."""
    if not made:
        return Reply("Sorry, I couldn't find that draft any more. Ask for it again.", [])
    try:
        c = Creation.model_validate(made["creation"])
        if theme in THEMES:
            c = c.model_copy(update={"theme": theme})
        name, part = _file(fmt, FORMATS[fmt][1](c), c.title)
    except Exception:  # noqa: BLE001
        log.exception("creation %s failed", fmt)
        return Reply(f"Sorry, I couldn't make {FORMATS[fmt][4]}. Try the download button again.", [])
    return Reply(f"Here is **{c.title}** ({KINDS[c.kind][0]}) as {FORMATS[fmt][4]}: {name}", [], files=(part,))


async def download_file(ctx: dict, pages: list | None = None, docs: list | None = None, fmt: str = render.PDF_ACTION) -> Reply:
    """The PDF or PowerPoint of the explanation the button was under. It is rebuilt from session
    state; an explanation that is no longer there (an old card) is made again."""
    question = str(ctx.get("question") or "")[:MAX_QUESTION_CHARS]
    level = ctx.get("level") if ctx.get("level") in LEVELS else DEFAULT_LEVEL
    if not question:
        return Reply("Sorry, I couldn't tell which explanation to save. Ask the question again.", [])
    try:
        expl, sources, names = await _shown(question, level, pages, docs)
        if ctx.get("theme") in THEMES:  # the theme of the card the button was under
            expl = with_theme(expl, ctx["theme"])
        name, part = _file(fmt, FORMATS[fmt][0](expl, sources, level, names), expl.title)
    except Exception:  # noqa: BLE001  (the user gets a message, not a broken turn)
        log.exception("%s failed for %r at %s", fmt, question, level)
        return Reply(f"Sorry, I couldn't make {FORMATS[fmt][4]}. Try the download button again.", [])
    return Reply(f"Here is **{expl.title}** ({LEVELS[level][0]}) as {FORMATS[fmt][4]}: {name}", [], files=(part,))


async def respond(content, last: dict | None = None, docs: list | None = None, pages: list | None = None,
                  theme: str | None = None, made: dict | None = None, mode: str | None = None) -> Reply:
    """The reply to this turn. `docs` are the documents to explain from (this turn's upload, or
    the latest one in the session); `pages` are the explanations shown earlier (for the PDF and
    theme switches); `theme` is the theme the user last switched to (Creative if none); `made`
    is the last thing created and `mode` whether the last answer was a creation or an explanation."""
    action = a2ui.extract_action(content)
    ctx = (action or {}).get("context") or {}
    if action and action.get("name") in FORMATS:
        fmt = action["name"]
        return made_file(made, ctx.get("theme"), fmt) if ctx.get("kind") == "create" else await download_file(ctx, pages, docs, fmt)
    if action and action.get("name") == explainer.THEME_ACTION:
        return switch_made_theme(made, ctx.get("theme")) if ctx.get("kind") == "create" else await switch_theme(ctx, pages, docs)
    if action and action.get("name") == maker.CREATE_ACTION:
        change = str(ctx.get("prompt") or "")[:MAX_QUESTION_CHARS]
        if made and change:
            return await make(change, (create_request(change) or (None, None))[1], docs, made, theme=theme)
        return await make(str(ctx.get("request") or change), None, docs, theme=theme)
    # What the user "said": typed text, or the prompt of a button that only carries a prompt (the
    # welcome examples and follow-up chips), so "Create a poster…" from a button creates too.
    if action is None:
        text = _user_text(content)
    elif action.get("name") == explainer.ASK_ACTION and not ctx.get("question"):
        text = str(ctx.get("prompt") or "")
    else:
        text = ""
    creating = mode == "create" and made
    m = _THEME_TEXT.match(text) if text else None
    if m and creating:
        return switch_made_theme(made, _theme_id(m.group(1)))
    if m and last:
        return await switch_theme({**last, "theme": _theme_id(m.group(1))}, pages, docs)
    wanted = create_request(text) if text else None
    if wanted:
        refers = re.search(r"\b(?:this|it|that|above)\b", text, re.I)
        previous = made if creating and refers else None
        brief = pages[-1] if pages and not creating and refers else None
        return await make(wanted[0], wanted[1], docs, previous, brief, theme)
    if creating and text and _TWEAK.match(text):
        return await make(text[:MAX_QUESTION_CHARS], None, docs, made, theme=theme)
    asked = question_for(content, last)
    if docs and asked is None:
        # A bare upload (or "hi", or "simpler" with nothing asked yet) means: explain the document.
        asked = parse(_user_text(content), {"question": DOC_QUESTION, "level": DEFAULT_LEVEL}) or (DOC_QUESTION, DEFAULT_LEVEL)
    if asked is None:
        return Reply("Ask me anything, or upload a document, and I'll give you a detailed briefing. "
                     "Ask me to explain it in a simpler way any time.", render.welcome_card())
    question, level = asked
    try:
        expl, sources = await llm.explain(_get_client(), question, level, docs)
        expl = with_theme(expl, theme if theme in THEMES else DEFAULT_THEME)
        messages, page = _card(expl, sources, question, level, [d.name for d in docs or []])
        return Reply(f"**{expl.title}** ({LEVELS[level][0]}): {expl.one_liner}", messages,
                     {"question": question, "level": level}, page)
    except Exception:  # the user gets a retry card instead of a broken turn
        log.exception("explain failed for %r at %s", question, level)
        return Reply("Sorry, that one didn't work.", render.error_card(explainer.level_prompt(level, question)))


class Eli5Agent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        log.info("turn parts: %s", document.describe(ctx.user_content))
        uploaded = document.from_content(ctx.user_content)
        # A new upload starts a new topic, so "simpler" with it means this document.
        last = None if uploaded else ctx.session.state.get(STATE_KEY)
        docs = uploaded or document.latest(ctx.session.events)
        pages = ctx.session.state.get(PAGES_KEY) or []
        state = ctx.session.state
        reply = await respond(ctx.user_content, last, docs, pages, state.get(THEME_KEY), state.get(CREATE_KEY), state.get(MODE_KEY))
        validate.check(reply.messages)
        parts = [genai_types.Part(text=reply.text), *reply.files] + [a2ui.to_genai_part(m) for m in reply.messages]
        delta = {STATE_KEY: reply.remember} if reply.remember else {}
        if reply.theme:
            delta[THEME_KEY] = reply.theme
        if reply.made:
            delta[CREATE_KEY], delta[MODE_KEY] = reply.made, "create"
        if reply.page:
            delta[MODE_KEY] = "explain"
            key = (reply.page["question"], reply.page["level"])
            delta[PAGES_KEY] = [p for p in pages if (p.get("question"), p.get("level")) != key][-(MAX_PAGES - 1):] + [reply.page]
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=genai_types.Content(role="model", parts=parts),
            actions=EventActions(state_delta=delta),
        )


if os.getenv("AGENT_MODE") == "probe":
    from .probe_agent import probe_agent as root_agent
else:
    root_agent = Eli5Agent(name="eli5", description="Explains any topic as a detailed expert briefing, with a simpler version on request, "
                                              "and creates on-brand posters, emails, social posts and one-pagers.")
