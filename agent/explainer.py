"""The explainer page shown in IFrameSrcdoc: one level, a level ladder, the picture, sources and
follow-up chips.

One self-contained HTML document (inline CSS/JS; the frame enforces connect-src 'none').
Proven in GE by the step 0 probe: JS runs in the frame, and a postMessage
{type: 'a2ui_action', action, data} reaches the agent as a v0.9 action whose context is `data`.
GE shows context.prompt as the user's turn, so every button sends what the user would type.
"""
import html
import json

from . import visuals
from .schema import LEVEL_KEYS, LEVELS, Explanation

ASK_ACTION = "ask"

_STYLE = """
:root{--bg:#fff;--ink:#1f1f1f;--muted:#5f6368;--line:#dadce0;--accent:#0b57d0;--on-accent:#fff;--tint:#eef3fd;
--hi:#fef7e0;--hi-ink:#5c4400;--ok:#137333;--ok-bg:#e6f4ea;--mid:#8a5300;--mid-bg:#fef7e0;--low:#a50e0e;--low-bg:#fce8e6}
@media (prefers-color-scheme:dark){:root{--bg:#1f1f1f;--ink:#e8eaed;--muted:#9aa0a6;--line:#3c4043;--accent:#a8c7fa;--on-accent:#062e6f;
--tint:#233047;--hi:#3a3220;--hi-ink:#fde293;--ok:#81c995;--ok-bg:#1e3a29;--mid:#fdd663;--mid-bg:#3a3220;--low:#f28b82;--low-bg:#4a2523}}
*{box-sizing:border-box}html{color-scheme:light dark}
body{margin:0;padding:20px 20px 28px;font:15px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--ink)}
.tags{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px}
.tag{font-size:12px;color:var(--muted);border:1px solid var(--line);border-radius:10px;padding:1px 8px}
.conf{font-size:12px;border-radius:10px;padding:1px 8px;font-weight:600}
.conf.high{color:var(--ok);background:var(--ok-bg)}.conf.medium{color:var(--mid);background:var(--mid-bg)}.conf.low{color:var(--low);background:var(--low-bg)}
h1{font-size:22px;line-height:1.3;margin:0 0 6px}.lede{color:var(--muted);margin:0 0 14px}
h2{font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin:24px 0 10px}
.ladder{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 16px}
.ladder button{font:inherit;font-size:13px;border:1px solid var(--line);background:var(--bg);color:var(--muted);border-radius:16px;padding:4px 12px;cursor:pointer}
.ladder button:hover{border-color:var(--accent);color:var(--accent)}
.ladder button[aria-current]{background:var(--accent);border-color:var(--accent);color:var(--on-accent);font-weight:600;cursor:default}
.analogy{display:flex;gap:12px;align-items:flex-start;background:var(--hi);color:var(--hi-ink);border-radius:14px;padding:12px 16px;margin:0 0 14px;font-size:16px}
.analogy .bulb{font-size:26px;line-height:1}.analogy b{display:block;font-size:11px;letter-spacing:.06em;text-transform:uppercase;opacity:.8}
.body{margin:0 0 14px;font-size:15.5px}
.fact{display:flex;gap:14px;align-items:center;border:1px solid var(--line);border-radius:14px;padding:12px 16px;background:linear-gradient(135deg,var(--c0t),var(--c3t))}
.fact .v{font-size:28px;font-weight:800;line-height:1.1;color:var(--accent);white-space:nowrap}.fact .l{font-size:14px}
.caption{font-size:13px;color:var(--muted);margin:6px 0 0}
ol.sources{margin:0;padding-left:22px;font-size:13px;color:var(--muted)}ol.sources a{color:var(--accent)}
.next{display:flex;flex-direction:column;align-items:flex-start;gap:8px}
.deeper{font:inherit;font-weight:600;border:0;background:var(--accent);color:var(--on-accent);border-radius:20px;padding:9px 18px;cursor:pointer}
.chip{border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:18px;padding:7px 14px;font:inherit;font-size:14px;cursor:pointer;text-align:left}
.chip:hover{background:var(--tint);border-color:var(--accent)}
button[disabled]:not([aria-current]){opacity:.55;cursor:default}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
"""

# Every [data-q] button asks its question once; then all of them lock so one click = one turn.
_SCRIPT = """
document.querySelectorAll('[data-q]').forEach(function(b){b.addEventListener('click',function(){
window.parent.postMessage({type:'a2ui_action',action:ACTION,data:JSON.parse(b.dataset.ctx)},'*');
document.querySelectorAll('[data-q]').forEach(function(x){x.disabled=true;});b.textContent='Asked: '+b.dataset.q;});});
"""


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def level_prompt(level: str, question: str) -> str:
    """What the user 'says' when they pick a level, e.g. "Explain it like I'm 10: Why is the sky blue?"."""
    return f"{LEVELS[level][1]}: {question}"


def _ask(cls: str, label: str, prompt: str, **context) -> str:
    """A button that sends `prompt` (plus optional context) back to the agent as an ask action."""
    ctx = json.dumps({"prompt": prompt, **context})
    return f'<button class="{cls}" data-q="{_esc(prompt)}" data-ctx="{_esc(ctx)}">{_esc(label)}</button>'


def _ladder(level: str, question: str) -> str:
    items = []
    for key in LEVEL_KEYS:
        if key == level:
            items.append(f'<button aria-current="true" disabled>{LEVELS[key][0]}</button>')
        else:
            items.append(_ask("", LEVELS[key][0], level_prompt(key, question), level=key, question=question))
    return f'<nav class="ladder" aria-label="Explanation level">{"".join(items)}</nav>'


def page(e: Explanation, sources: list[dict], question: str, level: str = "eli5") -> str:
    tags = "".join(f'<span class="tag">{_esc(t)}</span>' for t in e.tags[:3])
    fact = (f'<div class="fact"><span class="v">{_esc(e.key_fact.value)}</span><span class="l">{_esc(e.key_fact.label)}</span></div>'
            if e.key_fact and e.key_fact.value else "")
    viz = visuals.render(e.diagram, e.title)
    picture = f'<h2>The picture</h2>{viz}<p class="caption">{_esc(e.diagram.caption)}</p>' if viz else ""
    source_list = "".join(
        f'<li><a href="{_esc(s["uri"])}" target="_blank" rel="noopener">{_esc(s["title"])}</a></li>' for s in sources
    )
    sources_html = f'<h2>Sources</h2><ol class="sources">{source_list}</ol>' if sources else ""
    idx = LEVEL_KEYS.index(level)
    deeper = ""
    if idx + 1 < len(LEVEL_KEYS):
        nxt = LEVEL_KEYS[idx + 1]
        deeper = _ask("deeper", f"Go deeper: {LEVELS[nxt][1]} →", level_prompt(nxt, question), level=nxt, question=question)
    chips = "".join(_ask("chip", q, q) for q in e.follow_ups[:3])
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{_esc(e.title)}</title><style>{_STYLE}{visuals.CSS}</style></head><body>"
        f'<div class="tags">{tags}<span class="conf {e.confidence}">{e.confidence.capitalize()} confidence</span></div>'
        f'<h1>{_esc(e.title)}</h1><p class="lede">{_esc(e.one_liner)}</p>{_ladder(level, question)}'
        f'<div class="analogy"><span class="bulb" aria-hidden="true">\U0001F4A1</span><div><b>Think of it like</b>{_esc(e.analogy)}</div></div>'
        f'<p class="body">{_esc(e.body)}</p>{fact}{picture}{sources_html}'
        f'<h2>Keep going</h2><div class="next">{deeper}{chips}</div>'
        f"<script>var ACTION={json.dumps(ASK_ACTION)};{_SCRIPT}</script></body></html>"
    )
