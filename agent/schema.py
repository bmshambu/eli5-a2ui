"""The structured explanation the model returns, and the page renders.

Expert is the default answer: a detailed, multi-section briefing. "Explain it like I'm 5" is
offered as a follow-up and uses the same shape with fewer, simpler sections.
Photos are chosen by id from the brand catalogue (agent/brand.py), so the schema only allows
those ids.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

from .brand import PHOTO_IDS

# key -> (short label, how the user asks for it, who it is written for, how much to write)
LEVELS = {
    "expert": ("Expert", "Explain it like I'm an expert",
               "a specialist reader. Precise terms, mechanisms, numbers, trade-offs, caveats and what is still open.",
               "4 or 5 sections, each with 2 or 3 substantial paragraphs; 3 or 4 key stats; 2 to 4 caveats; 4 to 6 glossary terms."),
    "eli5": ("ELI5", "Explain it like I'm 5",
             "a curious 5-year-old. Short words, concrete everyday images, no jargon at all.",
             "2 or 3 short sections of 1 or 2 short paragraphs; 2 key stats; no caveats; no glossary."),
}
LEVEL_KEYS = tuple(LEVELS)
DEFAULT_LEVEL = "expert"

PhotoId = Literal[PHOTO_IDS]


class DiagramNode(BaseModel):
    label: str = Field(description="2 to 4 words.")
    note: str = Field(description="One short line, under 70 characters.")
    side: Optional[Literal["left", "right"]] = Field(
        default=None, description="Only for type 'compare': which column this node belongs to.")


class Diagram(BaseModel):
    type: Literal["flow", "cycle", "parts", "compare"] = Field(
        description="flow = steps in order; cycle = steps that loop back to the start; "
                    "parts = pieces of one whole; compare = two things side by side.")
    caption: str = Field(description="One sentence saying what the picture shows.")
    center: Optional[str] = Field(default=None, description="parts and cycle only: the whole thing, 1 to 3 words.")
    nodes: list[DiagramNode] = Field(description="3 to 6 nodes (compare: 2 to 4 per side).")
    left_title: Optional[str] = Field(default=None, description="compare only: left column title.")
    right_title: Optional[str] = Field(default=None, description="compare only: right column title.")


class Series(BaseModel):
    name: str = Field(description="What this series measures, e.g. 'Revenue' or '2025'.")
    values: list[float] = Field(description="One value per label, in the same order.")


class Chart(BaseModel):
    type: Literal["bar", "line", "donut"] = Field(
        description="bar = compare amounts across categories; line = change over time; donut = shares of one total.")
    title: str = Field(description="What the chart shows, under 60 characters.")
    unit: Optional[str] = Field(default=None, description="Unit for every value, e.g. '%', '£m', 'bn', 'people'.")
    labels: list[str] = Field(description="Category names or time points, 2 to 8, short.")
    series: list[Series] = Field(description="1 to 3 series (donut: exactly 1).")
    caption: str = Field(description="One sentence: the takeaway of the chart.")
    source: Optional[str] = Field(default=None, description="Where the numbers come from, e.g. 'Table 2, p. 7'.")


class Stat(BaseModel):
    value: str = Field(description="A short striking number, e.g. '4x', '1.5 C' or '150 million km'.")
    label: str = Field(description="What the value means, under 60 characters.")


class Section(BaseModel):
    heading: str = Field(description="A short heading, under 50 characters.")
    paragraphs: list[str] = Field(description="The section's text, one paragraph per item.")
    points: list[str] = Field(description="0 to 4 crisp key points for this section.")
    diagram: Optional[Diagram] = Field(
        default=None, description="A diagram where a picture explains this section better than words.")
    chart: Optional[Chart] = Field(
        default=None, description="A chart when this section turns on 3 or more comparable numbers stated in the source.")
    photo: Optional[PhotoId] = Field(default=None, description="A brand photo id that fits this section, or none.")
    doc_ref: Optional[str] = Field(
        default=None, description="When explaining a document: where this comes from in it, e.g. 'Section 3' or 'Slides 4-6'.")


class Term(BaseModel):
    term: str
    definition: str = Field(description="One sentence.")


class Explanation(BaseModel):
    title: str = Field(description="The topic as a short question or noun phrase.")
    one_liner: str = Field(description="The whole answer in one plain sentence, under 30 words.")
    tags: list[str] = Field(description="2 or 3 one-word subject tags, e.g. Physics.")
    confidence: Literal["high", "medium", "low"] = Field(
        description="How settled the answer is: high = settled science or fact; medium = mostly agreed; "
                    "low = contested or unknown.")
    hero_photo: PhotoId = Field(description="The brand photo id that best fits the whole topic.")
    summary: str = Field(description="An executive summary paragraph of 3 to 5 sentences.")
    analogy: Optional[str] = Field(default=None, description="One everyday comparison that makes the idea click.")
    takeaways: list[str] = Field(description="3 or 4 key takeaways, one sentence each.")
    key_stats: list[Stat]
    sections: list[Section]
    caveats: list[str] = Field(description="Limits, debates and open questions.")
    glossary: list[Term]
    follow_ups: list[str] = Field(
        description="Exactly 3 follow-up questions on new angles, phrased as the user would ask them.")
