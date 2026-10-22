"""ELI5 agent for Gemini Enterprise.

Each turn: find the question (typed, or an "ask" click from a follow-up chip or example
button), research it with Google Search grounding, write the four-level Explanation, and
reply with one line of text plus the explainer card (Canvas + IFrameSrcdoc).
Greetings and empty turns get the welcome card. AGENT_MODE=probe serves the step 0 probe.
"""
import logging
import os
import re
from typing import AsyncGenerator, Callable

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types as genai_types

from . import a2ui, explainer, llm, render, validate

log = logging.getLogger(__name__)

MAX_QUESTION_CHARS = 500
_GREETING = re.compile(r"^(hi|hello|hey|help|start|menu|what can you do\??|who are you\??)[!. ]*$", re.I)

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


def question_for(content) -> str | None:
    """The question this turn asks, or None for a greeting, an empty turn or an unknown click."""
    action = a2ui.extract_action(content)
    if action is not None:
        prompt = (action.get("context") or {}).get("prompt") if action.get("name") == explainer.ASK_ACTION else None
        text = (prompt or "").strip()
    else:
        text = _user_text(content)
    if not text or _GREETING.match(text):
        return None
    return text[:MAX_QUESTION_CHARS]


async def respond(content) -> tuple[str, list[dict]]:
    """(one-line reply, A2UI messages) for this turn."""
    question = question_for(content)
    if question is None:
        return "Ask me anything and I'll explain it like you're 5, then go deeper.", render.welcome_card()
    try:
        expl, sources = await llm.explain(_get_client(), question)
        messages = render.explanation_card(expl, sources)
        validate.check(messages)
        return f"**{expl.title}**: {expl.one_liner}", messages
    except Exception:  # the user gets a retry card instead of a broken turn
        log.exception("explain failed for %r", question)
        return "Sorry, that one didn't work.", render.error_card(question)


class Eli5Agent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        text, messages = await respond(ctx.user_content)
        validate.check(messages)
        parts = [genai_types.Part(text=text)] + [a2ui.to_genai_part(m) for m in messages]
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=genai_types.Content(role="model", parts=parts),
        )


if os.getenv("AGENT_MODE") == "probe":
    from .probe_agent import probe_agent as root_agent
else:
    root_agent = Eli5Agent(name="eli5", description="Explains any topic at four levels, from a 5-year-old's to an expert's.")
