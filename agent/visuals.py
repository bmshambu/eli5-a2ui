"""The picture on the explainer page, one layout per Diagram.type, in HTML and CSS.

HTML rather than one fixed SVG so the layout reflows with the panel: flow steps sit in a row
and stack on a narrow panel, parts and compare use a responsive grid. Only the cycle ring is
SVG. Each node gets a colour from a five-colour palette (light and dark) and an emoji; cards
appear one after another unless the viewer prefers reduced motion.
"""
import html
import math

from .schema import Diagram, DiagramNode

CSS = """
:root{--c0:#1a73e8;--c0t:#e8f0fe;--c1:#188038;--c1t:#e6f4ea;--c2:#e37400;--c2t:#fef0e0;--c3:#9334e6;--c3t:#f3e8fd;--c4:#d01884;--c4t:#fde7f3}
@media (prefers-color-scheme:dark){:root{--c0:#8ab4f8;--c0t:#1f2b40;--c1:#81c995;--c1t:#1c3326;--c2:#fcad70;--c2t:#3b2a1a;--c3:#c58af9;--c3t:#2f2240;--c4:#ff8bcb;--c4t:#3d1f30}}
.viz{margin:4px 0 8px}
.node{--c:var(--c0);--ct:var(--c0t);background:var(--ct);border:1px solid color-mix(in srgb,var(--c) 35%,transparent);
border-top:4px solid var(--c);border-radius:14px;padding:12px;min-width:0;position:relative}
.node .emo{font-size:30px;line-height:1;display:block;margin-bottom:6px}
.node b{display:block;font-size:14px;line-height:1.3;color:var(--ink)}
.node span.n{display:block;font-size:12.5px;line-height:1.4;color:var(--muted);margin-top:2px}
.num{position:absolute;top:8px;right:10px;font-size:12px;font-weight:700;color:var(--c)}
.k0{--c:var(--c0);--ct:var(--c0t)}.k1{--c:var(--c1);--ct:var(--c1t)}.k2{--c:var(--c2);--ct:var(--c2t)}.k3{--c:var(--c3);--ct:var(--c3t)}.k4{--c:var(--c4);--ct:var(--c4t)}
.pop{animation:pop .45s ease-out both;animation-delay:calc(var(--i,0) * 140ms)}
@keyframes pop{from{opacity:0;transform:translateY(10px) scale(.97)}}
@media (prefers-reduced-motion:reduce){.pop,.orbit{animation:none!important}}
.flow{display:flex;align-items:stretch;gap:4px}
.flow .node{flex:1 1 0}
.arrow{align-self:center;color:var(--muted);font-size:20px;flex:0 0 auto}
@media (max-width:560px){.flow{flex-direction:column}.arrow{transform:rotate(90deg);margin:-2px auto}}
.parts .hub{margin:0 auto;max-width:280px;text-align:center;border-radius:16px;padding:12px 16px;font-weight:700;
background:linear-gradient(135deg,var(--c0t),var(--c3t));border:1px solid var(--line)}
.parts .hub .emo{font-size:34px;display:block}
.parts .wire{height:18px;border-left:2px solid var(--line);width:0;margin:0 auto}
.parts .grid{display:grid;grid-template-columns:repeat(var(--cols,3),1fr);gap:10px;border-top:2px solid var(--line);padding-top:12px}
.compare{display:grid;grid-template-columns:1fr auto 1fr;gap:10px;align-items:start}
.compare .side{display:flex;flex-direction:column;gap:8px}
.compare h3{margin:0;font-size:15px;text-align:center;color:var(--c);padding:6px;border-radius:10px;background:var(--ct)}
.compare .vs{align-self:center;font-weight:800;color:var(--muted);font-size:13px;border:1px solid var(--line);border-radius:50%;width:34px;height:34px;display:grid;place-items:center}
@media (max-width:520px){.parts .grid{grid-template-columns:1fr 1fr}.compare{grid-template-columns:1fr}.compare .vs{margin:0 auto}}
.cycle{position:relative;width:100%;max-width:380px;aspect-ratio:1;margin:0 auto}
.cycle svg{position:absolute;inset:0;width:100%;height:100%}
.cycle .ring{fill:none;stroke:var(--line);stroke-width:2;stroke-dasharray:6 6}
.cycle .dot{fill:var(--accent)}
.orbit{transform-origin:50% 50%;animation:spin 8s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
.cycle .node{position:absolute;width:30%;transform:translate(-50%,-50%);text-align:center;padding:8px;animation-name:fade}
@keyframes fade{from{opacity:0}}
.cycle .node .emo{font-size:26px;margin-bottom:2px}
.cycle .center{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:30%;text-align:center;font-weight:700;font-size:14px;color:var(--muted)}
.legend{margin:10px 0 0;padding-left:20px;font-size:13px;color:var(--muted)}.legend b{color:var(--ink)}
"""


def _e(text: str | None) -> str:
    return html.escape(text or "", quote=True)


def _node(n: DiagramNode, i: int, num: bool = False, note: bool = True, color: int | None = None, pos: str = "") -> str:
    """One card; i sets its reveal order and (unless color is given) its colour."""
    return (f'<div class="node pop k{(i if color is None else color) % 5}" style="{pos}--i:{i}">'
            + (f'<span class="num">{i + 1}</span>' if num else "")
            + f'<span class="emo" aria-hidden="true">{_e(n.emoji)}</span><b>{_e(n.label)}</b>'
            + (f'<span class="n">{_e(n.note)}</span>' if note else "") + "</div>")


def _flow(d: Diagram) -> str:
    arrow = '<span class="arrow" aria-hidden="true">&rarr;</span>'
    return f'<div class="viz flow">{arrow.join(_node(n, i, num=True) for i, n in enumerate(d.nodes))}</div>'


def _cycle(d: Diagram, center: str) -> str:
    """Nodes around a dashed ring with a dot travelling round it; notes in a legend below."""
    k = len(d.nodes)
    placed = []
    for i, n in enumerate(d.nodes):
        a = -math.pi / 2 + 2 * math.pi * i / k
        placed.append(_node(n, i, note=False, pos=f"left:{50 + 37 * math.cos(a):.1f}%;top:{50 + 37 * math.sin(a):.1f}%;"))
    ring = ('<svg viewBox="0 0 100 100" aria-hidden="true"><circle class="ring" cx="50" cy="50" r="37"/>'
            '<g class="orbit"><circle class="dot" cx="50" cy="13" r="1.6"/></g></svg>')
    legend = "".join(f"<li><b>{_e(n.label)}</b>: {_e(n.note)}</li>" for n in d.nodes)
    return (f'<div class="viz cycle">{ring}<div class="center">{_e(center)}</div>{"".join(placed)}</div>'
            f'<ol class="legend">{legend}</ol>')


def _parts(d: Diagram, center: str) -> str:
    cards = "".join(_node(n, i) for i, n in enumerate(d.nodes))
    return (f'<div class="viz parts"><div class="hub pop">{_e(center)}</div>'
            f'<div class="wire"></div><div class="grid" style="--cols:{2 if len(d.nodes) == 4 else 3}">{cards}</div></div>')


def _compare(d: Diagram) -> str:
    sides = [[n for n in d.nodes if n.side == s] for s in ("left", "right")]
    if not all(sides):  # model left side unset: split in half
        half = (len(d.nodes) + 1) // 2
        sides = [d.nodes[:half], d.nodes[half:]]
    cols = []
    for c, (title, nodes) in enumerate(zip((d.left_title or "A", d.right_title or "B"), sides)):
        k = 0 if c == 0 else 2  # blue vs orange
        items = "".join(_node(n, i * 2 + c, color=k) for i, n in enumerate(nodes))
        cols.append(f'<div class="side k{k}"><h3>{_e(title)}</h3>{items}</div>')
    return f'<div class="viz compare">{cols[0]}<span class="vs">vs</span>{cols[1]}</div>'


def render(d: Diagram, title: str) -> str:
    if not d.nodes:
        return ""
    center = d.center or title
    body = {"flow": lambda: _flow(d), "cycle": lambda: _cycle(d, center),
            "parts": lambda: _parts(d, center), "compare": lambda: _compare(d)}[d.type]()
    return f'<figure role="img" aria-label="{_e(d.caption)}" style="margin:0">{body}</figure>'
