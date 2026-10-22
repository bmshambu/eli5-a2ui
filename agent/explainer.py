"""The explainer page shown in IFrameSrcdoc: a KPMG-branded briefing built from the 2026 brand
library in brand/extract.

Layout follows the recurring patterns in brand/extract/05-layouts/layout-patterns.md:
a Cobalt-to-KPMG-Blue cover with the white logo and a duotone photo, a KPI strip on light
blue tint panels, numbered contents, editorial sections in KPMG Blue with square bullets and
banner photos, a grey caveats panel, a glossary table, sources, and a legal footer.
Expert is the default; the "Explain it in a simpler way" follow-up uses the same template.

One self-contained HTML document (inline CSS/JS/images; the frame enforces connect-src
'none'). A postMessage {type: 'a2ui_action', action, data} reaches the agent as a v0.9 action
whose context is `data`, and GE shows context.prompt as the user's turn, so every button
sends what the user would type.
"""
import html
import json

from . import brand, charts, visuals
from .schema import LEVELS, Explanation

ASK_ACTION = "ask"
THEME_ACTION = "theme"  # re-show the same explanation in another KPMG theme (no new model call)
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
.cover h1,h2{font-family:"KPMG Bold","Arial Narrow","Helvetica Neue Condensed",Arial,sans-serif;font-stretch:condensed}
.cover h1{font-size:30px;line-height:1.15;margin:6px 0 10px;font-weight:700;max-width:30ch}
.cover .lede{font-size:17px;line-height:1.45;color:#fff;margin:0 0 14px;max-width:46ch}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip-tag{font-size:14px;color:#fff;border:1px solid rgba(255,255,255,.55);padding:1px 9px}
.conf{font-size:14px;font-weight:700;padding:1px 9px;background:#00B8F5;color:#0C233C}
.conf.medium{background:#76D2FF}.conf.low{background:#B497FF}
.kpis{display:grid;grid-template-columns:repeat(var(--n,4),1fr);gap:10px;margin:18px 0 6px}
.kpi{background:var(--tint10);padding:14px 14px 12px;border-top:4px solid var(--k)}
.kpi .ic{display:block;color:var(--k);margin-bottom:6px}.kpi .ic svg{height:40px;width:auto;display:block}
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
# GE's frame blocks printing and downloads, so the PDF is built by the agent (pdf.py) from the
# "Download PDF" button under the frame, not from the page.
# Motion poster: the cover photo drifts (slow zoom and pan), brand frames float, a light sweep
# crosses it, and the cover text reveals line by line. Further down, KPI numbers count up and
# sections, diagrams and charts animate as they scroll into view. Everything is CSS transforms
# and opacity (cheap, no video, nothing to download). Without JS the page shows fully; with
# "reduce motion" it keeps only gentle fades (no zoom, drift or sliding).
_MOTION = """
.cover{min-height:300px}
.cover .photo{animation:kb 26s ease-in-out infinite alternate;transform-origin:70% 40%}
@keyframes kb{from{transform:scale(1.02) translate(0,0)}to{transform:scale(1.16) translate(-3%,-2%)}}
.cover .frames{position:absolute;inset:0;pointer-events:none}
.cover .frames i{position:absolute;border:2px solid rgba(172,234,255,.35);animation:drift 18s ease-in-out infinite alternate}
.cover .frames i:nth-child(1){width:150px;height:150px;right:6%;top:14%}
.cover .frames i:nth-child(2){width:90px;height:90px;right:22%;top:52%;border-color:rgba(255,255,255,.28);animation-duration:23s;animation-delay:-6s}
.cover .frames i:nth-child(3){width:46px;height:46px;right:12%;top:70%;background:rgba(0,184,245,.25);border:0;animation-duration:15s;animation-delay:-3s}
@media (max-width:720px){.cover .frames i:nth-child(n+2){display:none}.cover .frames i:nth-child(1){width:110px;height:110px;right:-20px}}
@keyframes drift{from{transform:translate(0,0) rotate(0)}to{transform:translate(-26px,14px) rotate(8deg)}}
.cover .sweep{position:absolute;inset:0;pointer-events:none;background:linear-gradient(105deg,transparent 35%,rgba(255,255,255,.16) 50%,transparent 65%);
transform:translateX(-100%);animation:sweep 2.4s .5s ease-in-out both}
@keyframes sweep{to{transform:translateX(100%)}}
.rv0{animation:rise .7s cubic-bezier(.2,.7,.2,1) both;animation-delay:calc(var(--d,0) * 140ms + 150ms)}
@keyframes rise{from{opacity:0;transform:translateY(18px)}}
.js .rv{opacity:0;transform:translateY(22px);transition:opacity .7s ease-out,transform .7s cubic-bezier(.2,.7,.2,1)}
.js .rv.in{opacity:1;transform:none}
.js figure:not(.in) .pop,.js figure:not(.in) .fill,.js figure:not(.in) circle,.js figure:not(.in) .line svg{animation-play-state:paused}
.donut circle{animation:ring 1.1s ease-out both}@keyframes ring{from{stroke-dasharray:0 400}}
.line svg{animation:wipe 1.3s ease-out both}@keyframes wipe{from{clip-path:inset(0 100% 0 0)}}
.kpi{transition:transform .2s}.kpi:hover{transform:translateY(-3px)}
.js .cover:not(.go) .rv0,.js .cover:not(.go) .sweep{animation-play-state:paused}
@media (prefers-reduced-motion:reduce){html:not(.motion-on) .cover .photo,html:not(.motion-on) .cover .frames i,
html:not(.motion-on) .donut circle,html:not(.motion-on) .line svg{animation:none!important}
html:not(.motion-on) .cover .sweep{display:none}html:not(.motion-on) .rv0{animation-name:fadein}
html:not(.motion-on) .js .rv,html.js:not(.motion-on) .rv{transform:none;transition:opacity .8s ease-out}}
.themes{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:14px 0 0;font-size:14px}
.themes .tlab{font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-right:4px}
.themes .tbtn,.themes .tcur{font:inherit;font-size:14px;padding:4px 12px;border:1px solid var(--accent);background:transparent;color:var(--ink);cursor:pointer}
.themes .tbtn:hover{background:var(--tint10)}.themes .tcur{background:var(--accent);color:#fff;font-weight:700;cursor:default}
.t-ai .themes .tbtn,.t-ai .themes .tcur{border-radius:999px}.t-ai .themes .tcur{color:#00338D}
.motion{position:absolute;z-index:3;top:16px;right:18px;font:inherit;font-size:14px;font-weight:700;color:#fff;cursor:pointer;
background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.6);padding:6px 12px}.motion:hover{background:rgba(255,255,255,.25)}
@keyframes fadein{from{opacity:0}}
"""

# The four KPMG theme recipes (brand/extract/08-themes). Corporate is the base style above; the
# others adjust it. The body carries the class t-<theme>.
THEME_CSS = """
.cover h1 .hl{color:#ACEAFF}
body.t-ai{--bg:#1534C4;--ink:#FFFFFF;--brand:#FFFFFF;--muted:#ACEAFF;--line:rgba(172,234,255,.28);--accent:#00B8F5;--hi:#B497FF;
--tint5:rgba(5,11,46,.28);--tint10:rgba(5,11,46,.38);--tint20:rgba(255,255,255,.12);
--c0:#00B8F5;--c1:#76D2FF;--c2:#B497FF;--c3:#7213EA;--c4:#ACEAFF;color-scheme:dark;min-height:100vh;
background:radial-gradient(ellipse at 85% 0%,rgba(0,184,245,.22),transparent 45%),linear-gradient(180deg,#1E49E2 0%,#1534C4 35%,#0C1C8C 75%,#050B2E 100%)}
.t-ai .cover{background:linear-gradient(120deg,#1E49E2,#0A1E7A)}
.t-ai .cover .photo,.t-ai-platform .cover .photo,.t-finance-data .cover .photo{mix-blend-mode:normal;opacity:.95}
.t-ai .cover .shade{background:linear-gradient(90deg,rgba(30,73,226,.97) 0%,rgba(30,73,226,.82) 42%,rgba(30,73,226,.05) 100%)}
.t-ai .eyebrow,.t-ai-platform .eyebrow{color:#00B8F5}
.t-ai .cover h1 .hl,.t-ai-platform .cover h1 .hl{color:#00B8F5}
.t-ai .kpi{background:rgba(5,11,46,.38);border:1px solid rgba(0,184,245,.55);box-shadow:0 0 18px rgba(0,184,245,.22)}
.t-ai .kpi .v{color:#00B8F5;text-shadow:0 0 14px rgba(0,184,245,.55)}.t-ai .kpi .ic{color:#76D2FF}
.t-ai .points,.t-ai .panel,.t-ai .chart,.t-ai .analogy{background:rgba(5,11,46,.32);border:1px solid rgba(0,184,245,.5);box-shadow:0 0 16px rgba(0,184,245,.15)}
.t-ai .toc a{background:rgba(5,11,46,.45);border:1px solid rgba(0,184,245,.35)}.t-ai .toc{background:transparent}
.t-ai .primary{background:#00B8F5;color:#00338D;border-radius:999px}.t-ai .chip{border-radius:999px;border:1px solid #00B8F5;background:transparent}
.t-ai .conf{border-radius:999px}.t-ai table.gloss th{background:rgba(0,184,245,.25)}
.t-ai-platform .cover{background:linear-gradient(90deg,#050B2E,#0A1E7A)}
.t-ai-platform .cover .shade{background:linear-gradient(90deg,#050B2E 0%,rgba(5,11,46,.9) 42%,rgba(10,30,122,.12) 100%)}
.t-ai-platform .g0{--c:#D2DBF9}.t-ai-platform .g1{--c:#76D2FF}.t-ai-platform .g2{--c:#00B8F5}.t-ai-platform .g3,.t-ai-platform .g4{--c:#1E49E2}
.t-ai-platform .g0 .head,.t-ai-platform .g1 .head,.t-ai-platform .g0.hd,.t-ai-platform .g1.hd{color:#00338D}
.t-ai-platform .toc a{background:#050B2E}.t-ai-platform .toc{background:#050B2E}
.t-ai-platform .kpi{border-top-color:#1E49E2}
.t-finance-data .cover{background:linear-gradient(115deg,#1E49E2 0%,#1E49E2 55%,#76D2FF 100%)}
.t-finance-data .cover .shade{background:linear-gradient(90deg,rgba(30,73,226,.98) 0%,rgba(30,73,226,.86) 48%,rgba(30,73,226,0) 100%)}
.cstats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:14px;margin:4px 0 16px;max-width:620px}
.cstats div{border-top:3px solid #00B8F5;padding-top:8px}
.cstats .v{display:block;font-family:"KPMG Bold","Arial Narrow","Helvetica Neue Condensed",Arial,sans-serif;font-stretch:condensed;
font-size:32px;font-weight:700;line-height:1.1;color:#fff}
.cstats .l{display:block;font-size:14px;color:#ACEAFF;margin-top:2px}
.tabs{display:grid;grid-template-columns:1fr 1fr 1fr;height:6px}.tabs i:nth-child(1){background:#00B8F5}.tabs i:nth-child(2){background:#7213EA}.tabs i:nth-child(3){background:#76D2FF}
.t-finance-data h2{color:var(--fin-title,#1E49E2)}
.t-finance-data .chart{background:var(--tint5);border-color:var(--tint20)}
.t-finance-data .bars.one .fill{--s:#00B8F5!important}.t-finance-data .bars.one .grp:last-child .fill{--s:var(--fin-latest,#00338D)!important}
.t-finance-data table.gloss th{background:transparent;color:var(--brand);border-bottom:3px solid var(--brand)}
@media (prefers-color-scheme:dark){.t-finance-data{--fin-title:#76D2FF;--fin-latest:#ACEAFF}}
"""

_SCRIPT = """
(function(){document.documentElement.classList.add('js');
function count(el){var m=/^([^0-9]*)([0-9][0-9,]*(?:\\.[0-9]+)?)(.*)$/.exec(el.textContent);if(!m||el.dataset.counted)return;el.dataset.counted=1;
var end=parseFloat(m[2].replace(/,/g,'')),dp=(m[2].split('.')[1]||'').length,comma=m[2].indexOf(',')>=0,t0=null;
if(!dp&&!comma&&end>=1900&&end<=2100)return;
function f(v){var s=v.toFixed(dp);return comma?s.replace(/\\B(?=(\\d{3})+(?!\\d))/g,','):s;}
function step(t){t0=t0||t;var k=Math.min((t-t0)/1200,1);el.textContent=m[1]+f(end*(1-Math.pow(1-k,3)))+m[3];
if(k<1)requestAnimationFrame(step);}requestAnimationFrame(step);}
var items=document.querySelectorAll('section,figure,.kpis,.panel,table.gloss,.analogy,.points,.next');
items.forEach(function(x){x.classList.add('rv');});
function show(x){x.classList.add('in');x.querySelectorAll('figure').forEach(function(f){f.classList.add('in');});
if(x.classList.contains('kpis'))x.querySelectorAll('.v').forEach(count);}
// The cover intro starts when the cover is actually on screen (the panel may open after the
// page loads), with a fallback so it never stays paused.
var cover=document.querySelector('.cover');
function go(){if(!cover||cover.classList.contains('go'))return;cover.classList.add('go');
setTimeout(function(){document.querySelectorAll('.cstats .v').forEach(count);},700);}
setTimeout(go,2500);
// Windows "Animation effects" off makes the browser ask for reduced motion, so the cover stays
// still by default; this button lets the viewer turn the motion poster on anyway.
var mb=document.getElementById('motion');
if(mb&&window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches){mb.hidden=false;
mb.addEventListener('click',function(){var on=document.documentElement.classList.toggle('motion-on');
mb.textContent=on?'Stop motion':'Play motion';if(on&&cover){cover.classList.remove('go');void cover.offsetWidth;
cover.querySelectorAll('.rv0,.sweep').forEach(function(x){x.style.animation='none';void x.offsetWidth;x.style.animation='';});
cover.classList.add('go');}});}
if(!('IntersectionObserver' in window)){go();items.forEach(show);}else{
var io=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;
if(e.target===cover)go();else show(e.target);io.unobserve(e.target);});},{threshold:.15});
if(cover)io.observe(cover);items.forEach(function(x){io.observe(x);});}})();
document.querySelectorAll('[data-q]').forEach(function(b){b.addEventListener('click',function(){
window.parent.postMessage({type:'a2ui_action',action:b.dataset.action||ACTION,data:JSON.parse(b.dataset.ctx)},'*');
document.querySelectorAll('[data-q]').forEach(function(x){x.disabled=true;});b.textContent='Asked: '+b.dataset.q;});});
"""

_KPI_COLOURS = ("#1E49E2", "#00B8F5", "#7213EA", "#00338D")


def _esc(text: str) -> str:
    return html.escape(text or "", quote=True)


def level_prompt(level: str, question: str) -> str:
    """What the user 'says' when they pick a level, e.g. "Explain it in a simpler way: Why is the sky blue?"."""
    if question == DOC_QUESTION:
        return f"{DOC_QUESTION} {LEVELS[level][1][len('Explain it '):]}"  # "Explain this document in a simpler way"
    return f"{LEVELS[level][1]}: {question}"


def _ask(cls: str, label: str, prompt: str, action: str = "", **context) -> str:
    """A button that sends `prompt` (plus optional context) back to the agent as an ask action,
    or as `action` when given."""
    ctx = json.dumps({"prompt": prompt, **context})
    act = f' data-action="{_esc(action)}"' if action else ""
    return f'<button class="{cls}" data-q="{_esc(prompt)}" data-ctx="{_esc(ctx)}"{act}>{_esc(label)}</button>'


def theme_prompt(theme: str) -> str:
    return f"Show this in the {brand.THEMES[theme].name} theme"


def _theme_bar(e: Explanation, question: str, level: str) -> str:
    """Buttons that re-show this explanation in each of the other KPMG themes."""
    buttons = "".join(
        f'<span class="tcur" aria-current="true">{_esc(t.name[5:])}</span>' if k == e.theme else
        _ask("tbtn", t.name[5:], theme_prompt(k), THEME_ACTION, theme=k, question=question, level=level)
        for k, t in brand.THEMES.items())
    return f'<div class="themes"><span class="tlab">Theme</span>{buttons}</div>'


def _logo() -> str:
    return brand.logo_svg("white").replace("<svg", '<svg class="logo" role="img" aria-label="KPMG"', 1)


def _title(title: str) -> str:
    """The title with its last words marked, for the themes' two-tone cover headline."""
    words = title.split()
    if len(words) < 3:
        return _esc(title)
    k = 2 if len(words) > 4 else 1
    return f'{_esc(" ".join(words[:-k]))} <span class="hl">{_esc(" ".join(words[-k:]))}</span>'


def _cover_stats(e: Explanation) -> str:
    """Finance Data puts up to three headline figures on the cover."""
    stats = "".join(f'<div><span class="v">{_esc(s.value)}</span><span class="l">{_esc(s.label)}</span></div>'
                    for s in e.key_stats[:3])
    return f'<div class="cstats rv0" style="--d:4">{stats}</div>' if stats else ""


def _cover(e: Explanation, level: str, from_document: bool = False) -> str:
    chips = "".join(f'<span class="chip-tag">{_esc(t)}</span>' for t in e.tags[:3])
    finance = e.theme == "finance-data"
    return (
        f'<header class="cover"><div class="photo" style="background-image:url({brand.photo_uri(e.hero_photo)})"></div>'
        '<div class="shade"></div><div class="frames" aria-hidden="true"><i></i><i></i><i></i></div><div class="sweep"></div>'
        '<button class="motion" id="motion" type="button" hidden>Play motion</button>'
        f'<div class="in"><div class="rv0">{_logo()}</div>'
        f'<div class="eyebrow rv0" style="--d:1">{"Document explained" if from_document else "Explained"} · {LEVELS[level][0]}</div><h1 class="rv0" style="--d:2">{_title(e.title)}</h1>'
        f'<p class="lede rv0" style="--d:3">{_esc(e.one_liner)}</p>{_cover_stats(e) if finance else ""}'
        f'<div class="chips rv0" style="--d:{5 if finance else 4}">{chips}<span class="conf {e.confidence}">{e.confidence.capitalize()} confidence</span></div>'
        "</div></header>" + ('<div class="tabs" aria-hidden="true"><i></i><i></i><i></i></div>' if finance else "")
    )


def _kpis(e: Explanation) -> str:
    tiles = "".join(
        f'<div class="kpi" style="--k:{_KPI_COLOURS[i % 4]}">'
        + (f'<span class="ic" aria-hidden="true">{brand.icon_svg(s.icon)}</span>' if s.icon else "")
        + f'<span class="v">{_esc(s.value)}</span><span class="l">{_esc(s.label)}</span></div>'
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
                    f"{photo}{paras}{charts.render(s.chart)}{visuals.render(s.diagram, e.title)}{points}</section>")
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
        f"<title>{_esc(e.title)}</title><style>{_STYLE}{visuals.CSS}{charts.CSS}{_MOTION}{THEME_CSS}</style></head>"
        f'<body class="t-{e.theme}">'
        f'{_cover(e, level, bool(documents))}'
        f'<main class="wrap">{_theme_bar(e, question, level)}{_kpis(e.model_copy(update={"key_stats": e.key_stats[3:]})) if e.theme == "finance-data" else _kpis(e)}'
        f'<div class="label">At a glance</div><p class="summary">{_esc(e.summary)}</p>{analogy}'
        f'{_bullets(e.takeaways)}{contents}{sections}{caveats}{glossary}{sources_html}'
        f'<div class="label next-label">Keep going</div><div class="next">{switch}{chips}</div>'
        '<footer class="legal"><span>© 2026 KPMG International Cooperative ("KPMG International"), a Swiss entity. '
        'All rights reserved.</span><span>KPMG. Make the Difference.</span></footer>'
        f"</main><script>var ACTION={json.dumps(ASK_ACTION)};{_SCRIPT}</script></body></html>"
    )
