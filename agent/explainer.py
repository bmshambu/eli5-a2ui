"""The explainer page shown in IFrameSrcdoc: a KPMG-branded briefing built from the 2026 brand
library in brand/extract.

Layout follows the recurring patterns in brand/extract/05-layouts/layout-patterns.md:
a Cobalt-to-KPMG-Blue cover with the white logo and a duotone photo, a KPI strip on light
blue tint panels, numbered contents, editorial sections in KPMG Blue with square bullets and
banner photos, a grey caveats panel, a glossary table, sources, and a legal footer.
Expert is the default; the "Explain it like I'm 5" follow-up uses the same template.

One self-contained HTML document (inline CSS/JS/images; the frame enforces connect-src
'none'). A postMessage {type: 'a2ui_action', action, data} reaches the agent as a v0.9 action
whose context is `data`, and GE shows context.prompt as the user's turn, so every button
sends what the user would type.
"""
import html
import json

from . import brand, visuals
from .schema import LEVELS, Explanation

ASK_ACTION = "ask"
DOC_QUESTION = "Explain this document"  # the question when a document is uploaded without one
MAX_SECTION_PHOTOS = 2  # plus the cover photo; keeps the page well under GE's per-message limit

_STYLE = """
:root{--bg:#fff;--ink:#00338D;--brand:#00338D;--muted:#666666;--line:#E5E5E5;--accent:#1E49E2;--hi:#00B8F5;
--tint5:#F3F6FF;--tint10:#E9EDFC;--tint20:#D2DBF9;--high:#00338D;--medium:#1E49E2;--low:#7213EA}
@media (prefers-color-scheme:dark){:root{--bg:#0C233C;--ink:#E9EDFC;--brand:#ACEAFF;--muted:#B2B2B2;--line:#24405e;
--accent:#76D2FF;--hi:#00B8F5;--tint5:#102c49;--tint10:#13345a;--tint20:#1b3f6b;--high:#1E49E2;--medium:#0091DA;--low:#7213EA}}
*{box-sizing:border-box}html{color-scheme:light dark}
body{margin:0;font:15px/1.6 Arial,"Helvetica Neue",Helvetica,sans-serif;background:var(--bg);color:var(--ink)}
.wrap{padding:0 22px 22px}
.cover{position:relative;color:#fff;background:linear-gradient(120deg,#1E49E2 0%,#00338D 60%,#0C233C 100%);overflow:hidden}
.cover .photo{position:absolute;inset:0;background-size:cover;background-position:center right;opacity:.55;mix-blend-mode:luminosity}
.cover .shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,51,141,.96) 0%,rgba(0,51,141,.82) 45%,rgba(30,73,226,.25) 100%)}
.cover .in{position:relative;padding:18px 22px 22px}
.cover svg.logo{height:30px;width:auto;display:block;margin-bottom:26px}
.eyebrow{font-size:14px;letter-spacing:.08em;text-transform:uppercase;color:#ACEAFF;font-weight:700}
.cover h1{font-size:30px;line-height:1.15;margin:6px 0 10px;font-weight:700;max-width:30ch}
.cover .lede{font-size:17px;line-height:1.45;color:#fff;margin:0 0 14px;max-width:46ch}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip-tag{font-size:14px;color:#fff;border:1px solid rgba(255,255,255,.55);padding:1px 9px}
.conf{font-size:14px;font-weight:700;padding:1px 9px;background:#00B8F5;color:#0C233C}
.conf.medium{background:#76D2FF}.conf.low{background:#B497FF}
.kpis{display:grid;grid-template-columns:repeat(var(--n,4),1fr);gap:10px;margin:18px 0 6px}
.kpi{background:var(--tint10);padding:14px 14px 12px;border-top:4px solid var(--k)}
.kpi .v{display:block;font-size:30px;font-weight:700;line-height:1.1;color:var(--k)}
.kpi .l{display:block;font-size:14px;color:var(--ink);margin-top:4px}
h2{font-size:22px;line-height:1.25;margin:28px 0 10px;color:var(--brand);display:flex;gap:12px;align-items:baseline}
h2 .no{font-size:30px;font-weight:700;color:var(--accent);min-width:1.4em}
.label{display:flex;align-items:center;gap:8px;font-size:15px;font-weight:700;color:var(--brand);margin:24px 0 8px;text-transform:uppercase;letter-spacing:.05em}
.label::before{content:"";width:12px;height:12px;background:var(--accent);display:inline-block}
p{margin:0 0 12px}
.summary{font-size:17px;line-height:1.55}
.analogy{border-left:6px solid var(--hi);background:var(--tint5);padding:12px 16px;margin:4px 0 12px;font-style:italic;font-size:16px}
.analogy b{display:block;font-style:normal;font-size:14px;letter-spacing:.05em;text-transform:uppercase;color:var(--accent)}
ul.sq{list-style:none;padding:0;margin:4px 0 12px}
ul.sq li{position:relative;padding-left:22px;margin:6px 0}
ul.sq li::before{content:"";position:absolute;left:0;top:.5em;width:9px;height:9px;background:var(--accent)}
.toc{display:grid;grid-template-columns:repeat(var(--cols,3),1fr);gap:2px;background:var(--brand);padding:2px;margin:6px 0}
.toc a{display:flex;gap:10px;align-items:baseline;background:#00338D;color:#fff;text-decoration:none;padding:10px 12px;font-size:14px}
.toc a b{font-size:24px;color:#ACEAFF;line-height:1}
.toc a:hover{background:#1E49E2}
@media (max-width:560px){.kpis,.toc{grid-template-columns:1fr 1fr}}
.banner{display:block;width:100%;aspect-ratio:5/2;object-fit:cover;margin:4px 0 14px}
.points{background:var(--tint5);border:1px solid var(--line);padding:6px 16px;margin:4px 0 14px}
.ref{font-size:14px;color:var(--muted);margin:-4px 0 10px;border-left:3px solid var(--hi);padding-left:8px}
.caption{font-size:14px;color:var(--muted);margin:6px 0 0}
.panel{background:var(--tint10);padding:12px 18px;margin:6px 0}
table.gloss{width:100%;border-collapse:collapse;font-size:14px;margin:6px 0}
table.gloss th{background:#00338D;color:#fff;text-align:left;padding:8px 10px}
table.gloss td{padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
table.gloss tr:nth-child(even) td{background:var(--tint5)}
table.gloss td:first-child{font-weight:700;color:var(--brand);width:32%}
ol.sources{margin:0;padding-left:22px;font-size:14px;color:var(--muted)}ol.sources a{color:var(--accent)}
.next{display:flex;flex-direction:column;gap:8px}
.primary{font:inherit;font-weight:700;border:0;background:linear-gradient(120deg,#1E49E2,#00338D);color:#fff;padding:12px 18px;cursor:pointer;text-align:left;font-size:15px}
.primary:hover{background:#1E49E2}
.chip{border:1px solid var(--line);border-left:4px solid var(--accent);background:var(--bg);color:var(--ink);padding:9px 14px;font:inherit;font-size:15px;cursor:pointer;text-align:left}
.chip:hover{background:var(--tint10)}
button[disabled]{opacity:.55;cursor:default}
button:focus-visible,a:focus-visible{outline:2px solid var(--hi);outline-offset:2px}
.legal{margin-top:26px;padding-top:8px;border-top:1px solid var(--line);font-size:14px;color:var(--muted);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
"""

# Every [data-q] button asks its question once; then all of them lock so one click = one turn.
_SCRIPT = """
document.querySelectorAll('[data-q]').forEach(function(b){b.addEventListener('click',function(){
window.parent.postMessage({type:'a2ui_action',action:ACTION,data:JSON.parse(b.dataset.ctx)},'*');
document.querySelectorAll('[data-q]').forEach(function(x){x.disabled=true;});b.textContent='Asked: '+b.dataset.q;});});
"""

_KPI_COLOURS = ("#1E49E2", "#00B8F5", "#7213EA", "#00338D")


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def level_prompt(level: str, question: str) -> str:
    """What the user 'says' when they pick a level, e.g. "Explain it like I'm 5: Why is the sky blue?"."""
    if question == DOC_QUESTION:
        return f"{DOC_QUESTION} {LEVELS[level][1][len('Explain it '):]}"  # "Explain this document like I'm 5"
    return f"{LEVELS[level][1]}: {question}"


def _ask(cls: str, label: str, prompt: str, **context) -> str:
    """A button that sends `prompt` (plus optional context) back to the agent as an ask action."""
    ctx = json.dumps({"prompt": prompt, **context})
    return f'<button class="{cls}" data-q="{_esc(prompt)}" data-ctx="{_esc(ctx)}">{_esc(label)}</button>'


def _logo() -> str:
    return brand.logo_svg("white").replace("<svg", '<svg class="logo" role="img" aria-label="KPMG"', 1)


def _cover(e: Explanation, level: str, from_document: bool = False) -> str:
    chips = "".join(f'<span class="chip-tag">{_esc(t)}</span>' for t in e.tags[:3])
    return (
        f'<header class="cover"><div class="photo" style="background-image:url({brand.photo_uri(e.hero_photo)})"></div>'
        f'<div class="shade"></div><div class="in">{_logo()}'
        f'<div class="eyebrow">{"Document explained" if from_document else "Explained"} · {LEVELS[level][0]}</div><h1>{_esc(e.title)}</h1>'
        f'<p class="lede">{_esc(e.one_liner)}</p>'
        f'<div class="chips">{chips}<span class="conf {e.confidence}">{e.confidence.capitalize()} confidence</span></div>'
        "</div></header>"
    )


def _kpis(e: Explanation) -> str:
    tiles = "".join(
        f'<div class="kpi" style="--k:{_KPI_COLOURS[i % 4]}"><span class="v">{_esc(s.value)}</span><span class="l">{_esc(s.label)}</span></div>'
        for i, s in enumerate(e.key_stats[:4])
    )
    n = min(len(e.key_stats), 4)
    return f'<div class="kpis" style="--n:{2 if n == 4 else n}">{tiles}</div>' if tiles else ""


def _bullets(items: list[str]) -> str:
    return "<ul class=\"sq\">" + "".join(f"<li>{_esc(t)}</li>" for t in items) + "</ul>" if items else ""


def _cols(n: int) -> int:
    """Contents grid columns that leave no lone card where possible."""
    return 3 if n % 3 == 0 else 2 if n % 2 == 0 else 3


def _sections(e: Explanation) -> tuple[str, str]:
    """(contents grid, section bodies). Section photos are capped and never repeat the cover."""
    used, toc, body = {e.hero_photo}, [], []
    for i, s in enumerate(e.sections, 1):
        toc.append(f'<a href="#s{i}"><b>{i:02d}</b>{_esc(s.heading)}</a>')
        photo = ""
        if s.photo and s.photo not in used and len(used) <= MAX_SECTION_PHOTOS:
            used.add(s.photo)
            photo = f'<img class="banner" alt="" src="{brand.photo_uri(s.photo)}">'
        paras = "".join(f"<p>{_esc(p)}</p>" for p in s.paragraphs)
        points = f'<div class="points">{_bullets(s.points[:4])}</div>' if s.points else ""
        body.append(f'<section id="s{i}"><h2><span class="no">{i:02d}</span>{_esc(s.heading)}</h2>'
                    + (f'<div class="ref">From the document: {_esc(s.doc_ref)}</div>' if s.doc_ref else "") +
                    f"{photo}{paras}{visuals.render(s.diagram, e.title)}{points}</section>")
    contents = f'<div class="label">Contents</div><nav class="toc" style="--cols:{_cols(len(toc))}">{"".join(toc)}</nav>' if len(toc) > 1 else ""
    return contents, "".join(body)


def page(e: Explanation, sources: list[dict], question: str, level: str = "expert", documents: list[str] = ()) -> str:
    """The whole page. `documents` names the uploaded files the explanation is based on."""
    contents, sections = _sections(e)
    analogy = f'<div class="analogy"><b>Think of it like</b>{_esc(e.analogy)}</div>' if e.analogy else ""
    caveats = (f'<div class="label">Caveats and open questions</div><div class="panel">{_bullets(e.caveats)}</div>'
               if e.caveats else "")
    gloss = "".join(f"<tr><td>{_esc(t.term)}</td><td>{_esc(t.definition)}</td></tr>" for t in e.glossary)
    glossary = (f'<div class="label">Glossary</div><table class="gloss"><tr><th>Term</th><th>Meaning</th></tr>{gloss}</table>'
                if gloss else "")
    source_list = "".join(
        f'<li><a href="{_esc(s["uri"])}" target="_blank" rel="noopener">{_esc(s["title"])}</a></li>' for s in sources
    )
    sources_html = f'<div class="label">Sources</div><ol class="sources">{source_list}</ol>' if sources else ""
    if documents:
        names = "".join(f"<li>{_esc(n)}</li>" for n in documents)
        sources_html = (f'<div class="label">Based on your document</div><ol class="sources">{names}</ol>'
                        '<p class="caption">Explained from the document only, without web search.</p>' + sources_html)
    other = "eli5" if level == "expert" else "expert"
    switch = _ask("primary", f"{LEVELS[other][1]} →", level_prompt(other, question), level=other, question=question)
    chips = "".join(_ask("chip", q, q) for q in e.follow_ups[:3])
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{_esc(e.title)}</title><style>{_STYLE}{visuals.CSS}</style></head><body>"
        f'{_cover(e, level, bool(documents))}<main class="wrap">{_kpis(e)}'
        f'<div class="label">At a glance</div><p class="summary">{_esc(e.summary)}</p>{analogy}'
        f'{_bullets(e.takeaways)}{contents}{sections}{caveats}{glossary}{sources_html}'
        f'<div class="label">Keep going</div><div class="next">{switch}{chips}</div>'
        '<footer class="legal"><span>© 2026 KPMG International Cooperative ("KPMG International"), a Swiss entity. '
        'All rights reserved.</span><span>KPMG. Make the Difference.</span></footer>'
        f"</main><script>var ACTION={json.dumps(ASK_ACTION)};{_SCRIPT}</script></body></html>"
    )
