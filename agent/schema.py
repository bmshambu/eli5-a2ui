"""The structured explanation the writer model returns, and the page renders.

Kept flat and small on purpose: it is passed to Gemini as response_schema, and every field
maps to one thing on the explainer page.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

LEVELS = (("eli5", "ELI5"), ("eli10", "ELI10"), ("eli15", "ELI15"), ("expert", "Expert"))


class Level(BaseModel):
    analogy: str = Field(description="One everyday comparison for this audience, one sentence.")
    body: str = Field(description="2 to 5 short sentences. Cite sources inline as [1], [2].")


class DiagramNode(BaseModel):
    label: str = Field(description="2 to 4 words.")
    note: str = Field(description="One short line, under 60 characters.")
    side: Optional[Literal["left", "right"]] = Field(
        default=None, description="Only for type 'compare': which column this node belongs to.")


class Diagram(BaseModel):
    type: Literal["flow", "parts", "compare"] = Field(
        description="flow = steps in order; parts = pieces of one whole; compare = two things side by side.")
    caption: str = Field(description="One sentence saying what the picture shows.")
    nodes: list[DiagramNode] = Field(description="3 to 6 nodes (compare: 2 to 4 per side).")
    left_title: Optional[str] = Field(default=None, description="compare only: left column title.")
    right_title: Optional[str] = Field(default=None, description="compare only: right column title.")


class Explanation(BaseModel):
    title: str = Field(description="The topic as a short question or noun phrase.")
    one_liner: str = Field(description="The whole answer in one plain sentence, under 25 words.")
    tags: list[str] = Field(description="2 or 3 one-word subject tags, e.g. Physics.")
    confidence: Literal["high", "medium", "low"] = Field(
        description="high = settled and well sourced; medium = mostly agreed; low = contested or thin sources.")
    eli5: Level
    eli10: Level
    eli15: Level
    expert: Level
    diagram: Diagram
    follow_ups: list[str] = Field(
        description="Exactly 3 follow-up questions, phrased as the user would ask them.")
