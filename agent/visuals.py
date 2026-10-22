"""Section diagrams on the explainer page, one layout per Diagram.type, in HTML and CSS.

The process, funnel, roadmap, timeline, staircase, pyramid, matrix and pillar layouts follow
the KPMG templates in brand/extract/07-diagrams/templates (see templates-overview.png), built
live from the model's nodes instead of as fixed SVGs so any text fits.

Styled on the KPMG 2026 brand (brand/extract): square numbered markers instead of emoji,
the KPMG Blue / Cobalt / Pacific Blue / Purple palette, light blue tint panels. HTML rather
than one fixed SVG so the layout reflows with the panel; only the cycle ring is SVG. Cards
appear one after another unless the viewer prefers reduced motion.
"""
import html
import math

from .schema import Diagram, DiagramNode

CSS = """
:root{--c0:#00338D;--c1:#1E49E2;--c2:#00B8F5;--c3:#7213EA;--c4:#510DBC}
@media (prefers-color-scheme:dark){:root{--c0:#76D2FF;--c1:#7C97F0;--c2:#00B8F5;--c3:#B497FF;--c4:#C9B4FF}}
.viz{margin:6px 0 8px}
.node{--c:var(--c0);background:var(--tint5);border:1px solid var(--line);border-left:4px solid var(--c);
padding:12px 12px 12px 14px;min-width:0;position:relative}
.node .mk{display:inline-grid;place-items:center;min-width:26px;height:26px;padding:0 6px;background:var(--c);color:#fff;
font-weight:700;font-size:14px;margin-bottom:8px}
.node b{display:block;font-size:15px;line-height:1.3;color:var(--brand)}
.node span.n{display:block;font-size:14px;line-height:1.45;color:var(--muted);margin-top:3px}
.k0{--c:var(--c0)}.k1{--c:var(--c1)}.k2{--c:var(--c2)}.k3{--c:var(--c3)}.k4{--c:var(--c4)}
.pop{animation:pop .45s ease-out both;animation-delay:calc(var(--i,0) * 120ms)}
@keyframes pop{from{opacity:0;transform:translateY(10px)}}
@media (prefers-reduced-motion:reduce){.pop,.orbit{animation:none!important}}
.parts .hub{margin:0 auto;max-width:300px;text-align:center;padding:12px 16px;font-weight:700;font-size:16px;
background:linear-gradient(120deg,#1E49E2,#00338D);color:#fff}
.parts .wire{height:18px;border-left:2px solid var(--c1);width:0;margin:0 auto}
.parts .grid{display:grid;grid-template-columns:repeat(var(--cols,3),1fr);gap:10px;border-top:2px solid var(--c1);padding-top:12px}
.compare{display:grid;grid-template-columns:1fr auto 1fr;gap:10px;align-items:start}
.compare .side{display:flex;flex-direction:column;gap:8px}
.compare h4{margin:0;font-size:16px;text-align:center;color:#fff;padding:9px;background:var(--c)}
.compare .vs{align-self:center;font-weight:700;color:var(--brand);font-size:14px;border:2px solid var(--brand);width:40px;height:40px;display:grid;place-items:center}
@media (max-width:540px){.parts .grid{grid-template-columns:1fr 1fr}.compare{grid-template-columns:1fr}.compare .vs{margin:0 auto}}
.cycle{position:relative;width:100%;max-width:400px;aspect-ratio:1;margin:0 auto}
.cycle svg{position:absolute;inset:0;width:100%;height:100%}
.cycle .ring{fill:none;stroke:var(--c1);stroke-width:1.2;stroke-dasharray:4 4;opacity:.6}
.cycle .dot{fill:var(--c2)}
.orbit{transform-origin:50% 50%;animation:spin 8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
.cycle .node{position:absolute;width:31%;transform:translate(-50%,-50%);text-align:center;padding:8px;border-left-width:1px;border-top:4px solid var(--c);animation-name:fade}
@keyframes fade{from{opacity:0}}
.cycle .node .mk{margin-bottom:4px}
.cycle .center{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:30%;text-align:center;font-weight:700;font-size:15px;color:var(--brand)}
.legend{margin:10px 0 0;padding-left:22px;font-size:14px;color:var(--muted)}.legend b{color:var(--brand)}
.hd{font-family:"KPMG Bold","Arial Narrow","Helvetica Neue Condensed",Arial,sans-serif;font-stretch:condensed;font-weight:700}
.chev{display:flex;gap:4px}
.chev .step{flex:1 1 0;min-width:0}
.chev .head{background:var(--c);color:#fff;padding:10px 26px 10px 14px;min-height:64px;
clip-path:polygon(0 0,calc(100% - 16px) 0,100% 50%,calc(100% - 16px) 100%,0 100%,12px 50%)}
.chev .step:first-child .head{clip-path:polygon(0 0,calc(100% - 16px) 0,100% 50%,calc(100% - 16px) 100%,0 100%)}
.chev .head small{display:block;font-size:14px;opacity:.85;letter-spacing:.04em}
.chev .head b{display:block;font-size:17px;line-height:1.15}
.chev .body{padding:8px 4px 0 6px;font-size:14px;color:var(--muted);border-top:3px solid var(--c);margin:8px 14px 0 0}
.chev .body .when{display:block;font-weight:700;color:var(--brand)}
.g0{--c:#00338D}.g1{--c:#1E49E2}.g2{--c:#1A6FE8}.g3{--c:#0091DA}.g4{--c:#00B8F5}.g5{--c:#7213EA}.g6{--c:#510DBC}.g7{--c:#AB0D82}
@media (max-width:600px){.chev{flex-direction:column;gap:6px}.chev .head,.chev .step:first-child .head{clip-path:none;min-height:0;border-left:6px solid rgba(255,255,255,.35)}
.chev .body{margin:4px 0 0;border-top:0}}
.funnel{display:grid;grid-template-columns:minmax(0,56%) 1fr;gap:6px 14px;align-items:center}
.funnel .stage{--w:100%;width:var(--w);margin:0 auto;background:var(--c);color:#fff;text-align:center;padding:12px 6px;
clip-path:polygon(0 0,100% 0,calc(100% - 14px) 100%,14px 100%);font-size:16px}
.funnel .info{border-bottom:1px solid var(--line);padding:4px 0}
.funnel .info .v{font-size:24px;color:var(--brand);line-height:1.1}.funnel .info .n{font-size:14px;color:var(--muted)}
.funnel .info .conv{float:right;font-size:14px;font-weight:700;color:var(--c3)}
.tl{position:relative;display:grid;grid-template-columns:repeat(var(--n),1fr);padding:4px 0}
.tl::before{content:"";position:absolute;left:0;right:0;top:50%;height:3px;background:var(--c0)}
.tl .ms{position:relative;text-align:center;padding:0 4px;display:grid;grid-template-rows:1fr 30px 1fr}
.tl .ms .dot{grid-row:2;justify-self:center;align-self:center;width:18px;height:18px;border-radius:50%;background:var(--bg);border:3px solid var(--c);z-index:1}
.tl .ms .txt{grid-row:1;align-self:end;padding-bottom:6px}.tl .ms.down .txt{grid-row:3;align-self:start;padding:6px 0 0}
.tl .yr{display:block;font-size:24px;line-height:1.1;color:var(--c)}.tl .ms b{display:block;font-size:14px;color:var(--brand)}
.tl .ms span.n{display:block;font-size:14px;color:var(--muted);line-height:1.35}
@media (max-width:600px){.tl{grid-template-columns:1fr;padding-left:22px}.tl::before{left:8px;right:auto;top:0;bottom:0;width:3px;height:auto}
.tl .ms{display:block;text-align:left;padding:6px 0}.tl .ms .dot{position:absolute;left:-25px;top:10px}.tl .ms.down .txt,.tl .ms .txt{padding:0 0 0 8px}}
.stairs{display:flex;align-items:flex-end;gap:6px;height:260px}
.stairs .lvl{flex:1 1 0;min-width:0;height:var(--h);background:var(--c);color:var(--t,#fff);padding:10px 8px;overflow:hidden}
.stairs .lvl b{display:block;font-size:17px;line-height:1.15}.stairs .lvl b i{font-style:normal;font-size:24px;margin-right:4px}
.stairs .lvl span{display:block;font-size:14px;line-height:1.35;opacity:.9;margin-top:4px}
@media (max-width:600px){.stairs{flex-direction:column-reverse;align-items:stretch;height:auto}.stairs .lvl{flex:none;height:auto;width:var(--h);min-width:55%}}
.pyr{display:grid;grid-template-columns:minmax(0,50%) 1fr;gap:4px 14px;align-items:center}
.pyr .tier{margin:0 auto;width:var(--w);background:var(--c);color:#fff;text-align:center;font-size:15px;padding:12px 4px;
clip-path:polygon(var(--in) 0,calc(100% - var(--in)) 0,100% 100%,0 100%)}
.pyr .tier.top{clip-path:polygon(50% 0,100% 100%,0 100%);padding-top:22px}
.pyr .info{border-bottom:1px solid var(--line);padding:2px 0}.pyr .info b{display:block;color:var(--c);font-size:16px}
.pyr .info span{font-size:14px;color:var(--muted)}
.mx{display:grid;grid-template-columns:28px 1fr 1fr;grid-template-rows:auto auto auto;gap:6px}
.mx .ya{grid-row:1/3;writing-mode:vertical-rl;transform:rotate(180deg);text-align:center;font-size:14px;color:var(--brand);font-weight:700;border-right:2px solid var(--brand)}
.mx .q{padding:12px;min-height:110px;background:var(--qb);color:var(--qt)}
.mx .q b{display:block;font-size:18px}.mx .q span{font-size:14px;line-height:1.4}
.mx .xa{grid-column:2/4;grid-row:3;text-align:center;font-size:14px;color:var(--brand);font-weight:700;border-top:2px solid var(--brand);padding-top:4px}
.q0{--qb:#00338D;--qt:#fff}.q1{--qb:#00B8F5;--qt:#0C233C}.q2{--qb:var(--tint10);--qt:var(--ink)}.q3{--qb:var(--tint20,#D2DBF9);--qt:var(--ink)}
.pillars{background:linear-gradient(120deg,#1E49E2,#00338D);padding:16px;display:grid;grid-template-columns:repeat(var(--n),1fr);gap:12px}
.pillars .pl{color:#fff;min-width:0}
.pillars .pl .cap{background:linear-gradient(90deg,#00B8F5,#ACEAFF);color:#00338D;padding:12px;font-size:18px;line-height:1.15;min-height:72px}
.pillars .pl .v{display:block;font-size:26px;margin:10px 0 2px}.pillars .pl span{font-size:14px;line-height:1.4;color:#E9EDFC}
.pillars .pl::after{content:"";display:block;width:36px;height:3px;background:#00B8F5;margin-top:10px}
@media (max-width:600px){.funnel,.pyr{grid-template-columns:1fr}.pillars{grid-template-columns:1fr}.pillars .pl .cap{min-height:0}}
"""


def _e(text: str | None) -> str:
    return html.escape(text or "", quote=True)


def _node(n: DiagramNode, i: int, note: bool = True, color: int | None = None, pos: str = "", mark: str | None = None) -> str:
    """One card with a square numbered marker; i sets its reveal order and (unless color is
    given) its colour."""
    return (f'<div class="node pop k{(i if color is None else color) % 5}" style="{pos}--i:{i}">'
            f'<span class="mk">{_e(mark or str(i + 1))}</span><b>{_e(n.label)}</b>'
            + (f'<span class="n">{_e(n.note)}</span>' if note else "") + "</div>")


def _chevrons(d: Diagram, phases: bool = False) -> str:
    """Process steps (or roadmap phases) as numbered chevrons, KPMG Blue to Pacific Blue."""
    steps = []
    for i, n in enumerate(d.nodes):
        tag = f"Phase {i + 1}" if phases else f"{i + 1:02d}"
        when = f'<span class="when">{_e(n.value)}</span>' if n.value else ""
        steps.append(f'<div class="step g{min(i, 4)} pop" style="--i:{i}"><div class="head hd"><small>{tag}</small><b>{_e(n.label)}</b></div>'
                     f'<div class="body">{when}{_e(n.note)}</div></div>')
    return f'<div class="viz chev">{"".join(steps)}</div>'


def _number(text: str | None) -> float | None:
    """'10,000' -> 10000.0; anything else (ranges, words) -> None."""
    try:
        return float((text or "").replace(",", "").strip())
    except ValueError:
        return None


def _funnel(d: Diagram) -> str:
    k, rows = len(d.nodes), []
    for i, n in enumerate(d.nodes):
        prev, cur = _number(d.nodes[i - 1].value) if i else None, _number(n.value)
        conv = f'<span class="conv">{cur / prev:.0%}</span>' if prev and cur is not None else ""
        value = f'<span class="v hd">{_e(n.value)}</span>' if n.value else f'<span class="v hd">{_e(n.label)}</span>'
        rows.append(f'<div class="stage hd g{min(i, 4)} pop" style="--w:{100 - i * (50 / max(k - 1, 1)):.0f}%;--i:{i}">{_e(n.label)}</div>'
                    f'<div class="info">{conv}{value}<div class="n">{_e(n.note)}</div></div>')
    return f'<div class="viz funnel">{"".join(rows)}</div>'


def _timeline(d: Diagram) -> str:
    items = "".join(
        f'<div class="ms g{i % 5}{" down" if i % 2 else ""} pop" style="--i:{i}"><div class="txt">'
        f'<span class="yr hd">{_e(n.value or str(i + 1))}</span><b>{_e(n.label)}</b><span class="n">{_e(n.note)}</span></div>'
        f'<span class="dot"></span></div>' for i, n in enumerate(d.nodes))
    return f'<div class="viz tl" style="--n:{len(d.nodes)}">{items}</div>'


def _staircase(d: Diagram) -> str:
    k = len(d.nodes)
    shades = ("#D2DBF9", "#ACEAFF", "#00B8F5", "#1E49E2", "#00338D", "#0C233C")[-k:] if k <= 6 else ("#00338D",) * k
    steps = "".join(
        f'<div class="lvl pop" style="--h:{35 + 65 * i / max(k - 1, 1):.0f}%;--c:{shades[i]};{"--t:#00338D;" if i < 2 and k > 2 else ""}--i:{i}">'
        f'<b class="hd"><i>{i + 1}</i>{_e(n.label)}</b><span>{_e(n.note)}</span></div>' for i, n in enumerate(d.nodes))
    return f'<div class="viz stairs">{steps}</div>'


def _pyramid(d: Diagram) -> str:
    k, rows = len(d.nodes), []
    widths = [30 + 70 * i / max(k - 1, 1) for i in range(k)]
    for i, n in enumerate(d.nodes):
        w = widths[i]
        inset = (1 - widths[i - 1] / w) / 2 * 100 if i else 0  # each tier's top edge meets the tier above
        top = " top" if i == 0 else ""
        colour = "var(--c3)" if i == 0 else ("#00B8F5", "#1A6FE8", "#1E49E2", "#00338D", "#0C233C")[min(i - 1, 4)]
        rows.append(f'<div class="tier hd{top} pop" style="--w:{w:.1f}%;--in:{inset:.1f}%;--i:{i};--c:{colour}">{"" if top else _e(n.label)}</div>'
                    f'<div class="info" style="--c:{colour}"><b class="hd">{_e(n.label)}</b><span>{_e(n.note)}</span></div>')
    return f'<div class="viz pyr">{"".join(rows)}</div>'


def _matrix(d: Diagram) -> str:
    cells = "".join(f'<div class="q q{i} pop" style="--i:{i}"><b class="hd">{_e(n.label)}</b><span>{_e(n.note)}</span></div>'
                    for i, n in enumerate(d.nodes[:4]))
    return (f'<div class="viz mx"><div class="ya">{_e(d.y_axis or "")} &uarr;</div>{cells}'
            f'<div class="xa">{_e(d.x_axis or "")} &rarr;</div></div>')


def _pillars(d: Diagram) -> str:
    cards = "".join(
        f'<div class="pl pop" style="--i:{i}"><div class="cap hd">{_e(n.label)}</div>'
        + (f'<span class="v hd">{_e(n.value)}</span>' if n.value else "") + f"<span>{_e(n.note)}</span></div>"
        for i, n in enumerate(d.nodes[:4]))
    return f'<div class="viz pillars" style="--n:{min(len(d.nodes), 4)}">{cards}</div>'



def _cycle(d: Diagram, center: str) -> str:
    """Nodes around a dashed ring with a dot travelling round it; notes in a legend below."""
    k = len(d.nodes)
    placed = []
    for i, n in enumerate(d.nodes):
        a = -math.pi / 2 + 2 * math.pi * i / k
        placed.append(_node(n, i, note=False, pos=f"left:{50 + 37 * math.cos(a):.1f}%;top:{50 + 37 * math.sin(a):.1f}%;"))
    ring = ('<svg viewBox="0 0 100 100" aria-hidden="true"><circle class="ring" cx="50" cy="50" r="37"/>'
            '<g class="orbit"><circle class="dot" cx="50" cy="13" r="1.8"/></g></svg>')
    legend = "".join(f"<li><b>{_e(n.label)}</b>: {_e(n.note)}</li>" for n in d.nodes)
    return (f'<div class="viz cycle">{ring}<div class="center">{_e(center)}</div>{"".join(placed)}</div>'
            f'<ol class="legend">{legend}</ol>')


def _parts(d: Diagram, center: str) -> str:
    cards = "".join(_node(n, i) for i, n in enumerate(d.nodes))
    cols = 2 if len(d.nodes) in (2, 4) else 3
    return (f'<div class="viz parts"><div class="hub pop">{_e(center)}</div>'
            f'<div class="wire"></div><div class="grid" style="--cols:{cols}">{cards}</div></div>')


def _compare(d: Diagram) -> str:
    sides = [[n for n in d.nodes if n.side == s] for s in ("left", "right")]
    if not all(sides):  # model left side unset: split in half
        half = (len(d.nodes) + 1) // 2
        sides = [d.nodes[:half], d.nodes[half:]]
    cols = []
    for c, (title, nodes) in enumerate(zip((d.left_title or "A", d.right_title or "B"), sides)):
        k = 0 if c == 0 else 3  # KPMG Blue vs Purple
        items = "".join(_node(n, i * 2 + c, color=k, mark="AB"[c] + str(i + 1)) for i, n in enumerate(nodes))
        cols.append(f'<div class="side k{k}"><h4>{_e(title)}</h4>{items}</div>')
    return f'<div class="viz compare">{cols[0]}<span class="vs">vs</span>{cols[1]}</div>'


def render(d: Diagram | None, title: str) -> str:
    if d is None or not d.nodes:
        return ""
    center = d.center or title
    body = {"flow": lambda: _chevrons(d), "roadmap": lambda: _chevrons(d, phases=True),
            "cycle": lambda: _cycle(d, center), "parts": lambda: _parts(d, center), "compare": lambda: _compare(d),
            "funnel": lambda: _funnel(d), "timeline": lambda: _timeline(d), "staircase": lambda: _staircase(d),
            "pyramid": lambda: _pyramid(d), "matrix": lambda: _matrix(d), "pillars": lambda: _pillars(d)}[d.type]()
    return (f'<figure role="img" aria-label="{_e(d.caption)}" style="margin:0">{body}'
            f'<figcaption class="caption">{_e(d.caption)}</figcaption></figure>')
