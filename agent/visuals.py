"""Section diagrams on the explainer page, one layout per Diagram.type, in HTML and CSS.

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
.flow{display:flex;align-items:stretch;gap:4px}
.flow .node{flex:1 1 0}
.arrow{align-self:center;color:var(--c1);font-size:22px;font-weight:700;flex:0 0 auto}
@media (max-width:600px){.flow{flex-direction:column}.arrow{transform:rotate(90deg);margin:-4px auto}}
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
"""


def _e(text: str | None) -> str:
    return html.escape(text or "", quote=True)


def _node(n: DiagramNode, i: int, note: bool = True, color: int | None = None, pos: str = "", mark: str | None = None) -> str:
    """One card with a square numbered marker; i sets its reveal order and (unless color is
    given) its colour."""
    return (f'<div class="node pop k{(i if color is None else color) % 5}" style="{pos}--i:{i}">'
            f'<span class="mk">{_e(mark or str(i + 1))}</span><b>{_e(n.label)}</b>'
            + (f'<span class="n">{_e(n.note)}</span>' if note else "") + "</div>")


def _flow(d: Diagram) -> str:
    arrow = '<span class="arrow" aria-hidden="true">&rsaquo;</span>'
    return f'<div class="viz flow">{arrow.join(_node(n, i) for i, n in enumerate(d.nodes))}</div>'


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
    body = {"flow": lambda: _flow(d), "cycle": lambda: _cycle(d, center),
            "parts": lambda: _parts(d, center), "compare": lambda: _compare(d)}[d.type]()
    return (f'<figure role="img" aria-label="{_e(d.caption)}" style="margin:0">{body}'
            f'<figcaption class="caption">{_e(d.caption)}</figcaption></figure>')
