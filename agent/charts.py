"""Charts for the numbers in a section: bar, line and donut, in the KPMG palette.

Bars and labels are HTML, so text keeps its 14px minimum at any panel width; only the line
and the donut rings are SVG. Values come from the model's Chart, which may only use numbers
stated in the document or the sources (llm.py says so); nothing here estimates anything.
"""
import html
import math

from .schema import Chart

SERIES = ("var(--c0)", "var(--c2)", "var(--c3)", "var(--c1)", "var(--c4)")
_PREFIX = ("£", "$", "€", "¥", "₹")

CSS = """
.chart{margin:8px 0 10px;border:1px solid var(--line);background:var(--bg);padding:14px 14px 10px}
.chart h4{margin:0 0 10px;font-size:15px;color:var(--brand)}
.chart .src{font-size:14px;color:var(--muted);margin-top:6px}
.legend-row{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:14px;color:var(--ink);margin-bottom:8px}
.legend-row i{display:inline-block;width:12px;height:12px;margin-right:6px;vertical-align:-1px;background:var(--s)}
.bars{display:grid;grid-template-columns:minmax(80px,32%) 1fr;gap:8px 10px;align-items:center}
.bars .lab{font-size:14px;color:var(--ink);line-height:1.3}
.bars .grp{display:flex;flex-direction:column;gap:3px}
.bars .bar{display:flex;align-items:center;gap:6px;font-size:14px;font-weight:700;color:var(--ink)}
.bars .fill{height:18px;background:var(--s);min-width:2px;transform-origin:left;animation:grow .6s ease-out both}
@keyframes grow{from{transform:scaleX(0)}}
.line{position:relative;height:200px;margin:6px 0 4px 0;border-left:1px solid var(--line);border-bottom:1px solid var(--line)}
.line svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
.line polyline{fill:none;stroke-width:3;vector-effect:non-scaling-stroke;stroke-linejoin:round}
.line .pt{stroke-width:9;stroke-linecap:round;vector-effect:non-scaling-stroke}
.line .val{position:absolute;transform:translate(-50%,-130%);font-size:14px;font-weight:700;color:var(--ink);white-space:nowrap}
.line .y{position:absolute;left:4px;font-size:14px;color:var(--muted)}
.xlabs{position:relative;height:22px;font-size:14px;color:var(--muted)}
.xlabs span{position:absolute;transform:translateX(-50%);white-space:nowrap}
.donut{display:flex;flex-wrap:wrap;gap:16px;align-items:center}
.donut svg{width:170px;height:170px;flex:0 0 auto}
.donut circle{fill:none;stroke-width:22}
.donut .tot{font-size:14px;font-weight:700;fill:var(--brand)}
.donut ul{list-style:none;margin:0;padding:0;font-size:14px;flex:1 1 180px}
.donut li{display:flex;gap:8px;align-items:baseline;padding:4px 0;border-bottom:1px solid var(--line)}
.donut li i{width:12px;height:12px;background:var(--s);flex:0 0 auto}.donut li b{margin-left:auto;color:var(--brand)}
@media (prefers-reduced-motion:reduce){.bars .fill{animation:none}}
"""


def _e(text) -> str:
    return html.escape(str(text or ""), quote=True)


def fmt(v: float, unit: str | None = None) -> str:
    """1234.5 -> '1,234.5'; with unit '%' -> '12%', '£m' -> '£12m', 'people' -> '12 people'."""
    num = f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}".rstrip("0").rstrip(".")
    unit = (unit or "").strip()
    if not unit:
        return num
    if unit.startswith(_PREFIX):
        return f"{unit[0]}{num}{unit[1:]}"
    return f"{num}{unit}" if unit in ("%", "x", "pp", "bn", "m", "k") else f"{num} {unit}"


def _series(c: Chart) -> list[tuple[str, list[float]]]:
    """Series trimmed to the labels; series with missing values are dropped."""
    n = len(c.labels)
    return [(s.name, s.values[:n]) for s in c.series if len(s.values) >= n][:5]


def _legend(series) -> str:
    if len(series) < 2:
        return ""
    return '<div class="legend-row">' + "".join(
        f'<span><i style="--s:{SERIES[i]}"></i>{_e(name)}</span>' for i, (name, _) in enumerate(series)) + "</div>"


def _bars(c: Chart, series) -> str:
    top = max((abs(v) for _, vals in series for v in vals), default=0) or 1
    rows = []
    for j, label in enumerate(c.labels):
        bars = "".join(
            f'<div class="bar"><span class="fill" style="--s:{SERIES[i]};width:{max(abs(vals[j]) / top * 82, 0.5):.1f}%"></span>'
            f"{_e(fmt(vals[j], c.unit))}</div>" for i, (_, vals) in enumerate(series))
        rows.append(f'<span class="lab">{_e(label)}</span><div class="grp">{bars}</div>')
    return _legend(series) + f'<div class="bars">{"".join(rows)}</div>'


def _line(c: Chart, series) -> str:
    vals_all = [v for _, vals in series for v in vals]
    lo, hi = min(0, min(vals_all)), max(vals_all)
    span = (hi - lo) or 1
    n = len(c.labels)
    x = lambda j: 50 if n == 1 else 8 + j / (n - 1) * 84  # noqa: E731  (inset so edge labels fit)
    y = lambda v: 100 - (v - lo) / span * 88  # noqa: E731  (headroom for value labels)
    svg, labels = [], []
    for i, (_, vals) in enumerate(series):
        pts = " ".join(f"{x(j):.2f},{y(v):.2f}" for j, v in enumerate(vals))
        svg.append(f'<polyline points="{pts}" stroke="{SERIES[i]}"/>')
        svg.extend(f'<line class="pt" x1="{x(j):.2f}" y1="{y(v):.2f}" x2="{x(j):.2f}" y2="{y(v):.2f}" stroke="{SERIES[i]}"/>'
                   for j, v in enumerate(vals))
        if len(series) == 1 and n <= 8:
            labels.extend(f'<span class="val" style="left:{x(j):.1f}%;top:{y(v):.1f}%">{_e(fmt(v, c.unit))}</span>'
                          for j, v in enumerate(vals))
    ylabs = f'<span class="y" style="top:2px">{_e(fmt(hi, c.unit))}</span>' if len(series) > 1 or n > 8 else ""
    xl = "".join(f'<span style="left:{x(j):.1f}%">{_e(lab)}</span>' for j, lab in enumerate(c.labels))
    return (_legend(series) + f'<div class="line"><svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">'
            f'{"".join(svg)}</svg>{"".join(labels)}{ylabs}</div><div class="xlabs">{xl}</div>')


def _donut(c: Chart, series) -> str:
    vals = [max(v, 0) for v in series[0][1]]
    total = sum(vals) or 1
    r, circ, start, rings, items = 60, 2 * math.pi * 60, 0.0, [], []
    for j, (label, v) in enumerate(zip(c.labels, vals)):
        share = v / total
        colour = SERIES[j % len(SERIES)]
        rings.append(f'<circle r="{r}" cx="85" cy="85" stroke="{colour}" stroke-dasharray="{share * circ:.2f} {circ:.2f}" '
                     f'stroke-dashoffset="{-start * circ:.2f}" transform="rotate(-90 85 85)"/>')
        shown = fmt(v, c.unit) if c.unit == "%" else f"{fmt(v, c.unit)} · {share:.0%}"  # % values are the shares
        items.append(f'<li><i style="--s:{colour}"></i>{_e(label)}<b>{_e(shown)}</b></li>')
        start += share
    centre = "" if c.unit == "%" else f'<text class="tot" x="85" y="90" text-anchor="middle">{_e(fmt(sum(vals), c.unit))}</text>'
    return f'<div class="donut"><svg viewBox="0 0 170 170" aria-hidden="true">{"".join(rings)}{centre}</svg><ul>{"".join(items)}</ul></div>'


def render(c: Chart | None) -> str:
    if c is None or not c.labels:
        return ""
    series = _series(c)
    if not series:
        return ""
    body = {"bar": _bars, "line": _line, "donut": _donut}[c.type](c, series)
    src = f'<div class="src">Source: {_e(c.source)}</div>' if c.source else ""
    return (f'<figure class="chart" role="img" aria-label="{_e(c.caption)}" style="margin:8px 0 10px">'
            f"<h4>{_e(c.title)}</h4>{body}<figcaption class=\"caption\">{_e(c.caption)}</figcaption>{src}</figure>")
