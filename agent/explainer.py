"""The explainer page shown in IFrameSrcdoc: one level, a level ladder, the picture, sources and
follow-up chips, in KPMG branding (KPMG Blue, Arial, logo header, nothing under 14px).

One self-contained HTML document (inline CSS/JS; the frame enforces connect-src 'none').
Proven in GE by the step 0 probe: JS runs in the frame, and a postMessage
{type: 'a2ui_action', action, data} reaches the agent as a v0.9 action whose context is `data`.
GE shows context.prompt as the user's turn, so every button sends what the user would type.
"""
import base64
import html
import json
import pathlib

from . import visuals
from .schema import LEVEL_KEYS, LEVELS, Explanation

ASK_ACTION = "ask"

_LOGO = base64.b64encode((pathlib.Path(__file__).parent / "assets" / "kpmg_logo.png").read_bytes()).decode()
_BRAND_BAR = (f'<header class="brandbar"><img src="data:image/png;base64,{_LOGO}" alt="KPMG">'
              '<span>Explain like I\'m 5</span></header>')
_LEGAL = ('<footer class="legal">\u00a9 2026 KPMG International Cooperative ("KPMG International"), a Swiss entity. '
          "All rights reserved.</footer>")

_STYLE = """
:root{--bg:#fff;--ink:#333333;--muted:#555555;--line:#E0E0E0;--panel:#F5F5F5;--brand:#00338D;--accent:#005EB8;--on-accent:#fff;
--tint:#E6EBF4;--callout:#00338D;--on-callout:#fff;--high:#00A3A1;--medium:#0091DA;--low:#6D2077}
@media (prefers-color-scheme:dark){:root{--bg:#1a1f2b;--ink:#F5F5F5;--muted:#C8CDD6;--line:#3a4252;--panel:#232a38;--brand:#0091DA;
--accent:#0091DA;--on-accent:#fff;--tint:#1f2a44;--callout:#005EB8;--on-callout:#fff}}
*{box-sizing:border-box}html{color-scheme:light dark}
body{margin:0;padding:0 20px 20px;font:15px/1.6 Arial,"Helvetica Neue",Helvetica,sans-serif;background:var(--bg);color:var(--ink)}
.brandbar{display:flex;align-items:center;gap:12px;padding:14px 0 10px;margin-bottom:14px;border-bottom:2px solid #00338D}
.brandbar img{height:28px;width:auto;display:block;background:#fff;border-radius:4px;padding:2px 4px}
.brandbar span{font-size:14px;color:var(--muted);letter-spacing:.02em}
.tags{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px}
.tag{font-size:14px;color:var(--brand);background:var(--tint);border-radius:4px;padding:1px 8px}
.conf{font-size:14px;border-radius:4px;padding:1px 8px;font-weight:700;color:#fff}
.conf.high{background:var(--high)}.conf.medium{background:var(--medium)}.conf.low{background:var(--low)}
h1{font-size:24px;line-height:1.25;margin:0 0 6px;color:var(--brand)}.lede{color:var(--muted);margin:0 0 16px}
h2{font-size:16px;font-weight:700;color:var(--accent);margin:26px 0 10px;padding-bottom:4px;border-bottom:2px solid var(--accent)}
.ladder{display:flex;width:100%;margin:0 0 18px;border:1px solid var(--brand);border-radius:6px;overflow:hidden}
.ladder button{flex:1 1 0;font:inherit;font-size:14px;font-weight:700;border:0;border-left:1px solid var(--brand);background:var(--bg);
color:var(--brand);padding:8px 4px;cursor:pointer;text-align:center}
.ladder button:first-child{border-left:0}
.ladder button:hover{background:var(--tint)}
.ladder button[aria-current]{background:var(--brand);color:#fff;cursor:default}
.analogy{display:flex;gap:12px;align-items:flex-start;background:var(--callout);color:var(--on-callout);border-radius:6px;padding:14px 16px;margin:0 0 14px;font-size:16px;font-style:italic}
.analogy .bulb{font-size:26px;line-height:1;font-style:normal}.analogy b{display:block;font-size:14px;font-style:normal;letter-spacing:.04em;text-transform:uppercase;opacity:.85}
.body{margin:0 0 14px;font-size:16px}
.fact{display:flex;gap:14px;align-items:center;border-left:6px solid var(--accent);border-radius:4px;padding:12px 16px;background:var(--panel)}
.fact .v{font-size:30px;font-weight:700;line-height:1.1;color:var(--brand);white-space:nowrap}.fact .l{font-size:15px}
.caption{font-size:14px;color:var(--muted);margin:6px 0 0}
ol.sources{margin:0;padding-left:22px;font-size:14px;color:var(--muted)}ol.sources a{color:var(--accent)}
.next{display:flex;flex-direction:column;align-items:stretch;gap:8px}
.deeper{font:inherit;font-weight:700;border:0;background:var(--brand);color:#fff;border-radius:6px;padding:10px 18px;cursor:pointer;text-align:center}
.deeper:hover{background:var(--accent)}
.chip{border:1px solid var(--line);border-left:4px solid var(--accent);background:var(--bg);color:var(--ink);border-radius:4px;padding:8px 14px;font:inherit;font-size:15px;cursor:pointer;text-align:left}
.chip:hover{background:var(--tint)}
button[disabled]:not([aria-current]){opacity:.55;cursor:default}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.legal{margin-top:24px;padding-top:8px;border-top:1px solid var(--line);font-size:14px;color:var(--muted)}
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
        f"<title>{_esc(e.title)}</title><style>{_STYLE}{visuals.CSS}</style></head><body>{_BRAND_BAR}"
        f'<div class="tags">{tags}<span class="conf {e.confidence}">{e.confidence.capitalize()} confidence</span></div>'
        f'<h1>{_esc(e.title)}</h1><p class="lede">{_esc(e.one_liner)}</p>{_ladder(level, question)}'
        f'<div class="analogy"><span class="bulb" aria-hidden="true">\U0001F4A1</span><div><b>Think of it like</b>{_esc(e.analogy)}</div></div>'
        f'<p class="body">{_esc(e.body)}</p>{fact}{picture}{sources_html}'
        f'<h2>Keep going</h2><div class="next">{deeper}{chips}</div>{_LEGAL}'
        f"<script>var ACTION={json.dumps(ASK_ACTION)};{_SCRIPT}</script></body></html>"
    )
