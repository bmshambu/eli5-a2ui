"""The explainer page shown in IFrameSrcdoc: level tabs, diagram, sources and follow-up chips.

One self-contained HTML document (inline CSS/JS/SVG; the frame enforces connect-src 'none').
Proven in GE by the step 0 probe: JS runs in the frame, and a postMessage
{type: 'a2ui_action', action, data} reaches the agent as a v0.9 action whose context is `data`.
GE shows context.prompt as the user's turn, so each chip sends its question as the prompt.
"""
import html
import json
import re

from . import svg
from .schema import LEVELS, Explanation

ASK_ACTION = "ask"

_STYLE = """
:root{--bg:#fff;--ink:#1f1f1f;--muted:#5f6368;--line:#dadce0;--accent:#0b57d0;--tint:#eef3fd;--card:#f8f9fa;
--hi:#fef7e0;--hi-ink:#5c4400;--ok:#137333;--ok-bg:#e6f4ea;--mid:#8a5300;--mid-bg:#fef7e0;--low:#a50e0e;--low-bg:#fce8e6}
@media (prefers-color-scheme:dark){:root{--bg:#1f1f1f;--ink:#e8eaed;--muted:#9aa0a6;--line:#3c4043;--accent:#a8c7fa;--tint:#233047;
--card:#28292a;--hi:#3a3220;--hi-ink:#fde293;--ok:#81c995;--ok-bg:#1e3a29;--mid:#fdd663;--mid-bg:#3a3220;--low:#f28b82;--low-bg:#4a2523}}
*{box-sizing:border-box}html{color-scheme:light dark}
body{margin:0;padding:20px 20px 28px;font:15px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--ink)}
.tags{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px}
.tag{font-size:12px;color:var(--muted);border:1px solid var(--line);border-radius:10px;padding:1px 8px}
.conf{font-size:12px;border-radius:10px;padding:1px 8px;font-weight:600}
.conf.high{color:var(--ok);background:var(--ok-bg)}.conf.medium{color:var(--mid);background:var(--mid-bg)}.conf.low{color:var(--low);background:var(--low-bg)}
h1{font-size:22px;line-height:1.3;margin:0 0 6px}.lede{color:var(--muted);margin:0 0 16px}
h2{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:24px 0 8px}
.tabs{display:flex;gap:2px;border-bottom:1px solid var(--line);margin-bottom:14px;overflow-x:auto}
.tabs button{border:0;background:none;padding:8px 14px;font:inherit;font-size:14px;color:var(--muted);cursor:pointer;border-bottom:3px solid transparent;white-space:nowrap}
.tabs button[aria-selected=true]{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}
.tabs button:focus-visible,.chip:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.panel[hidden]{display:none}
.analogy{background:var(--hi);color:var(--hi-ink);border-radius:10px;padding:10px 14px;margin:0 0 12px}
.analogy b{display:block;font-size:12px;letter-spacing:.04em;text-transform:uppercase;opacity:.8}
.body{margin:0}sup a{color:var(--accent);text-decoration:none;font-size:11px;padding:0 1px}
.diagram{display:block;width:100%;max-width:520px;height:auto;margin:4px 0 6px}
.diagram .db{fill:var(--card);stroke:var(--line)}.diagram .dhub{fill:var(--tint);stroke:var(--accent)}
.diagram .dc{fill:var(--tint);stroke:var(--accent)}.diagram .dr{stroke:var(--line);stroke-width:2;fill:none}
.diagram text{font-family:inherit}.diagram .dl{font-size:13px;font-weight:600;fill:var(--ink)}
.diagram .dn{font-size:12px;fill:var(--muted)}.diagram .dh{font-size:13px;font-weight:700;fill:var(--accent)}
.diagram .dnum{font-size:13px;font-weight:700;fill:var(--accent)}
.caption{font-size:13px;color:var(--muted);margin:0}
ol.sources{margin:0;padding-left:22px;font-size:13px;color:var(--muted)}ol.sources a{color:var(--accent)}
.chips{display:flex;flex-direction:column;align-items:flex-start;gap:8px}
.chip{border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:18px;padding:7px 14px;font:inherit;font-size:14px;cursor:pointer;text-align:left}
.chip:hover{background:var(--tint);border-color:var(--accent)}.chip[disabled]{opacity:.55;cursor:default}
"""

_SCRIPT = """
var tabs=[].slice.call(document.querySelectorAll('.tabs button'));
function pick(t){tabs.forEach(function(b){var on=b===t;b.setAttribute('aria-selected',on);b.tabIndex=on?0:-1;
document.getElementById(b.getAttribute('aria-controls')).hidden=!on;});}
tabs.forEach(function(b,i){b.addEventListener('click',function(){pick(b);});
b.addEventListener('keydown',function(e){var d=e.key==='ArrowRight'?1:e.key==='ArrowLeft'?-1:0;
if(d){var n=tabs[(i+d+tabs.length)%tabs.length];pick(n);n.focus();}});});
document.querySelectorAll('.chip').forEach(function(c){c.addEventListener('click',function(){
window.parent.postMessage({type:'a2ui_action',action:ACTION,data:{prompt:c.dataset.q}},'*');
document.querySelectorAll('.chip').forEach(function(x){x.disabled=true;});c.textContent='Asked: '+c.dataset.q;});});
"""


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def _cited(text: str, n_sources: int) -> str:
    """Escapes text and turns [n] into a link to source n; drops citations to missing sources."""
    def link(m):
        n = int(m.group(1))
        return f'<sup><a href="#src{n}">[{n}]</a></sup>' if 1 <= n <= n_sources else ""
    return re.sub(r"\s?\[(\d+)\]", link, _esc(text))


def page(e: Explanation, sources: list[dict]) -> str:
    n = len(sources)
    tags = "".join(f'<span class="tag">{_esc(t)}</span>' for t in e.tags[:3])
    tabs, panels = [], []
    for i, (key, label) in enumerate(LEVELS):
        level = getattr(e, key)
        on = i == 0
        tabs.append(f'<button role="tab" id="t-{key}" aria-controls="p-{key}" aria-selected="{str(on).lower()}" '
                    f'tabindex="{0 if on else -1}">{label}</button>')
        panels.append(
            f'<div class="panel" role="tabpanel" id="p-{key}" aria-labelledby="t-{key}"{"" if on else " hidden"}>'
            f'<p class="analogy"><b>Think of it like</b>{_cited(level.analogy, n)}</p>'
            f'<p class="body">{_cited(level.body, n)}</p></div>'
        )
    diagram = svg.render(e.diagram, e.title)
    picture = (f'<h2>The picture</h2>{diagram}<p class="caption">{_esc(e.diagram.caption)}</p>' if diagram else "")
    source_list = "".join(
        f'<li id="src{i}"><a href="{_esc(s["uri"])}" target="_blank" rel="noopener">{_esc(s["title"])}</a></li>'
        for i, s in enumerate(sources, 1)
    )
    sources_html = f'<h2>Sources</h2><ol class="sources">{source_list}</ol>' if sources else ""
    chips = "".join(f'<button class="chip" data-q="{_esc(q)}">{_esc(q)}</button>' for q in e.follow_ups[:3])
    chips_html = f'<h2>Ask next</h2><div class="chips">{chips}</div>' if chips else ""
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{_esc(e.title)}</title><style>{_STYLE}</style></head><body>"
        f'<div class="tags">{tags}<span class="conf {e.confidence}">{e.confidence.capitalize()} confidence</span></div>'
        f'<h1>{_esc(e.title)}</h1><p class="lede">{_esc(e.one_liner)}</p>'
        f'<div class="tabs" role="tablist" aria-label="Explanation level">{"".join(tabs)}</div>{"".join(panels)}'
        f"{picture}{sources_html}{chips_html}"
        f"<script>var ACTION={json.dumps(ASK_ACTION)};{_SCRIPT}</script></body></html>"
    )
