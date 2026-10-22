"""ELI5 agent for Gemini Enterprise.

Each turn: find the question and the level (typed, or an "ask" click from the explainer page
or an example button), explain it at that one level, and reply with one line of text plus the
explainer card (Canvas + IFrameSrcdoc). New questions get a detailed Expert briefing; the
simpler ELI5 version is made only when asked (the follow-up button, "like I'm 5"). The last
question and level are kept in session state so "like I'm 5" alone works, and "go deeper"
goes back to Expert.
Documents: when the user uploads a file in GE chat, the page explains that document (no web
search), following its structure. Later turns in the session keep using the latest document.
Greetings and empty turns get the welcome card. AGENT_MODE=probe serves the step 0 probe.
"""
import logging
import os
import re
from typing import AsyncGenerator, Callable

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types as genai_types

from . import a2ui, document, explainer, llm, render, validate
from .schema import DEFAULT_LEVEL, LEVELS

log = logging.getLogger(__name__)

MAX_QUESTION_CHARS = 500
STATE_KEY = "eli5_last"  # {"question": str, "level": str}
DOC_QUESTION = explainer.DOC_QUESTION

_GREETING = re.compile(r"^(hi|hello|hey|help|start|menu|what can you do\??|who are you\??)[!. ]*$", re.I)
_LEVEL = re.compile(
    r"\b(?:eli\s*-?\s*(5|10|15|expert)"
    r"|like\s+(?:i'?\s*a?m|i\s+am|i\s+was)\s+(?:a\s+|an\s+)?(5|10|15|five|ten|fifteen|expert)(?:\s*(?:years?[\s-]*old|yo))?"
    r"|(?:at\s+)?(expert)\s+level)\b",
    re.I,
)
# Only Expert and ELI5 exist; "like I'm 10/15" is read as the simple version.
_WORDS = {"5": "eli5", "five": "eli5", "10": "eli5", "ten": "eli5", "15": "eli5", "fifteen": "eli5", "expert": "expert"}
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
    if _DEEPER.match(text):
        if not last:
            return None
        return last["question"], DEFAULT_LEVEL
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


async def respond(content, last: dict | None = None, docs: list | None = None) -> tuple[str, list[dict], dict | None]:
    """(one-line reply, A2UI messages, new session memory or None) for this turn. `docs` are the
    documents to explain from (this turn's upload, or the latest one in the session)."""
    asked = question_for(content, last)
    if docs and asked is None:
        # A bare upload (or "hi", or "like I'm 5" with nothing asked yet) means: explain the document.
        asked = parse(_user_text(content), {"question": DOC_QUESTION, "level": DEFAULT_LEVEL}) or (DOC_QUESTION, DEFAULT_LEVEL)
    if asked is None:
        return "Ask me anything, or upload a document, and I'll give you a detailed briefing. Ask for ELI5 any time for the simple version.", render.welcome_card(), None
    question, level = asked
    try:
        expl, sources = await llm.explain(_get_client(), question, level, docs)
        messages = render.explanation_card(expl, sources, question, level, [d.name for d in docs or []])
        validate.check(messages)
        return (f"**{expl.title}** ({LEVELS[level][0]}): {expl.one_liner}", messages,
                {"question": question, "level": level})
    except Exception:  # the user gets a retry card instead of a broken turn
        log.exception("explain failed for %r at %s", question, level)
        return "Sorry, that one didn't work.", render.error_card(explainer.level_prompt(level, question)), None


class Eli5Agent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        log.info("turn parts: %s", document.describe(ctx.user_content))
        uploaded = document.from_content(ctx.user_content)
        # A new upload starts a new topic, so "like I'm 5" with it means this document.
        last = None if uploaded else ctx.session.state.get(STATE_KEY)
        docs = uploaded or document.latest(ctx.session.events)
        text, messages, remember = await respond(ctx.user_content, last, docs)
        validate.check(messages)
        parts = [genai_types.Part(text=text)] + [a2ui.to_genai_part(m) for m in messages]
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=genai_types.Content(role="model", parts=parts),
            actions=EventActions(state_delta={STATE_KEY: remember} if remember else {}),
        )


if os.getenv("AGENT_MODE") == "probe":
    from .probe_agent import probe_agent as root_agent
else:
    root_agent = Eli5Agent(name="eli5", description="Explains any topic as a detailed expert briefing, with an ELI5 version on request.")
