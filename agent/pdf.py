"""The explanation as a KPMG-branded A4 PDF, built on the server.

GE's chat frame blocks printing and downloads, so the page can't save itself. Instead the
"Download PDF" button under the frame asks the agent, which builds this PDF from the same
Explanation and sends it back as a file in chat. Pure Python (reportlab), so it runs on
Agent Engine with no system libraries.
"""
import base64
import io
import re
from xml.sax.saxutils import escape

from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.charts.doughnut import Doughnut
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from . import brand
from .charts import fmt
from .schema import LEVELS, Chart, Diagram, Explanation

MAX_PHOTOS = 2  # section banners, besides the cover; keeps the file well under GE's ~1 MB part limit
W, H = A4
MARGIN = 18 * mm
COVER_H = 105 * mm
BODY_W = W - 2 * MARGIN

BLUE, COBALT, DARK = colors.HexColor(brand.KPMG_BLUE), colors.HexColor(brand.COBALT), colors.HexColor(brand.DARK_BLUE)
PACIFIC, PURPLE = colors.HexColor(brand.PACIFIC), colors.HexColor(brand.PURPLE)
MUTED, LINE, TINT = colors.HexColor("#666666"), colors.HexColor("#E5E5E5"), colors.HexColor("#F3F6FF")
SERIES = (BLUE, PACIFIC, PURPLE, COBALT, colors.HexColor(brand.LIGHT_PURPLE))
# Cover per KPMG theme (brand/extract/08-themes): overlay colour and strength, eyebrow colour,
# and the colour of the title's last words. Inner pages stay white in every theme so they print.
COVERS = {
    "corporate": (BLUE, 0.78, colors.white, colors.HexColor(brand.PALE_BLUE)),
    "ai": (COBALT, 0.82, PACIFIC, PACIFIC),
    "ai-platform": (colors.HexColor("#050B2E"), 0.84, PACIFIC, PACIFIC),
    "finance-data": (COBALT, 0.82, colors.white, colors.white),
}
LEGAL = '© 2026 KPMG International Cooperative ("KPMG International"), a Swiss entity. All rights reserved.'

# Liberation Sans: Arial-metric like the brand's Arial fallback, and unlike the built-in
# Helvetica it has Greek, superscripts and symbols. Subsets are embedded, so files stay small.
for _name, _file in (("Sans", "LiberationSans-Regular.ttf"), ("Sans-Bold", "LiberationSans-Bold.ttf")):
    pdfmetrics.registerFont(TTFont(_name, str(brand.ASSETS / "fonts" / _file)))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans", boldItalic="Sans-Bold")

_S = {
    "body": ParagraphStyle("body", fontName="Sans", fontSize=10.5, leading=15, textColor=DARK, spaceAfter=6),
    "small": ParagraphStyle("small", fontName="Sans", fontSize=9, leading=12, textColor=MUTED),
    "label": ParagraphStyle("label", fontName="Sans-Bold", fontSize=9, leading=12, textColor=COBALT,
                            spaceBefore=12, spaceAfter=6, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="Sans-Bold", fontSize=17, leading=21, textColor=BLUE,
                         spaceBefore=14, spaceAfter=6),
    "h4": ParagraphStyle("h4", fontName="Sans-Bold", fontSize=11, leading=14, textColor=BLUE, spaceAfter=4),
    "bullet": ParagraphStyle("bullet", fontName="Sans", fontSize=10.5, leading=15, textColor=DARK,
                             leftIndent=12, bulletIndent=0, spaceAfter=3,
                             bulletFontName="Sans-Bold", bulletFontSize=7, bulletOffsetY=-1),
    "kv": ParagraphStyle("kv", fontName="Sans-Bold", fontSize=18, leading=22, textColor=BLUE),
    "kl": ParagraphStyle("kl", fontName="Sans", fontSize=9, leading=12, textColor=DARK),
    "node": ParagraphStyle("node", fontName="Sans", fontSize=9.5, leading=13, textColor=DARK),
    "num": ParagraphStyle("num", fontName="Sans-Bold", fontSize=10, leading=12, textColor=colors.white,
                          alignment=TA_CENTER),
    "eyebrow": ParagraphStyle("eyebrow", fontName="Sans-Bold", fontSize=10, leading=13, textColor=colors.white),
    "title": ParagraphStyle("title", fontName="Sans-Bold", fontSize=26, leading=30, textColor=colors.white),
    "lede": ParagraphStyle("lede", fontName="Sans", fontSize=12, leading=16, textColor=colors.white),
}


_QUOTE = {'"': "&quot;"}


# Emoji, variation selectors and joiners: the embedded font has no colour emoji, so they are dropped.
_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D]")


def _x(text) -> str:
    return escape(_EMOJI.sub("", str(text or "")).strip())


def _p(text, style="body") -> Paragraph:
    return Paragraph(_x(text), _S[style])


def _photo_bytes(photo_id: str) -> io.BytesIO:
    return io.BytesIO(base64.b64decode(brand.photo_uri(photo_id).split(",", 1)[1]))


def _photo(photo_id: str) -> ImageReader:
    return ImageReader(_photo_bytes(photo_id))


def filename(title: str) -> str:
    return (re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-")[:60] or "explainer") + ".pdf"


def _bullets(items) -> list:
    return [Paragraph(_x(t), _S["bullet"], bulletText="■") for t in items]


def _label(text: str) -> Paragraph:
    return _p(text.upper(), "label")


def _kpis(stats):
    stats = stats[:4]
    if not stats:
        return None
    tiles = [[_p(s.value, "kv"), _p(s.label, "kl")] for s in stats]
    t = Table([tiles], colWidths=[BODY_W / len(stats)] * len(stats))
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), TINT),
             ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 8),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]
    style += [("LINEBEFORE", (i, 0), (i, 0), 3, SERIES[i % 4]) for i in range(len(stats))]
    t.setStyle(TableStyle(style))
    return t


def _num(i: int, colour=BLUE) -> Table:
    t = Table([[_p(f"{i:02d}", "num")]], colWidths=[9 * mm], rowHeights=[7 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colour), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    return t


def _node(n) -> Paragraph:
    value = f' <font color="{brand.COBALT}"><b>{_x(n.value)}</b></font>' if n.value else ""
    return Paragraph(f"<b>{_x(n.label)}</b>{value}<br/>{_x(n.note)}", _S["node"])


def _boxed(t: Table, extra=()) -> Table:
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 6),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5), *extra]))
    return t


def diagram(d: Diagram | None) -> list:
    """The diagram as a numbered table: the same content as the page, laid out for print."""
    if d is None or not d.nodes:
        return []
    if d.type == "compare":
        left = [n for n in d.nodes if n.side != "right"]
        right = [n for n in d.nodes if n.side == "right"]
        rows = [[_p(d.left_title or "", "h4"), _p(d.right_title or "", "h4")]]
        rows += [[_node(left[i]) if i < len(left) else "", _node(right[i]) if i < len(right) else ""]
                 for i in range(max(len(left), len(right)))]
        body = _boxed(Table(rows, colWidths=[BODY_W / 2] * 2),
                      [("LINEBELOW", (0, 0), (-1, 0), 2, BLUE), ("BACKGROUND", (0, 1), (-1, -1), TINT),
                       ("LINEAFTER", (0, 0), (0, -1), 0.5, LINE)])
    elif d.type == "matrix" and len(d.nodes) >= 4:
        body = _boxed(Table([[_node(d.nodes[0]), _node(d.nodes[1])], [_node(d.nodes[2]), _node(d.nodes[3])]],
                            colWidths=[BODY_W / 2] * 2),
                      [("GRID", (0, 0), (-1, -1), 1, colors.white), ("BACKGROUND", (0, 0), (0, 0), TINT),
                       ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#E9EDFC")),
                       ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#E9EDFC")),
                       ("BACKGROUND", (1, 1), (1, 1), TINT)])
        axes = " · ".join(x for x in (f"Across: {d.x_axis}" if d.x_axis else "", f"Up: {d.y_axis}" if d.y_axis else "") if x)
        body = [body, _p(axes, "small")] if axes else body
    else:
        rows = [[_num(i, SERIES[(i - 1) % 4]), _node(n)] for i, n in enumerate(d.nodes, 1)]
        if d.center:
            rows.insert(0, ["", _p(d.center, "h4")])
        body = _boxed(Table(rows, colWidths=[12 * mm, BODY_W - 12 * mm]),
                      [("LINEBELOW", (1, 0), (1, -2), 0.5, LINE)])
    parts = body if isinstance(body, list) else [body]
    return [KeepTogether([Spacer(1, 4), *parts, _p(d.caption, "small"), Spacer(1, 6)])]


def _legend(drawing: Drawing, names, y: float) -> None:
    x = 0
    for i, name in enumerate(names):
        drawing.add(Rect(x, y, 8, 8, fillColor=SERIES[i % 5], strokeColor=None))
        drawing.add(String(x + 11, y + 1, name, fontName="Sans", fontSize=8, fillColor=DARK))
        x += 20 + len(name) * 4.5


def chart(c: Chart | None) -> list:
    """Bar, line or donut, drawn as vector graphics from the numbers in the Chart."""
    if c is None or not c.labels:
        return []
    n = len(c.labels)
    series = [s for s in c.series if len(s.values) >= n][:5]
    if not series:
        return []
    data = [tuple(s.values[:n]) for s in series]
    label = lambda v: fmt(v, c.unit)  # noqa: E731
    if c.type == "donut":
        d = Drawing(BODY_W, 150)
        pie = Doughnut()
        pie.x, pie.y, pie.width, pie.height = 0, 5, 140, 140
        pie.data = [max(v, 0) for v in data[0]]
        pie.innerRadiusFraction = 0.55
        pie.slices.strokeColor = colors.white
        for i in range(n):
            pie.slices[i].fillColor = SERIES[i % 5]
        d.add(pie)
        total = sum(pie.data) or 1
        for i, (lab, v) in enumerate(zip(c.labels, pie.data)):
            y = 130 - i * 16
            shown = label(v) if c.unit == "%" else f"{label(v)} · {v / total:.0%}"
            d.add(Rect(160, y, 9, 9, fillColor=SERIES[i % 5], strokeColor=None))
            d.add(String(174, y + 1, f"{lab}: {shown}", fontName="Sans", fontSize=9, fillColor=DARK))
    elif c.type == "line":
        d = Drawing(BODY_W, 170)
        lc = HorizontalLineChart()
        lc.x, lc.y, lc.width, lc.height = 40, 28, BODY_W - 50, 120
        lc.data = data
        lc.categoryAxis.categoryNames = list(c.labels)
        lc.categoryAxis.labels.fontName = lc.valueAxis.labels.fontName = "Sans"
        lc.categoryAxis.labels.fontSize = lc.valueAxis.labels.fontSize = 8
        lc.valueAxis.valueMin = min(0, *(v for row in data for v in row))
        lc.valueAxis.labelTextFormat = label
        lc.valueAxis.visibleGrid, lc.valueAxis.gridStrokeColor = True, LINE
        for i in range(len(data)):
            lc.lines[i].strokeColor, lc.lines[i].strokeWidth = SERIES[i], 2
        if len(data) == 1:
            lc.lineLabelFormat = label
            lc.lineLabels.fontName, lc.lineLabels.fontSize, lc.lineLabels.dy = "Sans-Bold", 8, 6
        d.add(lc)
        if len(series) > 1:
            _legend(d, [s.name for s in series], 158)
    else:
        rows = n * len(data)
        d = Drawing(BODY_W, 30 + rows * 16)
        bc = HorizontalBarChart()
        bc.x, bc.y, bc.width, bc.height = 110, 10, BODY_W - 170, rows * 16
        bc.data = data
        bc.categoryAxis.categoryNames = list(c.labels)
        bc.categoryAxis.reverseDirection = True
        bc.categoryAxis.labels.fontName = "Sans"
        bc.categoryAxis.labels.fontSize = 8.5
        bc.categoryAxis.labels.boxAnchor = "e"
        bc.valueAxis.visible = False
        bc.valueAxis.valueMin = min(0, *(v for row in data for v in row))
        bc.barLabelFormat = label
        bc.barLabels.fontName, bc.barLabels.fontSize, bc.barLabels.boxAnchor, bc.barLabels.dx = "Sans-Bold", 8, "w", 3
        bc.barSpacing, bc.groupSpacing = 1, 6
        for i in range(len(data)):
            bc.bars[i].fillColor, bc.bars[i].strokeColor = SERIES[i], None
        d.add(bc)
        if len(series) > 1:
            d.height += 14
            _legend(d, [s.name for s in series], d.height - 10)
    src = [_p(f"Source: {c.source}", "small")] if c.source else []
    return [KeepTogether([Spacer(1, 4), _p(c.title, "h4"), d, _p(c.caption, "small"), *src, Spacer(1, 6)])]


def _story(e: Explanation, sources: list[dict], documents) -> list:
    story = [NextPageTemplate("body")]
    # Finance Data shows its first three figures on the cover.
    kpis = _kpis(e.key_stats[3:] if e.theme == "finance-data" else e.key_stats)
    if kpis:
        story += [kpis, Spacer(1, 6)]
    story += [_label("At a glance"), _p(e.summary)]
    if e.analogy:
        box = Table([[Paragraph(f"<b>Think of it like</b><br/>{_x(e.analogy)}", _S["body"])]], colWidths=[BODY_W])
        story.append(_boxed(box, [("BACKGROUND", (0, 0), (-1, -1), TINT), ("LINEBEFORE", (0, 0), (0, 0), 3, COBALT),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 10)]))
    story += _bullets(e.takeaways)
    used = {e.hero_photo}
    h2 = ParagraphStyle("h2t", parent=_S["h2"], textColor=COBALT) if e.theme == "finance-data" else _S["h2"]
    for i, s in enumerate(e.sections, 1):
        head = [Paragraph(f'<font color="{brand.COBALT}">{i:02d}</font>  {_x(s.heading)}', h2)]
        if s.doc_ref:
            head.append(_p(f"From the document: {s.doc_ref}", "small"))
        if s.photo and s.photo not in used and len(used) <= MAX_PHOTOS:
            used.add(s.photo)
            img = Image(_photo_bytes(s.photo), width=BODY_W, height=BODY_W * 0.4)
            head += [Spacer(1, 4), img, Spacer(1, 6)]
        paras = [_p(p) for p in s.paragraphs]
        story.append(KeepTogether(head + paras[:1]))
        story += paras[1:] + chart(s.chart) + diagram(s.diagram) + _bullets(s.points[:4])
    if e.caveats:
        story += [_label("Caveats and open questions"), *_bullets(e.caveats)]
    if e.glossary:
        rows = [[_p("Term", "h4"), _p("Meaning", "h4")]] + [[Paragraph(f"<b>{_x(t.term)}</b>", _S["node"]),
                                                               _p(t.definition, "node")] for t in e.glossary]
        story += [_label("Glossary"), _boxed(Table(rows, colWidths=[45 * mm, BODY_W - 45 * mm], repeatRows=1),
                                             [("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE)])]
    if documents:
        story += [_label("Based on your document"), *_bullets(documents),
                  _p("Explained from the document only, without web search.", "small")]
    if sources:
        story.append(_label("Sources"))
        story += [Paragraph(f'{i}. <link href="{escape(s["uri"], _QUOTE)}" color="{brand.COBALT}">{_x(s["title"])}</link>',
                            _S["node"]) for i, s in enumerate(sources, 1)]
    return story


def _cover_stats(canvas, stats, y: float) -> None:
    """Up to three headline figures on the Finance Data cover, each under a Pacific Blue rule."""
    w = BODY_W * 0.9 / 3
    for i, s in enumerate(stats):
        x = MARGIN + i * w
        canvas.setStrokeColor(PACIFIC)
        canvas.setLineWidth(2)
        canvas.line(x, y, x + w - 6 * mm, y)
        canvas.setFillColor(colors.white)
        canvas.setFont("Sans-Bold", 18)
        canvas.drawString(x, y - 8 * mm, s.value[:14])
        label = Paragraph(_x(s.label), ParagraphStyle("cl", parent=_S["small"], textColor=colors.HexColor(brand.PALE_BLUE)))
        _, h = label.wrap(w - 6 * mm, 20 * mm)
        label.drawOn(canvas, x, y - 10 * mm - h)


def build(e: Explanation, sources: list[dict], level: str = "expert", documents=()) -> bytes:
    """The PDF bytes for one explanation."""
    buf = io.BytesIO()
    eyebrow = f'{"Document explained" if documents else "Explained"} · {LEVELS[level][0]}'

    def cover(canvas, _doc):
        canvas.saveState()
        top = H - COVER_H
        canvas.drawImage(_photo(e.hero_photo), (W - COVER_H * 2.5) / 2, top, COVER_H * 2.5, COVER_H)  # 5:2 crops, centred
        if e.theme == "creative":  # the topic's accent colour
            a1, _, _, ah = brand.ACCENTS.get(e.accent, brand.ACCENTS["cobalt"])
            wash, alpha, eyebrow_colour, hl = colors.HexColor(a1), 0.8, colors.HexColor(ah), colors.HexColor(ah)
        else:
            wash, alpha, eyebrow_colour, hl = COVERS.get(e.theme, COVERS["corporate"])
        canvas.setFillColor(wash)
        canvas.setFillAlpha(alpha)
        canvas.rect(0, top, W, COVER_H, stroke=0, fill=1)
        canvas.setFillAlpha(1)
        canvas.drawImage(ImageReader(str(brand.ASSETS / "kpmg-logo-white.png")), MARGIN, H - 22 * mm,
                         width=26 * mm, height=10.2 * mm, mask="auto")
        y = H - 34 * mm
        words = e.title.split()
        k = 0 if len(words) < 3 else 2 if len(words) > 4 else 1
        title = _x(" ".join(words[:len(words) - k]))
        if k:
            title += f' <font color="{hl.hexval().replace("0x", "#")}">{_x(" ".join(words[-k:]))}</font>'
        eb = ParagraphStyle("eb", parent=_S["eyebrow"], textColor=eyebrow_colour)
        for para in (Paragraph(_x(eyebrow.upper()), eb), Paragraph(title, _S["title"]), Paragraph(_x(e.one_liner), _S["lede"])):
            _, h = para.wrap(BODY_W * 0.9, COVER_H)
            y -= h
            para.drawOn(canvas, MARGIN, y)
            y -= 4 * mm
        if e.theme == "finance-data":
            _cover_stats(canvas, e.key_stats[:3], y)
        _footer(canvas)
        canvas.restoreState()

    def body(canvas, _doc):
        canvas.saveState()
        canvas.drawImage(ImageReader(str(brand.ASSETS / "kpmg-logo-blue.png")), MARGIN, H - 13 * mm,
                         width=15 * mm, height=5.9 * mm, mask="auto")
        canvas.setFont("Sans", 8)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(W - MARGIN, H - 11 * mm, e.title[:90])
        canvas.setStrokeColor(LINE)
        canvas.line(MARGIN, H - 15 * mm, W - MARGIN, H - 15 * mm)
        _footer(canvas)
        canvas.restoreState()

    def _footer(canvas):
        canvas.setFont("Sans", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, 10 * mm, LEGAL)
        canvas.drawRightString(W - MARGIN, 10 * mm, f"KPMG. Make the Difference.   {canvas.getPageNumber()}")

    doc = BaseDocTemplate(buf, pagesize=A4, title=e.title, author="KPMG", subject=e.one_liner,
                          leftMargin=MARGIN, rightMargin=MARGIN, topMargin=20 * mm, bottomMargin=18 * mm)
    first = Frame(MARGIN, 18 * mm, BODY_W, H - COVER_H - 26 * mm, id="first")
    rest = Frame(MARGIN, 18 * mm, BODY_W, H - 38 * mm, id="rest")
    doc.addPageTemplates([PageTemplate("cover", [first], onPage=cover), PageTemplate("body", [rest], onPage=body)])
    doc.build(_story(e, sources, list(documents)))
    return buf.getvalue()
