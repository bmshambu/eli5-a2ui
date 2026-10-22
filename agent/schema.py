"""The structured explanation the model returns for one level, and the page renders.

One level per reply keeps generation fast: ELI5 first, deeper levels only when asked.
Kept flat and small: it is passed to Gemini as response_schema, and every field maps to
one thing on the explainer page.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

# key, tab label, how the user asks for it (shown as their turn in GE), who it is written for
LEVELS = {
    "eli5": ("ELI5", "Explain it like I'm 5", "a curious 5-year-old. Short words, one concrete everyday image, no jargon at all."),
    "eli10": ("ELI10", "Explain it like I'm 10", "a 10-year-old. Simple cause and effect, and one new word explained."),
    "eli15": ("ELI15", "Explain it like I'm 15", "a high-school student. The real mechanism with the proper terms."),
    "expert": ("Expert", "Explain it like I'm an expert", "a specialist. Precise terms, numbers, caveats and what is still open."),
}
LEVEL_KEYS = tuple(LEVELS)


class DiagramNode(BaseModel):
    emoji: str = Field(description="One emoji that pictures this node.")
    label: str = Field(description="2 to 4 words.")
    note: str = Field(description="One short line, under 60 characters.")
    side: Optional[Literal["left", "right"]] = Field(
        default=None, description="Only for type 'compare': which column this node belongs to.")


class Diagram(BaseModel):
    type: Literal["flow", "cycle", "parts", "compare"] = Field(
        description="flow = steps in order; cycle = steps that loop back to the start; "
                    "parts = pieces of one whole; compare = two things side by side.")
    caption: str = Field(description="One sentence saying what the picture shows.")
    center: Optional[str] = Field(default=None, description="parts and cycle only: the whole thing, 1 to 3 words.")
    nodes: list[DiagramNode] = Field(description="3 to 5 nodes (compare: 2 to 3 per side).")
    left_title: Optional[str] = Field(default=None, description="compare only: left column title.")
    right_title: Optional[str] = Field(default=None, description="compare only: right column title.")


class KeyFact(BaseModel):
    value: str = Field(description="A short striking number or word, e.g. '4x' or '150 million km'.")
    label: str = Field(description="What the value means, under 60 characters.")


class Explanation(BaseModel):
    title: str = Field(description="The topic as a short question or noun phrase.")
    one_liner: str = Field(description="The whole answer in one plain sentence, under 25 words.")
    tags: list[str] = Field(description="2 or 3 one-word subject tags, e.g. Physics.")
    confidence: Literal["high", "medium", "low"] = Field(
        description="How settled the answer is: high = settled science or fact; medium = mostly agreed; "
                    "low = contested or unknown.")
    analogy: str = Field(description="One everyday comparison for this audience, one sentence.")
    body: str = Field(description="3 to 5 short sentences for this audience.")
    key_fact: Optional[KeyFact] = Field(default=None, description="One memorable fact, if there is a good one.")
    diagram: Diagram
    follow_ups: list[str] = Field(
        description="Exactly 3 follow-up questions on new angles, phrased as the user would ask them.")
