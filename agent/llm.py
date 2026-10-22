"""The two model calls behind every explanation.

  research(): Gemini with Google Search grounding gathers facts and the web sources behind them.
  write():    Gemini with a response_schema turns those notes into an Explanation.

They are separate calls because grounding and structured output are not combined in one
request. The client is passed in so tests can use a fake one.
"""
import os

from google import genai
from google.genai import types as genai_types

from .schema import Explanation

MAX_SOURCES = 6

RESEARCH_PROMPT = """Research this question for an explainer that goes from a 5-year-old's level up to an expert's.
Question: {question}

Write plain factual notes: the core mechanism, one or two numbers or names an expert would expect,
common misconceptions, and anything still debated. No preamble."""

WRITER_PROMPT = """You write "Explain like I'm 5" explainers. Using only the research notes and sources below,
explain the question at four levels:
  eli5:   a curious 5-year-old. Short words, one concrete everyday image, no jargon.
  eli10:  a 10-year-old. Simple cause and effect, one new word explained.
  eli15:  a high-school student. The real mechanism and the proper terms.
  expert: a specialist. Precise terms, numbers, caveats and what is still open.
Each level stands alone: do not say "as above". Cite sources inline as [n] using the numbers below,
only where that source supports the sentence. If no source fits, cite nothing and lower the confidence.
The diagram must teach the core idea at a glance. The 3 follow_ups are natural next questions the
user would type, each a full question under 70 characters.
Plain text only: no markdown, HTML or emoji.

Question: {question}

Research notes:
{notes}

Sources:
{sources}"""


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


def sources_from(response) -> list[dict]:
    """Deduped web sources from a grounded response: [{"title", "uri"}]."""
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


async def research(client, question: str) -> tuple[str, list[dict]]:
    response = await client.aio.models.generate_content(
        model=model_name(),
        contents=RESEARCH_PROMPT.format(question=question),
        config=genai_types.GenerateContentConfig(
            tools=[genai_types.Tool(google_search=genai_types.GoogleSearch())],
            temperature=0.2,
        ),
    )
    return (response.text or "").strip(), sources_from(response)


async def write(client, question: str, notes: str, sources: list[dict]) -> Explanation:
    numbered = "\n".join(f"[{i}] {s['title']}" for i, s in enumerate(sources, 1)) or "(none)"
    response = await client.aio.models.generate_content(
        model=model_name(),
        contents=WRITER_PROMPT.format(question=question, notes=notes or "(none)", sources=numbered),
        config=genai_types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Explanation,
            temperature=0.4,
        ),
    )
    if isinstance(response.parsed, Explanation):
        return response.parsed
    return Explanation.model_validate_json(response.text)


async def explain(client, question: str) -> tuple[Explanation, list[dict]]:
    notes, sources = await research(client, question)
    return await write(client, question, notes, sources), sources
