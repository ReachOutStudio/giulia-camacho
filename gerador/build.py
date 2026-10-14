"""Gera o site estático da Giulia Camacho a partir do conteúdo publicado no Sanity.

Uso:
  python3 gerador/build.py dist        gera o site na pasta dist/
  python3 gerador/build.py --check     escreve mudou=true/false em $GITHUB_OUTPUT

Variáveis de ambiente:
  SITE_URL           endereço público, terminando em "/" (padrão: GitHub Pages)
  SANITY_PROJECT_ID  padrão 9ybkssyz
  SANITY_DATASET     padrão production
Só usa a biblioteca padrão do Python.
"""
import hashlib
import html
import json
import os
import pathlib
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
SITE_URL = os.environ.get("SITE_URL", "https://reachoutstudio.github.io/giulia-camacho/")
assert SITE_URL.endswith("/")
BASE_PATH = urllib.parse.urlparse(SITE_URL).path
PROJECT = os.environ.get("SANITY_PROJECT_ID", "9ybkssyz")
DATASET = os.environ.get("SANITY_DATASET", "production")
API = f"https://{PROJECT}.api.sanity.io/v2025-02-19/data/query/{DATASET}"

e = html.escape
LANGS = ("pt", "en")

ASSET = "asset->{_id, url, metadata{dimensions{width, height}, palette{dominant{background}}}}"
QUERY = f"""{{
  "series": *[_type == "serie" && defined(slug.current)] | order(grupo asc, ordem asc, nome asc){{
    nome, "slug": slug.current, grupo, lugar, texto, creditos,
    "capa": capa{{{ASSET}}},
    "fotos": fotos[]{{{ASSET}}}
  }},
  "inicio": *[_id == "inicio"][0]{{ destaques[]{{ "foto": foto{{{ASSET}}}, "serie": serie->slug.current }} }},
  "sobre": *[_id == "sobre"][0]{{ "retrato": retrato{{{ASSET}}}, bio, linhaDoTempo }},
  "config": *[_id == "configuracoes"][0]{{ email, whatsapp, instagram, base, contatoTexto, descricao }},
  "atualizado": *[!(_id in path("drafts.**")) && _type in ["serie", "inicio", "sobre", "configuracoes"]] | order(_updatedAt desc)[0]._updatedAt
}}"""

# Textos fixos da interface. Os textos de conteúdo vêm do Sanity.
T = dict(
    pt=dict(
        editorial="Editorial", lifestyle="Lifestyle", sobre="Sobre", contato="Contato",
        base="São Paulo · Londres", menu="Menu", close="Fechar", prev="Anterior", nextPhoto="Próxima", of="de",
        photos="fotos", next="Próxima série", back="Voltar para", credit="Fotografia Giulia Camacho",
        editorialLede="Retratos editoriais feitos na rua, com a cidade como cenário.",
        lifestyleLede="Famílias e casais, em casa e ao ar livre, com luz natural.",
        work="Trabalhos", portraitAlt="Retrato de Giulia Camacho",
        contactLede="Baseada em São Paulo. Disponível para trabalhos em Londres.",
        email="E-mail", whatsapp="WhatsApp", instagram="Instagram", copy="Copiar", copied="Copiado",
        copyFail="Selecionado. Use Cmd+C ou Ctrl+C para copiar.",
        fName="Nome", fEmail="Seu e-mail", fType="Tipo de trabalho", fDate="Data desejada", fMsg="Mensagem", fSend="Enviar por e-mail",
        types=["Editorial", "Marca ou campanha", "Retrato", "Família", "Casal", "Outro"],
        sent="Abrimos o seu app de e-mail com a mensagem pronta. Se nada abriu, escreva para {email}.",
        required="Preencha nome, e-mail e mensagem.", subject="Contato pelo site",
        whatsappCta="Conversar no WhatsApp",
        desc="Giulia Camacho é fotógrafa brasileira de editorial e lifestyle.",
        notFound="Página não encontrada", notFoundText="O endereço pode ter mudado. Volte para o início ou veja as séries.",
        home="Início", skip="Pular para o conteúdo", homeTitle="Fotografia editorial e lifestyle",
    ),
    en=dict(
        editorial="Editorial", lifestyle="Lifestyle", sobre="About", contato="Contact",
        base="São Paulo · London", menu="Menu", close="Close", prev="Previous", nextPhoto="Next", of="of",
        photos="photos", next="Next series", back="Back to", credit="Photography Giulia Camacho",
        editorialLede="Editorial portraits made on the street, with the city as the set.",
        lifestyleLede="Families and couples, at home and outdoors, in natural light.",
        work="Work", portraitAlt="Portrait of Giulia Camacho",
        contactLede="Based in São Paulo. Available for work in London.",
        email="Email", whatsapp="WhatsApp", instagram="Instagram", copy="Copy", copied="Copied",
        copyFail="Selected. Press Cmd+C or Ctrl+C to copy.",
        fName="Name", fEmail="Your email", fType="Type of work", fDate="Preferred date", fMsg="Message", fSend="Send by email",
        types=["Editorial", "Brand or campaign", "Portrait", "Family", "Couple", "Other"],
        sent="We opened your email app with the message ready. If nothing opened, write to {email}.",
        required="Please fill in name, email and message.", subject="Enquiry from the website",
        whatsappCta="Chat on WhatsApp",
        desc="Giulia Camacho is a Brazilian editorial and lifestyle photographer.",
        notFound="Page not found", notFoundText="The address may have changed. Go back home or browse the series.",
        home="Home", skip="Skip to content", homeTitle="Editorial and lifestyle photography",
    ),
)

FIXED = dict(
    inicio=dict(pt="", en="en/"),
    editorial=dict(pt="editorial/", en="en/editorial/"),
    lifestyle=dict(pt="lifestyle/", en="en/lifestyle/"),
    sobre=dict(pt="sobre/", en="en/about/"),
    contato=dict(pt="contato/", en="en/contact/"),
)


# ---------- dados ----------

def fetch():
    if os.environ.get("SANITY_JSON"):  # teste local com uma resposta salva
        return json.loads(pathlib.Path(os.environ["SANITY_JSON"]).read_text())["result"]
    url = API + "?" + urllib.parse.urlencode({"query": QUERY, "perspective": "published"})
    req = urllib.request.Request(url, headers={"Accept-Encoding": "identity", "User-Agent": "giulia-camacho-site"})
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())["result"]
        except Exception as err:  # rede instável: tenta de novo
            last = err
            time.sleep(2 * (attempt + 1))
    raise SystemExit(f"Não consegui ler o conteúdo do Sanity: {last}")


def loc(arr, lang, fallback=""):
    """Lê um campo internationalizedArray (formato v5: language/value)."""
    if not arr:
        return fallback
    by = {(i.get("language") or i.get("_key")): i.get("value") for i in arr if i.get("value")}
    return by.get(lang) or by.get("pt") or fallback


def pic(obj):
    a = (obj or {}).get("asset") or {}
    if not a.get("url"):
        return None
    d = (a.get("metadata") or {}).get("dimensions") or {}
    pal = ((a.get("metadata") or {}).get("palette") or {}).get("dominant") or {}
    return dict(id=a["_id"], url=a["url"], w=d.get("width", 1200), h=d.get("height", 1600), avg=pal.get("background", "#d8cbb8"))


def load(raw):
    series = []
    for s in raw.get("series") or []:
        fotos = [p for p in (pic(f) for f in (s.get("fotos") or [])) if p]
        capa = pic(s.get("capa")) or (fotos[0] if fotos else None)
        if not fotos or not capa or s.get("grupo") not in ("editorial", "lifestyle"):
            continue
        series.append(dict(
            slug=s["slug"], name=s["nome"], group=s["grupo"], credits=s.get("creditos") or "",
            place={l: loc(s.get("lugar"), l) for l in LANGS},
            text={l: loc(s.get("texto"), l) for l in LANGS},
            cover=capa, photos=fotos,
        ))
    by = {s["slug"]: s for s in series}
    home = []
    for d in ((raw.get("inicio") or {}).get("destaques") or []):
        p = pic(d.get("foto"))
        if p and d.get("serie") in by:
            home.append(dict(photo=p, slug=d["serie"]))
    if not home:
        home = [dict(photo=s["cover"], slug=s["slug"]) for s in series]
    sobre = raw.get("sobre") or {}
    cfg = raw.get("config") or {}
    contact = dict(
        email=cfg.get("email") or "",
        whatsapp=cfg.get("whatsapp") or "",
        instagram=cfg.get("instagram") or "",
    )
    contact["whatsapp_link"] = "https://wa.me/" + re.sub(r"\D", "", contact["whatsapp"]) if contact["whatsapp"] else ""
    handle = contact["instagram"].lstrip("@").strip()
    contact["instagram_link"] = f"https://www.instagram.com/{handle}/" if handle else ""
    texts = {l: dict(
        base=loc(cfg.get("base"), l, T[l]["base"]),
        contactLede=loc(cfg.get("contatoTexto"), l, T[l]["contactLede"]),
        desc=loc(cfg.get("descricao"), l, T[l]["desc"]),
        bio=[p.strip() for p in re.split(r"\n\s*\n", loc(sobre.get("bio"), l)) if p.strip()],
        timeline=[(loc(x.get("lugar"), l), loc(x.get("descricao"), l)) for x in (sobre.get("linhaDoTempo") or [])],
    ) for l in LANGS}
    return dict(series=series, by=by, home=home, portrait=pic(sobre.get("retrato")), contact=contact,
                texts=texts, updated=raw.get("atualizado") or "")


# ---------- html ----------

VER = {}
C = None  # conteúdo carregado
PATHS = {}


def root_of(path):
    return "../" * path.count("/") if path else ""


def url(key, lang, root):
    return root + PATHS[key][lang]


def abs_url(key, lang):
    return SITE_URL + PATHS[key][lang]


def src(p, w):
    return f'{p["url"]}?w={w}&fm=jpg&q=75&fit=max'


SIZES_ROW = "(max-width: 560px) 100vw, (max-width: 860px) 50vw, 40vw"


def img(p, alt, sizes=SIZES_ROW, eager=False, cls=""):
    w = min(p["w"], 1400)
    h = round(p["h"] * w / p["w"])
    srcset = f'{src(p, 800)} 800w, {src(p, 1400)} {w}w' if p["w"] > 800 else f'{src(p, p["w"])} {p["w"]}w'
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} src="{src(p, 1400)}" srcset="{srcset}" sizes="{sizes}" width="{w}" height="{h}" '
            f'alt="{e(alt)}" {load} decoding="async" style="background:{p["avg"]}">')


def land(p):
    return p["w"] > p["h"] * 1.15


def rows(items, render):
    """items: lista de fotos. Fotos verticais em pares, horizontais sozinhas."""
    out, i = [], 0
    while i < len(items):
        a = items[i]
        if land(a):
            out.append([a]); i += 1; continue
        b = items[i + 1] if i + 1 < len(items) else None
        if b is not None and not land(b):
            out.append([a, b]); i += 2
        else:
            out.append([a, None]); i += 1
    html_rows, n = [], 0
    for r in out:
        cells = []
        for p in r:
            if p is None:
                ref = r[0]
                cells.append(f'<div class="cell spacer" style="flex:{ref["w"] / ref["h"]:.4f} 1 0%" aria-hidden="true"></div>')
            else:
                cells.append(f'<div class="cell" style="flex:{p["w"] / p["h"]:.4f} 1 0%">{render(p, n)}</div>')
                n += 1
        html_rows.append(f'<div class="row">{"".join(cells)}</div>')
    return "".join(html_rows), [p for r in out for p in r if p is not None]


def nav(current, lang, root):
    t = T[lang]
    cur = C["by"].get(current)
    group = cur["group"] if cur else current
    items = []
    for p in ["editorial", "lifestyle", "sobre", "contato"]:
        on = p == group
        sub = ""
        if on and p in ("editorial", "lifestyle"):
            li = []
            for s in C["series"]:
                if s["group"] != p:
                    continue
                ac = ' aria-current="page"' if cur and cur["slug"] == s["slug"] else ""
                li.append(f'<li><a href="{url(s["slug"], lang, root)}"{ac}>{e(s["name"])}</a></li>')
            sub = f'<ul class="sub">{"".join(li)}</ul>'
        ac = ' aria-current="page"' if on and not cur else ""
        cls = ' class="on"' if on else ""
        items.append(f'<li><a href="{url(p, lang, root)}"{ac}{cls}>{e(t[p])}</a>{sub}</li>')
    return f'<ul>{"".join(items)}</ul>'


def page(key, lang, title, desc, body, og=None, extra_end=""):
    path = PATHS[key][lang]
    root = root_of(path)
    t = T[lang]
    ct = C["contact"]
    og = og or (C["home"][0]["photo"] if C["home"] else None)
    og_url = f'{og["url"]}?w=1200&h=630&fit=crop&fm=jpg&q=80' if og else ""
    full_title = f"{title} · Giulia Camacho" if title else f'Giulia Camacho · {t["homeTitle"]}'
    head_ld = ""
    if key == "inicio":
        ld = {"@context": "https://schema.org", "@type": "Person", "name": "Giulia Camacho",
              "jobTitle": "Fotógrafa" if lang == "pt" else "Photographer", "url": SITE_URL,
              "address": {"@type": "PostalAddress", "addressLocality": "São Paulo", "addressCountry": "BR"}}
        if ct["email"]:
            ld["email"] = "mailto:" + ct["email"]
        if ct["instagram_link"]:
            ld["sameAs"] = [ct["instagram_link"]]
        head_ld = f'\n<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    mini = [f'<span>{e(C["texts"][lang]["base"])}</span>']
    if ct["email"]:
        mini.append(f'<a href="mailto:{e(ct["email"])}">{e(ct["email"])}</a>')
    if ct["instagram_link"]:
        mini.append(f'<a href="{e(ct["instagram_link"])}" rel="me noopener" target="_blank">{e(ct["instagram"])}</a>')
    og_tag = f'\n<meta property="og:image" content="{e(og_url)}">' if og_url else ""
    return f'''<!doctype html>
<html lang="{"pt-BR" if lang == "pt" else "en"}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(full_title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{abs_url(key, lang)}">
<link rel="alternate" hreflang="pt-BR" href="{abs_url(key, "pt")}">
<link rel="alternate" hreflang="en" href="{abs_url(key, "en")}">
<link rel="alternate" hreflang="x-default" href="{abs_url(key, "pt")}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Giulia Camacho">
<meta property="og:title" content="{e(full_title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{abs_url(key, lang)}">{og_tag}
<meta property="og:locale" content="{"pt_BR" if lang == "pt" else "en_GB"}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#EDE2D1">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://cdn.sanity.io">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Caprasimo&family=DM+Mono:wght@400;500&family=Schibsted+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="{root}assets/site.css?v={VER["css"]}">{head_ld}
</head>
<body>
<a class="skip" href="#main">{e(t["skip"])}</a>
<aside class="side">
  <div class="side-top">
    <a class="logo" href="{url("inicio", lang, root)}" aria-label="Giulia Camacho, {e(t["home"])}"><span>Giulia</span><span>Camacho</span></a>
    <button type="button" id="menu-btn" aria-expanded="false" aria-controls="nav">{e(t["menu"])}</button>
  </div>
  <nav id="nav" aria-label="Menu">{nav(key, lang, root)}</nav>
  <div class="side-foot">
    <div class="lang" role="group" aria-label="Idioma / Language"><a href="{url(key, "pt", root)}" hreflang="pt-BR" lang="pt-BR" aria-current="{str(lang == "pt").lower()}">PT</a><a href="{url(key, "en", root)}" hreflang="en" lang="en" aria-current="{str(lang == "en").lower()}">EN</a></div>
    <div class="contact-mini">{"".join(mini)}</div>
  </div>
</aside>
<main id="main" class="main" tabindex="-1">
{body}
</main>
<p class="foot-note">© 2026 Giulia Camacho</p>
{extra_end}<script src="{root}assets/site.js?v={VER["js"]}" defer></script>
</body>
</html>
'''


def page_home(lang):
    root = root_of(PATHS["inicio"][lang])
    photos = [d["photo"] for d in C["home"]]
    slugs = {id(d["photo"]): d["slug"] for d in C["home"]}

    def cell(p, n):
        s = C["by"][slugs[id(p)]]
        alt = s["name"] + (", " + s["place"][lang] if s["place"][lang] else "")
        cap = e(s["name"]) + (" · " + e(s["place"][lang]) if s["place"][lang] else "")
        return f'<a class="ph" href="{url(s["slug"], lang, root)}">{img(p, alt, eager=n < 2)}<span class="cap">{cap}</span></a>'

    grid, _ = rows(photos, cell)
    body = f'<h1 class="visually-hidden">Giulia Camacho</h1><div class="photos home">{grid}</div>'
    return page("inicio", lang, "", C["texts"][lang]["desc"], body)


def page_index(group, lang):
    root = root_of(PATHS[group][lang])
    t = T[lang]
    lst = [s for s in C["series"] if s["group"] == group]
    if not lst:
        body = f'<header class="page-head"><h1>{e(t[group])}</h1><p>{e(t[group + "Lede"])}</p></header>'
        return page(group, lang, t[group], t[group + "Lede"], body)
    items = []
    for i, s in enumerate(lst):
        cv = s["cover"]
        hot = ' class="hot"' if i == 0 else ""
        place = s["place"][lang]
        attrs = (f'data-src="{src(cv, 1400)}" data-srcset="{src(cv, 800)} 800w, {src(cv, 1400)} {min(cv["w"], 1400)}w" '
                 f'data-w="{min(cv["w"], 1400)}" data-h="{round(cv["h"] * min(cv["w"], 1400) / cv["w"])}" data-avg="{cv["avg"]}"')
        items.append(f'''<li><a href="{url(s["slug"], lang, root)}"{hot} {attrs} data-cap="{e(s["name"])}{" · " + e(place) if place else ""}">
      <span class="num">{i + 1:02d}</span><span class="nm">{e(s["name"])}</span>
      <span class="pl">{e(place) + " · " if place else ""}{len(s["photos"])} {t["photos"]}</span>
      <span class="thumb">{img(cv, s["name"], sizes="72px")}</span></a></li>''')
    first = lst[0]
    fp = first["place"][lang]
    body = f'''<div class="index">
  <div class="index-list">
    <header class="page-head"><h1>{e(t[group])}</h1><p>{e(t[group + "Lede"])}</p></header>
    <ol>{"".join(items)}</ol>
  </div>
  <figure class="index-preview" aria-hidden="true">
    <div class="frame">{img(first["cover"], "", sizes="45vw", eager=True, cls="pv")}</div>
    <figcaption id="pv-cap">{e(first["name"])}{" · " + e(fp) if fp else ""}</figcaption>
  </figure>
</div>'''
    return page(group, lang, t[group], t[group + "Lede"], body, og=first["cover"])


def page_series(s, lang):
    root = root_of(PATHS[s["slug"]][lang])
    t = T[lang]
    n = len(s["photos"])
    nx = C["series"][(C["series"].index(s) + 1) % len(C["series"])]
    place = s["place"][lang]
    label = s["name"] + (", " + place if place else "")

    def cell(p, i):
        alt = f'{label}, {i + 1} {t["of"]} {n}'
        return f'<button class="ph" type="button" data-i="{i}" aria-label="{e(alt)}">{img(p, alt, eager=i < 2)}</button>'

    grid, order = rows(s["photos"], cell)
    lb = [dict(src=src(p, 2000), w=min(p["w"], 2000), h=round(p["h"] * min(p["w"], 2000) / p["w"]), avg=p["avg"],
               alt=f'{label}, {i + 1} {t["of"]} {n}') for i, p in enumerate(order)]
    credit = t["credit"] + (" · " + s["credits"] if s["credits"] else "")
    lede = f'<p class="lede">{e(s["text"][lang])}</p>' if s["text"][lang] else ""
    nplace = nx["place"][lang]
    body = f'''<article class="series">
  <header class="page-head series-head">
    <a class="back" href="{url(s["group"], lang, root)}">← {e(t["back"])} {e(t[s["group"]])}</a>
    <h1>{e(s["name"])}</h1>
    <p class="pl">{e(place) + " · " if place else ""}{n} {t["photos"]}</p>
    {lede}
    <p class="credit">{e(credit)}</p>
  </header>
  <div class="photos">{grid}</div>
  <a class="next-series" href="{url(nx["slug"], lang, root)}"><span>{e(t["next"])}</span><b>{e(nx["name"])}</b><span class="pl">{e(nplace)}</span></a>
</article>'''
    lb_json = json.dumps(dict(name=s["name"], photos=lb), ensure_ascii=False).replace("</", "<\\/")
    lb_html = f'''<div class="lb" id="lb" hidden role="dialog" aria-modal="true" aria-label="{e(s["name"])}">
  <div class="lb-bar"><span id="lb-count"></span><button type="button" id="lb-close">{e(t["close"])}</button></div>
  <div class="lb-stage"><img id="lb-img" alt=""><button type="button" class="lb-nav" id="lb-prev" aria-label="{e(t["prev"])}"></button><button type="button" class="lb-nav" id="lb-next" aria-label="{e(t["nextPhoto"])}"></button></div>
</div>
<script type="application/json" id="lb-data">{lb_json}</script>
'''
    desc = s["text"][lang] or C["texts"][lang]["desc"]
    return page(s["slug"], lang, s["name"], desc, body, og=s["cover"], extra_end=lb_html)


def page_about(lang):
    key = "sobre"
    root = root_of(PATHS[key][lang])
    t = T[lang]
    tx = C["texts"][lang]
    work = "".join(
        f'<li><a href="{url(s["slug"], lang, root)}">{e(s["name"])}</a><span>{e(t[s["group"]])}{" · " + e(s["place"][lang]) if s["place"][lang] else ""}</span></li>'
        for s in C["series"])
    bio = "".join(f'<p class="bio">{e(p)}</p>' for p in tx["bio"])
    tl = "".join(f'<li><b>{e(a)}</b><span>{e(b)}</span></li>' for a, b in tx["timeline"] if a or b)
    timeline = f'<ol class="timeline">{tl}</ol>' if tl else ""
    portrait = (f'<figure class="portrait">{img(C["portrait"], t["portraitAlt"], sizes="(max-width: 860px) 100vw, 40vw", eager=True)}</figure>'
                if C["portrait"] else "")
    body = f'''<div class="about">
  <div class="about-text">
    <header class="page-head"><h1>{e(t["sobre"])}</h1></header>
    {bio}
    {timeline}
    <h2>{e(t["work"])}</h2>
    <ul class="worklist">{work}</ul>
  </div>
  {portrait}
</div>'''
    desc = tx["bio"][0] if tx["bio"] else tx["desc"]
    return page(key, lang, t["sobre"], desc, body, og=C["portrait"])


def page_contact(lang):
    key = "contato"
    t = T[lang]
    ct = C["contact"]
    tx = C["texts"][lang]
    opts = "".join(f"<option>{e(o)}</option>" for o in t["types"])
    rows_ = []
    if ct["email"]:
        rows_.append(f'<div><dt>{e(t["email"])}</dt><dd><a id="mail" href="mailto:{e(ct["email"])}">{e(ct["email"])}</a> '
                     f'<button type="button" class="copy" id="copy-mail" data-copy="{e(ct["email"])}" data-ok="{e(t["copied"])}" data-fail="{e(t["copyFail"])}">{e(t["copy"])}</button></dd></div>')
    if ct["whatsapp"]:
        rows_.append(f'<div><dt>{e(t["whatsapp"])}</dt><dd><a href="{e(ct["whatsapp_link"])}" target="_blank" rel="noopener">{e(ct["whatsapp"])}</a></dd></div>')
    if ct["instagram_link"]:
        rows_.append(f'<div><dt>{e(t["instagram"])}</dt><dd><a href="{e(ct["instagram_link"])}" target="_blank" rel="me noopener">{e(ct["instagram"])}</a></dd></div>')
    wa = f'<a class="wa" href="{e(ct["whatsapp_link"])}" target="_blank" rel="noopener">{e(t["whatsappCta"])}</a>' if ct["whatsapp"] else ""
    form = ""
    if ct["email"]:
        form = f'''<form id="form" class="form" novalidate data-to="{e(ct["email"])}" data-subject="{e(t["subject"])}" data-sent="{e(t["sent"].format(email=ct["email"]))}" data-required="{e(t["required"])}">
    <label for="f-name">{e(t["fName"])}<input id="f-name" name="name" autocomplete="name"></label>
    <label for="f-email">{e(t["fEmail"])}<input id="f-email" name="email" type="email" autocomplete="email"></label>
    <label for="f-type">{e(t["fType"])}<select id="f-type" name="type">{opts}</select></label>
    <label for="f-date">{e(t["fDate"])}<input id="f-date" name="date" type="date"></label>
    <label for="f-msg" class="wide">{e(t["fMsg"])}<textarea id="f-msg" name="msg" rows="5"></textarea></label>
    <div class="wide form-foot"><button type="submit" class="send">{e(t["fSend"])}</button><p id="form-status" role="status"></p></div>
  </form>'''
    body = f'''<div class="contact">
  <header class="page-head"><h1>{e(t["contato"])}</h1><p>{e(tx["contactLede"])}</p></header>
  <dl class="channels">{"".join(rows_)}</dl>
  {wa}
  {form}
</div>'''
    return page(key, lang, t["contato"], tx["contactLede"], body, og=C["portrait"])


def page_404():
    t = T["pt"]
    b = BASE_PATH
    links = "".join(f'<li><a href="{b}{PATHS[s["slug"]]["pt"]}">{e(s["name"])}</a></li>' for s in C["series"])
    return f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(t["notFound"])} · Giulia Camacho</title><meta name="robots" content="noindex">
<link rel="icon" href="{b}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Caprasimo&family=DM+Mono:wght@400;500&family=Schibsted+Grotesk:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="{b}assets/site.css?v={VER["css"]}"></head>
<body><main class="nf"><a class="logo" href="{b}"><span>Giulia</span><span>Camacho</span></a>
<h1>{e(t["notFound"])}</h1><p>{e(t["notFoundText"])}</p>
<ul><li><a href="{b}">{e(t["home"])}</a></li>{links}</ul></main></body></html>
'''


def build(out):
    global C, PATHS
    raw = fetch()
    C = load(raw)
    if not C["series"]:
        raise SystemExit("Nenhuma série publicada no Sanity. O site não foi gerado.")
    PATHS = dict(FIXED)
    for s in C["series"]:
        PATHS[s["slug"]] = dict(pt=f'{s["slug"]}/', en=f'en/{s["slug"]}/')

    out = pathlib.Path(out)
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    for f in ("site.css", "site.js", "favicon.svg"):
        shutil.copy2(HERE / "assets" / f, out / "assets" / f)
    VER["css"] = hashlib.sha1((HERE / "assets/site.css").read_bytes()).hexdigest()[:8]
    VER["js"] = hashlib.sha1((HERE / "assets/site.js").read_bytes()).hexdigest()[:8]

    def write(key, lang, content):
        p = out / PATHS[key][lang] / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    for lang in LANGS:
        write("inicio", lang, page_home(lang))
        write("editorial", lang, page_index("editorial", lang))
        write("lifestyle", lang, page_index("lifestyle", lang))
        write("sobre", lang, page_about(lang))
        write("contato", lang, page_contact(lang))
        for s in C["series"]:
            write(s["slug"], lang, page_series(s, lang))

    (out / "404.html").write_text(page_404(), encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    urls = []
    for key in PATHS:
        alts = "".join(f'<xhtml:link rel="alternate" hreflang="{h}" href="{abs_url(key, l)}"/>' for l, h in (("pt", "pt-BR"), ("en", "en")))
        for lang in LANGS:
            urls.append(f"<url><loc>{abs_url(key, lang)}</loc>{alts}</url>")
    (out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">' + "".join(urls) + "</urlset>\n")
    (out / "versao.txt").write_text(C["updated"] + "\n")
    pages = len(list(out.rglob("index.html")))
    print(f"Site gerado em {out}: {pages} páginas, {len(C['series'])} séries, conteúdo de {C['updated']}")


def check():
    """Diz se o conteúdo publicado no Sanity mudou desde o último deploy."""
    event = os.environ.get("GITHUB_EVENT_NAME", "")
    changed = True
    if event == "schedule":
        raw = fetch()
        try:
            with urllib.request.urlopen(SITE_URL + "versao.txt", timeout=30) as r:
                live = r.read().decode().strip()
        except Exception:
            live = ""
        changed = (raw.get("atualizado") or "") != live
        print(f"Sanity: {raw.get('atualizado')} · site: {live or '(sem versão)'} · mudou: {changed}")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"mudou={'true' if changed else 'false'}\n")
    else:
        print("mudou:", changed)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check()
    else:
        build(sys.argv[1] if len(sys.argv) > 1 else "dist")
