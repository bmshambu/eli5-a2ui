"""Inline SVG diagrams for the explainer page, one layout per Diagram.type.

Drawn on a narrow 360-unit canvas with at most two columns, so labels stay readable when the
Canvas side panel is narrow. Colours come from the page's CSS variables (light and dark).
"""
import html
import textwrap

from .schema import Diagram, DiagramNode

W = 360
PAD = 8
LINE = 15  # px per text line


def _lines(x: float, y: float, text: str, width_chars: int, cls: str, anchor: str = "start") -> tuple[str, float]:
    """<text> with one <tspan> per wrapped line; returns (svg, height used)."""
    rows = textwrap.wrap(text, width_chars) or [""]
    spans = "".join(
        f'<tspan x="{x:g}" dy="{0 if i == 0 else LINE}">{html.escape(r)}</tspan>' for i, r in enumerate(rows)
    )
    return f'<text class="{cls}" x="{x:g}" y="{y:g}" text-anchor="{anchor}">{spans}</text>', len(rows) * LINE


def _box(x: float, y: float, w: float, node: DiagramNode, chars: int) -> tuple[str, float]:
    label, lh = _lines(x + 10, y + 20, node.label, chars, "dl")
    note, nh = _lines(x + 10, y + 20 + lh + 2, node.note, chars + 4, "dn")
    h = 14 + lh + nh + 8
    return f'<rect class="db" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="10"/>{label}{note}', h


def _flow(d: Diagram) -> tuple[str, float]:
    """Numbered steps down the page, joined by a line."""
    out, y, centers = [], PAD, []
    for i, n in enumerate(d.nodes, 1):
        label, lh = _lines(54, y + 18, n.label, 36, "dl")
        note, nh = _lines(54, y + 18 + lh + 2, n.note, 42, "dn")
        centers.append(y + 14)
        out.append(f'<circle class="dc" cx="22" cy="{y + 14:g}" r="13"/>'
                   f'<text class="dnum" x="22" y="{y + 19:g}" text-anchor="middle">{i}</text>{label}{note}')
        y += max(lh + nh + 22, 44)
    rail = f'<line class="dr" x1="22" y1="{centers[0]:g}" x2="22" y2="{centers[-1]:g}"/>' if len(centers) > 1 else ""
    return rail + "".join(out), y


def _parts(d: Diagram, hub: str) -> tuple[str, float]:
    """The whole on top, its parts in two columns below, each wired to the whole."""
    hub_text, hh = _lines(W / 2, PAD + 22, hub, 34, "dh", "middle")
    hub_h = hh + 18
    col_w, y0 = (W - 3 * PAD) / 2, PAD + hub_h + 28
    # wires first so boxes sit on top: hub down to the top of each column
    wires = "".join(
        f'<path class="dr" d="M{W / 2:g} {PAD + hub_h:g}V{PAD + hub_h + 14:g}H{PAD + c * (col_w + PAD) + col_w / 2:g}V{y0:g}"/>'
        for c in range(min(2, len(d.nodes)))
    )
    out = [wires, f'<rect class="dhub" x="{W / 2 - 130:g}" y="{PAD:g}" width="260" height="{hub_h:g}" rx="12"/>{hub_text}']
    ys = [y0, y0]
    for i, n in enumerate(d.nodes):
        c = i % 2
        box, h = _box(PAD + c * (col_w + PAD), ys[c], col_w, n, 20)
        out.append(box)
        ys[c] += h + PAD
    return "".join(out), max(ys)


def _compare(d: Diagram) -> tuple[str, float]:
    """Two columns with a title each; nodes sit under their side."""
    col_w = (W - 3 * PAD) / 2
    out, ys = [], []
    for c, (side, title) in enumerate((("left", d.left_title or "A"), ("right", d.right_title or "B"))):
        x = PAD + c * (col_w + PAD)
        head, th = _lines(x + col_w / 2, PAD + 16, title, 22, "dh", "middle")
        out.append(head)
        y = PAD + th + 12
        nodes = [n for n in d.nodes if n.side == side]
        if not any(n.side for n in d.nodes):  # model left side unset: split in half
            half = (len(d.nodes) + 1) // 2
            nodes = d.nodes[:half] if c == 0 else d.nodes[half:]
        for n in nodes:
            box, h = _box(x, y, col_w, n, 20)
            out.append(box)
            y += h + PAD
        ys.append(y)
    out.insert(0, f'<line class="dr" x1="{W / 2:g}" y1="{PAD:g}" x2="{W / 2:g}" y2="{max(ys):g}" stroke-dasharray="4 4"/>')
    return "".join(out), max(ys)


def render(d: Diagram, hub: str) -> str:
    if not d.nodes:
        return ""
    body, h = {"flow": lambda: _flow(d), "parts": lambda: _parts(d, hub), "compare": lambda: _compare(d)}[d.type]()
    return (f'<svg class="diagram" viewBox="0 0 {W} {h + PAD:g}" role="img" '
            f'aria-label="{html.escape(d.caption, quote=True)}">{body}</svg>')
