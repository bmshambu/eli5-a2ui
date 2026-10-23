"""The model call behind every explanation: one level per call (Expert first, the simpler version on request).

With uploaded documents: one structured call over the documents and no web search, so the
answer stays faithful to them (explain_documents).

Fast path: one Gemini call with Google Search grounding AND a response_schema (supported
by Gemini 3 and later). If the model rejects that combination, fall back for good to two
calls: research() with grounding, then write() with the schema.
The client is passed in so tests can use a fake one.
"""
import json
import logging
import os

from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from . import brand
from .schema import DEFAULT_LEVEL, KINDS, LEVELS, Creation, Explanation

log = logging.getLogger(__name__)

MAX_SOURCES = 6

_STYLE = """Write for {audience}
Length: {length}
Plain text only: no markdown, HTML, emoji or citation markers.
Prefer visuals to long text. Give a section a diagram where a picture teaches better than words
(at least one section should have one), and pick the diagram type that fits the idea: funnel for
a pipeline or conversion, roadmap for a phased plan with dates, timeline for dated milestones,
staircase for a maturity model, pyramid for a hierarchy, matrix for a 2x2 prioritisation,
pillars for 3 or 4 key messages with a stat each, flow for a process, cycle for a loop, parts for
the pieces of a whole, compare for two options. Vary the types across sections. Give a key stat
a brand icon only where one plainly fits.
Give a section a chart when it turns on 3 or more comparable numbers (a trend, a breakdown, a
comparison). Charts may only use numbers stated in the document or your sources, exactly as
given: never estimate, interpolate or invent a value, and leave the chart out if the numbers
are not there. Name where they come from in the chart's source. When a section has a chart or
diagram, keep its paragraphs short and let the visual carry the detail. Choose photos only from this
list of brand photos, by id; pick the closest fit, use each photo at most once, and give at
most 2 sections a photo:
{photos}
Art direction (the creative look): use theme creative, and pick an accent, a cover_style and emojis
that suit this topic, so different topics look different. Give the cover one emoji, each section one
emoji and each key stat one emoji, all standard Unicode and apt (no faces for serious topics). Emojis go
only in those emoji fields, never in the text. Choose photos from the whole catalogue.
The 3 follow_ups are natural next questions on new angles, each a full question under 70
characters. Do not offer a simpler or deeper explanation as a follow-up: the page already has that."""

EXPLAIN_PROMPT = """You write clear, accurate explainers for KPMG professionals. Search the web to check the facts,
then explain the question below.
""" + _STYLE + """

Question: {question}"""

RESEARCH_PROMPT = """Research this question for an explainer aimed at {audience}
Question: {question}

Write plain factual notes: the core mechanisms, key numbers and names, how it is used in
practice, trade-offs, common misconceptions and open questions. No preamble."""

WRITER_PROMPT = """You write clear, accurate explainers for KPMG professionals. Using the research notes below,
explain the question.
""" + _STYLE + """

Question: {question}

Research notes:
{notes}"""

DOC_PROMPT = """You explain documents to KPMG professionals. The user uploaded the document(s) above
and asks: {question}

Explain the document itself, faithfully and completely:
- Follow the document's own structure: one section per major part, in its order, with doc_ref
  saying where it comes from (section, page or slide). Cover every major part; do not drop any.
- Keep the substance: every key figure, date, name, threshold, obligation, recommendation and
  decision that matters. Quote numbers exactly as the document gives them.
- Use only what the document says. Do not add outside facts; if you explain a term the document
  assumes, keep it brief. Put gaps, ambiguities and things the document leaves open in caveats.
- key_stats must be numbers that appear in the document. Sources are not needed.
- If the user asks about one part of the document, focus on that part but keep the context.
""" + _STYLE

# How much to write about a document: as much as its structure needs, not a fixed count.
DOC_LENGTH = {
    "expert": "one section per major part of the document (3 to 8), each with 2 or 3 substantial paragraphs; "
              "3 or 4 key stats; caveats for anything unclear or open; 4 to 8 glossary terms.",
    "eli5": "2 to 4 short sections covering the document's main points in order; 2 key stats; no caveats; no glossary.",
}

CREATE_PROMPT = """You create on-brand KPMG content for KPMG professionals: posters, emails, social posts
and one-pagers. Make what the user asks for below.
Kinds: {kinds}
Pick the kind that matches the request ({hint}). Write for the format: {length}
Facts: use only what the user, their document or the briefing gives you. Never invent names,
people, dates, times, places, prices, numbers or links: where one is needed and not given,
write a [placeholder] in square brackets, e.g. [Date], [Venue], [Your name], [Link].
Tone: professional, clear and human, KPMG's voice; follow any tone the user asks for.
Plain text only: no markdown, HTML or emoji in the text (emojis only in the emoji fields).
Art direction: theme creative; pick the accent and one emoji that suit the message, and the
brand photo that fits best, by id, from this list:
{photos}
The 3 ideas are quick changes the user might want next (tone, length, a detail, another format).
{context}
Request: {request}"""

CREATE_LENGTH = {k: v[2] for k, v in KINDS.items()}


def _brief(page: dict | None) -> str:
    """The briefing the user just saw, so "make a poster of this" has something to work from."""
    if not page:
        return ""
    e = page.get("explanation") or {}
    stats = "; ".join(f"{s.get('value')} {s.get('label')}" for s in e.get("key_stats") or [])
    lines = [f"Title: {e.get('title')}", f"Summary: {e.get('summary')}",
             "Takeaways: " + " | ".join(e.get("takeaways") or []), f"Key stats: {stats}"]
    return "Briefing the user just read (use it if the request refers to it, e.g. 'this' or 'it'):\n" + "\n".join(lines)


async def create(client, request: str, kind: str | None = None, docs: list | None = None,
                 previous: dict | None = None, page: dict | None = None) -> Creation:
    """One structured call that writes a poster, email, social post or one-pager. `previous`
    is the creation being changed ("make it shorter"); `page` the briefing just shown."""
    context = []
    if previous:
        context.append("The user is changing this earlier draft; keep what they did not ask to change "
                       "(change the kind only if they ask for another format):\n" + json.dumps(previous, ensure_ascii=False))
    elif page:
        context.append(_brief(page))
    if docs:
        context.append("The user's document(s) are attached above; take the facts from them.")
    prompt = CREATE_PROMPT.format(
        kinds="; ".join(f"{k} = {v[1]}" for k, v in KINDS.items()),
        hint=f"probably {kind}" if kind else "infer it from the request",
        length=" ".join(f"{v[0]}: {v[2]}" for v in KINDS.values()) if not kind else CREATE_LENGTH[kind],
        photos=brand.catalogue(), context="\n\n".join(context), request=request)
    parts = [*(d.part for d in docs or []), genai_types.Part(text=prompt)]
    response = await client.aio.models.generate_content(
        model=model_name(),
        contents=[genai_types.Content(role="user", parts=parts)],
        config=genai_types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=Creation,
            thinking_config=_thinking(), temperature=0.7,
        ),
    )
    if isinstance(response.parsed, Creation):
        return response.parsed
    return Creation.model_validate_json(response.text)


# None until the first call tells us whether search + response_schema work together.
_combined_ok: bool | None = None


def make_client() -> genai.Client:
    """Vertex AI client. MODEL_LOCATION is separate from the Agent Engine region because the
    newest Gemini models are served from the global endpoint only."""
    return genai.Client(
        vertexai=True,
        project=os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_CLOUD_PROJECT"),
        location=os.getenv("MODEL_LOCATION", "global"),
    )


def model_name() -> str:
    return os.getenv("MODEL", "gemini-4-argon")


def _thinking() -> genai_types.ThinkingConfig | None:
    """Low thinking keeps answers quick. THINKING_LEVEL='' leaves the model default."""
    level = os.getenv("THINKING_LEVEL", "low").strip()
    return genai_types.ThinkingConfig(thinking_level=level.upper()) if level else None


def _search() -> list[genai_types.Tool]:
    return [genai_types.Tool(google_search=genai_types.GoogleSearch())]


def _prompt_args(question: str, level: str) -> dict:
    return {"question": question, "audience": LEVELS[level][2], "length": LEVELS[level][3],
            "photos": brand.catalogue()}


def sources_from(response) -> list[dict]:
    """Deduped web sources from a grounded response: [{"title", "uri"}]. Empty when the model
    answered without searching."""
    seen, out = set(), []
    for cand in getattr(response, "candidates", None) or []:
        meta = getattr(cand, "grounding_metadata", None)
        for chunk in getattr(meta, "grounding_chunks", None) or []:
            web = getattr(chunk, "web", None)
            uri = getattr(web, "uri", None)
            if not uri or uri in seen:
                continue
            seen.add(uri)
            out.append({"title": (getattr(web, "title", None) or getattr(web, "domain", None) or uri).strip(),
                        "uri": uri})
    return out[:MAX_SOURCES]


def _parsed(response) -> Explanation:
    if isinstance(response.parsed, Explanation):
        return response.parsed
    return Explanation.model_validate_json(response.text)


async def _combined(client, question: str, level: str) -> tuple[Explanation, list[dict]]:
    response = await client.aio.models.generate_content(
        model=model_name(),
        contents=EXPLAIN_PROMPT.format(**_prompt_args(question, level)),
        config=genai_types.GenerateContentConfig(
            tools=_search(), response_mime_type="application/json", response_schema=Explanation,
            thinking_config=_thinking(), temperature=0.4,
        ),
    )
    return _parsed(response), sources_from(response)


async def research(client, question: str, level: str = DEFAULT_LEVEL) -> tuple[str, list[dict]]:
    response = await client.aio.models.generate_content(
        model=model_name(),
        contents=RESEARCH_PROMPT.format(**_prompt_args(question, level)),
        config=genai_types.GenerateContentConfig(tools=_search(), thinking_config=_thinking(), temperature=0.2),
    )
    return (response.text or "").strip(), sources_from(response)


async def write(client, question: str, level: str, notes: str) -> Explanation:
    response = await client.aio.models.generate_content(
        model=model_name(),
        contents=WRITER_PROMPT.format(notes=notes or "(none)", **_prompt_args(question, level)),
        config=genai_types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=Explanation,
            thinking_config=_thinking(), temperature=0.4,
        ),
    )
    return _parsed(response)


async def explain_documents(client, docs: list, question: str, level: str = DEFAULT_LEVEL) -> Explanation:
    """One structured call over the uploaded documents, without web search, so the answer
    stays grounded in the document."""
    prompt = DOC_PROMPT.format(**{**_prompt_args(question, level), "length": DOC_LENGTH[level]})
    response = await client.aio.models.generate_content(
        model=model_name(),
        contents=[genai_types.Content(role="user", parts=[*(d.part for d in docs), genai_types.Part(text=prompt)])],
        config=genai_types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=Explanation,
            thinking_config=_thinking(), temperature=0.2,
        ),
    )
    return _parsed(response)


async def explain(client, question: str, level: str = DEFAULT_LEVEL, docs: list | None = None) -> tuple[Explanation, list[dict]]:
    """The explanation and its web sources. With documents, the answer comes from them only."""
    if docs:
        return await explain_documents(client, docs, question, level), []
    global _combined_ok
    if _combined_ok is not False:
        try:
            result = await _combined(client, question, level)
            _combined_ok = True
            return result
        except genai_errors.ClientError as exc:
            # A 400 on the very first call means the model can't combine the two; anything else is real.
            if _combined_ok or exc.code != 400:
                raise
            log.warning("search + response_schema in one call failed; using two calls from now on", exc_info=True)
            _combined_ok = False
    notes, sources = await research(client, question, level)
    return await write(client, question, level, notes), sources
