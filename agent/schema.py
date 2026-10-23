"""The structured explanation the model returns, and the page renders.

Expert is the default answer: a detailed, multi-section briefing. "Explain it in a simpler way"
is offered as a follow-up and uses the same shape with fewer, simpler sections. (The key for
that level is still "eli5"; users never see it.)
Photos are chosen by id from the brand catalogue (agent/brand.py), so the schema only allows
those ids.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field

from .brand import ACCENT_IDS, DEFAULT_THEME, ICON_HELP, ICON_IDS, PHOTO_IDS, THEME_HELP, THEME_IDS

# key -> (short label, how the user asks for it, who it is written for, how much to write)
LEVELS = {
    "expert": ("Expert", "Explain it like I'm an expert",
               "a specialist reader. Precise terms, mechanisms, numbers, trade-offs, caveats and what is still open.",
               "4 or 5 sections, each with 2 or 3 substantial paragraphs; 3 or 4 key stats; 2 to 4 caveats; 4 to 6 glossary terms."),
    "eli5": ("Simpler", "Explain it in a simpler way",
             "a busy professional who is new to the topic. Plain English, short sentences, concrete everyday "
             "examples, no jargon (if a term is unavoidable, say what it means in a few words).",
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
    value: Optional[str] = Field(
        default=None, description="funnel: the count at this stage; timeline: the year or date; roadmap: the dates; "
                                  "pillars: a headline stat. Only values stated in the source.")


class Diagram(BaseModel):
    type: Literal["flow", "cycle", "parts", "compare", "funnel", "roadmap", "timeline", "staircase",
                  "pyramid", "matrix", "pillars"] = Field(
        description="flow = steps of a process in order; cycle = steps that loop back to the start; "
                    "parts = pieces of one whole; compare = two things side by side; "
                    "funnel = stages that narrow (pipeline, conversion), widest first; "
                    "roadmap = phases of a plan with dates; timeline = dated milestones; "
                    "staircase = maturity levels from lowest to highest; "
                    "pyramid = a hierarchy, top (most specific) first, foundation last; "
                    "matrix = exactly 4 quadrants: top-left, top-right, bottom-left, bottom-right; "
                    "pillars = 3 or 4 key messages side by side, each with a headline stat.")
    caption: str = Field(description="One sentence saying what the picture shows.")
    center: Optional[str] = Field(default=None, description="parts and cycle only: the whole thing, 1 to 3 words.")
    nodes: list[DiagramNode] = Field(description="3 to 6 nodes (compare: 2 to 4 per side).")
    left_title: Optional[str] = Field(default=None, description="compare only: left column title.")
    right_title: Optional[str] = Field(default=None, description="compare only: right column title.")
    x_axis: Optional[str] = Field(default=None, description="matrix only: what the horizontal axis measures, low to high.")
    y_axis: Optional[str] = Field(default=None, description="matrix only: what the vertical axis measures, low to high.")


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
    icon: Optional[Literal[ICON_IDS]] = Field(
        default=None, description="A brand line icon that fits the stat, if one does: " + ICON_HELP)
    emoji: Optional[str] = Field(default=None, description="One emoji that fits the stat, e.g. a globe for countries.")


class Section(BaseModel):
    heading: str = Field(description="A short heading, under 50 characters.")
    paragraphs: list[str] = Field(description="The section's text, one paragraph per item.")
    points: list[str] = Field(description="0 to 4 crisp key points for this section.")
    diagram: Optional[Diagram] = Field(
        default=None, description="A diagram where a picture explains this section better than words.")
    chart: Optional[Chart] = Field(
        default=None, description="A chart when this section turns on 3 or more comparable numbers stated in the source.")
    photo: Optional[PhotoId] = Field(default=None, description="A brand photo id that fits this section, or none.")
    emoji: Optional[str] = Field(default=None, description="One emoji that captures this section.")
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
    theme: Literal[THEME_IDS] = Field(
        default=DEFAULT_THEME, description="Always 'creative' (the user can switch to another theme later): " + THEME_HELP)
    accent: Literal[ACCENT_IDS] = Field(
        default="cobalt", description="Accent colour for the creative look: cobalt (calm, everyday), pacific (bright, "
                                      "digital), purple (future, innovation), magenta (bold, human, energetic).")
    cover_style: Literal["poster", "split", "mosaic"] = Field(
        default="poster", description="Cover layout: poster = one big photo; split = colour block beside a photo; "
                                      "mosaic = a grid of the cover photo and two section photos (needs 2 section photos).")
    emoji: Optional[str] = Field(default=None, description="One big emoji for the cover that sums up the topic.")
    hero_photo: PhotoId = Field(description="The brand photo id that best fits the whole topic, preferably one of "
                                            "the chosen theme's cover photos.")
    summary: str = Field(description="An executive summary paragraph of 3 to 5 sentences.")
    analogy: Optional[str] = Field(default=None, description="One everyday comparison that makes the idea click.")
    takeaways: list[str] = Field(description="3 or 4 key takeaways, one sentence each.")
    key_stats: list[Stat]
    sections: list[Section]
    caveats: list[str] = Field(description="Limits, debates and open questions.")
    glossary: list[Term]
    follow_ups: list[str] = Field(
        description="Exactly 3 follow-up questions on new angles, phrased as the user would ask them.")


# What the agent can make besides explanations, on the same brand.
# key -> (label, what it is, how much to write)
KINDS = {
    "poster": ("Poster", "a one-page poster for a wall, screen or intranet",
               "a punchy headline of up to 8 words, a tagline, 2 to 4 short points, the event details if any, one call to action. "
               "Very little text: a poster is read in seconds."),
    "email": ("Email", "an email the user will send",
              "a subject line, a one-line preview, a greeting, 2 to 4 short paragraphs (or 1 or 2 blocks with points), the details "
              "if any, a call to action and a sign-off. Clear and warm; match the tone the user asks for (formal by default)."),
    "social": ("Social post", "a LinkedIn-style social post",
               "a hook headline for the image, 2 to 4 short paragraphs (the first line must hook), 0 to 4 points, "
               "3 to 5 hashtags, an optional call to action."),
    "flyer": ("One-pager", "a one-page flyer, announcement, invitation, memo or factsheet",
              "a headline, a tagline, a short intro paragraph, 2 to 4 blocks (heading, 1 or 2 sentences, 0 to 3 points), "
              "the details if any, a call to action."),
}
KIND_IDS = tuple(KINDS)


class Detail(BaseModel):
    label: str = Field(description="e.g. 'Date', 'Where', 'Who', 'Deadline'.")
    value: str = Field(description="As the user gave it, or a [placeholder] like '[Date]' when they did not.")


class Block(BaseModel):
    heading: str = Field(description="Under 40 characters.")
    text: str = Field(description="1 or 2 sentences.")
    points: list[str] = Field(default_factory=list, description="0 to 3 short points.")
    emoji: Optional[str] = Field(default=None, description="One emoji for this block.")


class Creation(BaseModel):
    """A poster, email, social post or one-pager in the KPMG brand."""
    kind: Literal[KIND_IDS] = Field(description="poster, email, social (a LinkedIn-style post) or flyer (a one-pager, "
                                                "announcement, invitation, memo or factsheet).")
    title: str = Field(description="The headline (for an email, the headline in the email's banner).")
    tagline: str = Field(description="One line under the headline, under 90 characters.")
    subject: Optional[str] = Field(default=None, description="email only: the subject line, under 70 characters.")
    preheader: Optional[str] = Field(default=None, description="email only: the preview line, under 100 characters.")
    greeting: Optional[str] = Field(default=None, description="email only: e.g. 'Dear colleagues,'.")
    body: list[str] = Field(default_factory=list, description="The main text, one paragraph per item.")
    blocks: list[Block] = Field(default_factory=list, description="Short headed blocks (one-pager, longer emails).")
    points: list[str] = Field(default_factory=list, description="Key points, short.")
    details: list[Detail] = Field(default_factory=list, description="0 to 4 practical facts: date, time, place, who, deadline.")
    cta: Optional[str] = Field(default=None, description="The call to action, 2 to 6 words, e.g. 'Register by 14 November'.")
    sign_off: Optional[str] = Field(default=None, description="email only: e.g. 'Kind regards,\\n[Your name]'.")
    hashtags: list[str] = Field(default_factory=list, description="social only: 3 to 5 hashtags without the # sign.")
    theme: Literal[THEME_IDS] = Field(default=DEFAULT_THEME, description="Always 'creative' (the user can switch later).")
    accent: Literal[ACCENT_IDS] = Field(
        default="cobalt", description="Accent colour: cobalt (calm, everyday), pacific (bright, digital), "
                                      "purple (future, innovation), magenta (bold, human, celebration).")
    emoji: Optional[str] = Field(default=None, description="One big emoji that sums it up.")
    hero_photo: PhotoId = Field(description="The brand photo id that best fits.")
    ideas: list[str] = Field(description="Exactly 3 quick changes the user might want next, phrased as they would ask, "
                                         "under 40 characters, e.g. 'Make it more formal'.")
