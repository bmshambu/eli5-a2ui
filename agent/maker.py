"""The page for things the agent makes on request (a poster, an email, a social post or a
one-pager), in the same KPMG brand, themes and motion as the explainer page (explainer.py).

Every format is laid out as the real thing: a portrait poster, an email as it lands in the
inbox, a LinkedIn-style post with its image, a one-page flyer. Under it: the theme bar, the
email or post as plain text to copy (the frame can't write to the clipboard), quick changes
the model suggested, and buttons to turn it into the other formats. Buttons send a "create"
action, so a change edits this draft instead of starting again.
"""
import json

from . import brand, explainer
from .explainer import _accent, _emoji, _esc, _logo, _title
from .schema import KINDS, Creation

CREATE_ACTION = "create"  # change the current creation ("Make it shorter", "Turn it into an email")

MAKER_CSS = """
body.t-corporate{--a1:#00338D;--a3:#1E49E2;--ah:#ACEAFF}body.t-ai{--a1:#1E49E2;--a3:#00B8F5;--ah:#00B8F5}
body.t-ai-platform{--a1:#0A1E7A;--a3:#050B2E;--ah:#00B8F5}body.t-finance-data{--a1:#1E49E2;--a3:#76D2FF;--ah:#FFFFFF}
.stage{display:flex;justify-content:center;padding:18px 0 4px;position:relative;z-index:1}
.poster{position:relative;width:100%;max-width:520px;aspect-ratio:3/4;display:flex;flex-direction:column;color:#fff;overflow:hidden;
background:linear-gradient(160deg,var(--a1,#1E49E2),#00338D 60%,var(--a3,#7213EA));box-shadow:0 18px 50px rgba(0,0,0,.28)}
.poster.cover{min-height:0}
.poster .ph{position:relative;flex:0 0 40%;overflow:hidden}
.poster .ph .photo{position:absolute;inset:0;background-size:cover;background-position:center;opacity:1;mix-blend-mode:normal}
.poster .ph::after{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 40%,color-mix(in srgb,var(--a1,#1E49E2) 85%,transparent))}
.poster .in{position:relative;flex:1;display:flex;flex-direction:column;padding:16px 26px 0}
.poster svg.logo{position:absolute;top:16px;left:22px;z-index:2;height:28px;margin:0}
.poster h1{font-size:40px;line-height:1.05;margin:0 0 10px;max-width:none}
.poster .lede{font-size:17px;margin:0 0 12px}
.poster ul.sq li::before{background:var(--ah,#ACEAFF)}.poster ul.sq{margin:0 0 10px;font-size:15px}
.poster .big-emoji{top:calc(40% - 70px);right:22px;font-size:72px}
.facts{display:flex;flex-wrap:wrap;gap:8px 18px;margin:auto 0 0;padding:10px 0 14px;border-top:1px solid rgba(255,255,255,.35)}
.facts div{min-width:90px}.facts b{display:block;font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ah,#ACEAFF)}
.facts span{font-size:15px;font-weight:700}
.ctab{margin:0 -26px;padding:14px 26px;background:#fff;color:#00338D;font-weight:700;font-size:18px;display:flex;justify-content:space-between;gap:12px}
.ctab small{font-weight:400;font-size:12px;color:#666;align-self:center}
.mail{width:100%;max-width:640px;background:#fff;color:#1a1a1a;border:1px solid #d6dbe6;box-shadow:0 12px 36px rgba(0,0,0,.18)}
.mail .meta{padding:10px 18px;border-bottom:1px solid #e5e5e5;font-size:14px;color:#444;background:#f7f8fb}
.mail .meta div{padding:2px 0}.mail .meta b{display:inline-block;width:72px;color:#666;font-weight:400}
.mail .meta .subj{font-size:17px;font-weight:700;color:#1a1a1a}
.mail .band{background:linear-gradient(120deg,var(--a1,#1E49E2),#00338D);padding:14px 22px}.mail .band svg.logo{height:26px;margin:0}
.mail img.hero{display:block;width:100%;aspect-ratio:5/2;object-fit:cover}
.mail .copy{padding:18px 26px 8px}
.mail h1{font-family:"KPMG Bold","Arial Narrow",Arial,sans-serif;font-stretch:condensed;color:#00338D;font-size:28px;line-height:1.15;margin:4px 0 6px}
.mail .tag{color:var(--a1,#1E49E2);font-weight:700;margin:0 0 14px}
.post .blk h3{margin:8px 0 2px;font-size:15px}.post ul.sq li::before{background:#0a66c2}
.mail .blk h3{margin:14px 0 4px;color:#00338D;font-size:17px}.mail ul.sq li::before{background:var(--a1,#1E49E2)}
.mail table.dt{border-collapse:collapse;margin:8px 0 14px;font-size:14px}.mail table.dt td{padding:5px 14px 5px 0;border-bottom:1px solid #eee}
.mail table.dt td:first-child{font-weight:700;color:#00338D}
.mail .btn{display:inline-block;background:var(--a1,#1E49E2);color:#fff;font-weight:700;padding:11px 20px;margin:6px 0 16px}
.mail .sign{white-space:pre-line;margin:0 0 16px}
.mail .foot{background:#00338D;color:#ACEAFF;font-size:12px;padding:12px 26px}
.post{width:100%;max-width:560px;background:#fff;color:#1a1a1a;border:1px solid #d6dbe6;border-radius:8px;overflow:hidden;box-shadow:0 12px 36px rgba(0,0,0,.16)}
.post .who{display:flex;gap:10px;align-items:center;padding:12px 16px}
.post .av{width:46px;height:46px;border-radius:4px;background:#00338D;display:grid;place-items:center}.post .av svg{width:36px;height:auto}
.post .who b{display:block}.post .who small{color:#666}
.post .txt{padding:0 16px 8px;font-size:15px}.post .txt p{margin:0 0 10px}
.post .hash{color:#0a66c2;font-weight:700}
.post .img{position:relative;aspect-ratio:1.91/1;overflow:hidden;color:#fff;display:flex;align-items:flex-end}
.post .img .photo{position:absolute;inset:0;background-size:cover;background-position:center}
.post .img .shade{position:absolute;inset:0;background:linear-gradient(90deg,color-mix(in srgb,var(--a1,#1E49E2) 92%,transparent),transparent 75%)}
.post .img .in{position:relative;padding:18px 20px}.post .img svg.logo{height:22px;margin-bottom:10px}
.post .img h1{font-size:28px;margin:0;max-width:20ch}
.post .img .big-emoji{top:14px;right:18px;font-size:54px}
.flyer{width:100%;max-width:680px;background:var(--bg);box-shadow:0 12px 36px rgba(0,0,0,.16)}
.flyer .cover{min-height:260px}.flyer .wrap{padding:6px 24px 20px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0}
.card{background:var(--tint10);padding:14px 16px;border-top:4px solid var(--a1,var(--accent))}
.card h3{margin:0 0 6px;color:var(--brand);font-size:17px;display:flex;gap:8px;align-items:center}
.card p{margin:0 0 6px;font-size:15px}
.flyer .facts{border-top:2px solid var(--accent);color:var(--ink)}.flyer .facts b{color:var(--accent)}
.flyer .ctab{margin:12px 0 0;background:linear-gradient(120deg,var(--a1,#1E49E2),#00338D);color:#fff}.flyer .ctab small{color:#ACEAFF}
@media (max-width:560px){.grid{grid-template-columns:1fr}.poster h1{font-size:30px}}
.plain{margin:16px 0 0}.plain textarea{width:100%;min-height:150px;font:14px/1.5 Arial,sans-serif;padding:10px;border:1px solid var(--line);
background:var(--tint5);color:var(--ink);resize:vertical}
.plain .caption{margin:4px 0 0}
"""


def plain_text(c: Creation) -> str:
    """The email or post as plain text, to paste into Outlook or LinkedIn."""
    lines = []
    if c.kind == "email":
        if c.subject:
            lines += [f"Subject: {c.subject}", ""]
        if c.greeting:
            lines += [c.greeting, ""]
    for p in c.body:
        lines += [p, ""]
    for b in c.blocks:
        lines += [b.heading, b.text, *(f"- {p}" for p in b.points), ""]
    if c.points:
        lines += [*(f"- {p}" for p in c.points), ""]
    if c.details:
        lines += [*(f"{d.label}: {d.value}" for d in c.details), ""]
    if c.cta:
        lines += [c.cta, ""]
    if c.kind == "email" and c.sign_off:
        lines += [c.sign_off]
    if c.kind == "social" and c.hashtags:
        lines += [" ".join("#" + h.lstrip("#") for h in c.hashtags)]
    return "\n".join(lines).strip()


def _paras(items: list[str]) -> str:
    return "".join(f"<p>{_esc(p)}</p>" for p in items)


def _facts(c: Creation) -> str:
    rows = "".join(f"<div><b>{_esc(d.label)}</b><span>{_esc(d.value)}</span></div>" for d in c.details[:4])
    return f'<div class="facts">{rows}</div>' if rows else ""


def _big_emoji(c: Creation) -> str:
    em = _emoji(c.emoji) if c.theme == "creative" else ""
    return f'<div class="big-emoji" aria-hidden="true">{em}</div>' if em else ""


def _photo(c: Creation) -> str:
    return f'<div class="photo" style="background-image:url({brand.photo_uri(c.hero_photo)})"></div>'


def _poster(c: Creation) -> str:
    cta = f'<div class="ctab">{_esc(c.cta)}<small>KPMG. Make the Difference.</small></div>' if c.cta else ""
    return (f'<div class="poster cover"><div class="ph">{_photo(c)}<div class="sweep"></div></div>{_logo()}{_big_emoji(c)}'
            '<button class="motion" id="motion" type="button" hidden>Play motion</button>'
            f'<div class="in"><h1 class="rv0" style="--d:1">{_title(c.title)}</h1>'
            f'<p class="lede rv0" style="--d:2">{_esc(c.tagline)}</p>'
            f'<div class="rv0" style="--d:3">{explainer._bullets(c.points[:4])}</div>{_facts(c)}{cta}</div></div>')


def _blocks(c: Creation) -> str:
    return "".join(f'<div class="blk"><h3>{_esc(b.heading)}</h3><p>{_esc(b.text)}</p>{explainer._bullets(b.points)}</div>'
                   for b in c.blocks)


def _email(c: Creation) -> str:
    blocks = _blocks(c)
    details = "".join(f"<tr><td>{_esc(d.label)}</td><td>{_esc(d.value)}</td></tr>" for d in c.details)
    return ('<div class="mail">'
            f'<div class="meta"><div class="subj">{_esc(c.subject or c.title)}</div>'
            + (f'<div><b>Preview</b>{_esc(c.preheader)}</div>' if c.preheader else "") +
            f'</div><div class="band">{_logo()}</div><img class="hero" alt="" src="{brand.photo_uri(c.hero_photo)}">'
            f'<div class="copy"><h1>{_esc(c.title)}</h1><p class="tag">{_esc(c.tagline)}</p>'
            + (f"<p>{_esc(c.greeting)}</p>" if c.greeting else "") + _paras(c.body) + blocks + explainer._bullets(c.points)
            + (f'<table class="dt">{details}</table>' if details else "")
            + (f'<span class="btn">{_esc(c.cta)}</span>' if c.cta else "")
            + (f'<p class="sign">{_esc(c.sign_off)}</p>' if c.sign_off else "") +
            '</div><div class="foot">© 2026 KPMG International Cooperative ("KPMG International"), a Swiss entity. '
            'All rights reserved.</div></div>')


def _social(c: Creation) -> str:
    tags = " ".join(f'<span class="hash">#{_esc(h.lstrip("#"))}</span>' for h in c.hashtags[:5])
    return ('<div class="post"><div class="who"><div class="av">' + brand.logo_svg("white") + '</div>'
            '<div><b>KPMG</b><small>Draft post</small></div></div>'
            f'<div class="txt">{_paras(c.body)}{_blocks(c)}{explainer._bullets(c.points[:4])}'
            + (f"<p><b>{_esc(c.cta)}</b></p>" if c.cta else "") + (f"<p>{tags}</p>" if tags else "") + '</div>'
            f'<div class="img cover">{_photo(c)}<div class="shade"></div><div class="sweep"></div>{_big_emoji(c)}'
            f'<div class="in">{_logo()}<h1 class="rv0">{_title(c.title)}</h1></div></div></div>')


def _flyer(c: Creation) -> str:
    cards = "".join(
        f'<div class="card"><h3>{_emoji(b.emoji) if c.theme == "creative" else ""}{_esc(b.heading)}</h3>'
        f'<p>{_esc(b.text)}</p>{explainer._bullets(b.points)}</div>' for b in c.blocks[:4])
    cta = f'<div class="ctab">{_esc(c.cta)}<small>KPMG. Make the Difference.</small></div>' if c.cta else ""
    return (f'<div class="flyer"><header class="cover cv-poster">{_photo(c)}{_big_emoji(c)}'
            '<div class="shade"></div><div class="sweep"></div>'
            '<button class="motion" id="motion" type="button" hidden>Play motion</button>'
            f'<div class="in"><div class="rv0">{_logo()}</div><h1 class="rv0" style="--d:1">{_title(c.title)}</h1>'
            f'<p class="lede rv0" style="--d:2">{_esc(c.tagline)}</p></div></header>'
            f'<div class="wrap">{_paras(c.body)}' + (f'<div class="grid">{cards}</div>' if cards else "")
            + explainer._bullets(c.points) + _facts(c) + cta + "</div></div>")


_LAYOUTS = {"poster": _poster, "email": _email, "social": _social, "flyer": _flyer}


def turn_into(kind: str) -> str:
    """'Turn it into a poster' / 'Turn it into an email'."""
    name = KINDS[kind][0].lower()
    return f"Turn it into {'an' if name.startswith(('a', 'e', 'i')) else 'a'} {name}"


def _theme_bar(c: Creation, request: str) -> str:
    buttons = "".join(
        f'<span class="tcur" aria-current="true">{_esc(t.name[5:])}</span>' if k == c.theme else
        explainer._ask("tbtn", t.name[5:], explainer.theme_prompt(k), explainer.THEME_ACTION, theme=k, kind="create",
                       request=request)
        for k, t in brand.THEMES.items())
    return f'<div class="themes"><span class="tlab">Theme</span>{buttons}</div>'


def page(c: Creation, request: str) -> str:
    """The whole page. `request` is what the user asked for, sent back with every change."""
    plain = ""
    if c.kind in ("email", "social"):
        what = "email" if c.kind == "email" else "post"
        plain = (f'<div class="label">Copy the {what}</div><div class="plain">'
                 f'<textarea readonly onclick="this.select()">{_esc(plain_text(c))}</textarea>'
                 f'<p class="caption">Click the box and copy (Ctrl+C), then paste it into '
                 f'{"Outlook" if c.kind == "email" else "LinkedIn"}. Replace anything in [brackets] first.</p></div>')
    changes = "".join(explainer._ask("chip", i, i, CREATE_ACTION, request=request) for i in c.ideas[:3])
    others = "".join(explainer._ask("chip", turn_into(k), turn_into(k), CREATE_ACTION, request=request)
                     for k in KINDS if k != c.kind)
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{_esc(c.title)}</title><style>{explainer._STYLE}{explainer._MOTION}{explainer.THEME_CSS}"
        f"{explainer.CREATIVE_CSS}{MAKER_CSS}</style></head>"
        f'<body class="t-{c.theme}"{_accent(c)}>{"<div class=blobs aria-hidden=true><i></i><i></i></div>" if c.theme == "creative" else ""}'
        f'<main class="wrap"><div class="stage">{_LAYOUTS[c.kind](c)}</div>{_theme_bar(c, request)}{plain}'
        f'<div class="label">Change it</div><div class="next">{changes}{others}</div>'
        '<footer class="legal"><span>Draft made with KPMG brand assets. Check every [placeholder] and fact before you use it.</span>'
        '<span>KPMG. Make the Difference.</span></footer>'
        f"</main><script>var ACTION={json.dumps(CREATE_ACTION)};{explainer._SCRIPT}</script></body></html>"
    )
