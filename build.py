#!/usr/bin/env python3
"""Static site generator for ribboncheckup.org. Run: python3 build.py -> writes ./site"""
import re, shutil, datetime, html, json
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "site"
DOMAIN = "https://ribboncheckup.org"
SITE_NAME = "Ribbon Checkup"
PUBLISHER = "Ribbon Health Press"
TAGLINE = "Understand your health. Make informed choices."

SECTIONS = {
    "articles":          {"name": "Articles",          "color": "blue",   "blurb": "Reported pieces on how the body works, what the evidence says, and what changed."},
    "guides":            {"name": "Guides",            "color": "teal",   "blurb": "Step by step. How to test, how to read a result, how to choose."},
    "health-explained":  {"name": "Health Explained",  "color": "purple", "blurb": "The numbers on a lab report and a test strip, decoded one at a time."},
    "preventive-health": {"name": "Preventive Health", "color": "coral",  "blurb": "What to check, how often, and why. The screenings that change outcomes."},
}

def md_to_html(md: str) -> str:
    out, buf, mode = [], [], None
    def inline(s):
        s = html.escape(s, quote=False)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*", r"<em>\1</em>", s)
        s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)
        return s
    def flush():
        nonlocal buf, mode
        if not buf: return
        if mode == "p": out.append("<p>" + inline(" ".join(buf)) + "</p>")
        elif mode == "ul": out.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + "</ul>")
        elif mode == "ol": out.append("<ol>" + "".join(f"<li>{inline(b)}</li>" for b in buf) + "</ol>")
        elif mode == "quote": out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>")
        elif mode == "table":
            rows = [r for r in buf if not re.match(r"^\|?\s*-{2,}", r)]
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            head = "".join(f"<th>{inline(c)}</th>" for c in cells[0])
            body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in cells[1:])
            out.append(f'<div class="tablewrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
        buf, mode = [], None
    for line in md.splitlines():
        if line.startswith("### "): flush(); out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            flush(); sid = re.sub(r"[^a-z0-9]+", "-", line[3:].lower()).strip("-")
            out.append(f'<h2 id="{sid}">{inline(line[3:])}</h2>')
        elif line.startswith("- "):
            if mode != "ul": flush(); mode = "ul"
            buf.append(line[2:])
        elif re.match(r"^\d+\. ", line):
            if mode != "ol": flush(); mode = "ol"
            buf.append(re.sub(r"^\d+\. ", "", line))
        elif line.startswith("> "):
            if mode != "quote": flush(); mode = "quote"
            buf.append(line[2:])
        elif line.startswith("|"):
            if mode != "table": flush(); mode = "table"
            buf.append(line)
        elif line.strip() == "": flush()
        else:
            if mode != "p": flush(); mode = "p"
            buf.append(line.strip())
    flush()
    return "\n".join(out)

def parse(path: Path):
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    meta = {k.strip(): v.strip() for k, v in (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)}
    meta["slug"] = path.stem
    meta["section"] = path.parent.name
    meta["body"] = m.group(2)
    meta["words"] = len(re.findall(r"\w+", meta["body"]))
    return meta

import hashlib
CSS_VER = hashlib.md5((SRC / "style.css").read_bytes()).hexdigest()[:8]

def img_url(pid, w=1600):
    return f"https://images.unsplash.com/photo-{pid}?auto=format&fit=crop&w={w}&q=80"

def hero_figure(a, cls="hero-img"):
    if not a.get("image"): return ""
    pid, alt = a["image"], html.escape(a.get("image_alt", ""))
    return f"""<figure class="{cls}"><img src="{img_url(pid)}" srcset="{img_url(pid,800)} 800w, {img_url(pid,1200)} 1200w, {img_url(pid,1600)} 1600w, {img_url(pid,2400)} 2400w" sizes="(max-width: 48rem) 100vw, 44rem" alt="{alt}" loading="eager" decoding="async"><figcaption>{alt}. Photograph via <a href="https://unsplash.com" rel="noopener">Unsplash</a>.</figcaption></figure>"""

def nav_links(active=None):
    return "".join(f'<a href="/{k}/"{" class=on" if k == active else ""}>{v["name"]}</a>' for k, v in SECTIONS.items())

def layout(title, description, body, url, extra_head="", kind="website", active=None, og_image=None):
    year = datetime.date.today().year
    foot_sections = "".join(f'<a href="/{k}/">{v["name"]}</a>' for k, v in SECTIONS.items())
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{kind}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:image" content="{og_image or DOMAIN + "/mark.png"}">
<meta name="twitter:card" content="{"summary_large_image" if og_image else "summary"}">
<link rel="icon" href="/favicon.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;0,9..144,700;1,9..144,500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css?v={CSS_VER}">
{extra_head}
</head>
<body>
<header class="top">
  <a class="brand" href="/"><img src="/mark-small.png" alt="" width="26" height="35"><span class="wm"><b>Ribbon</b><i>checkup</i><em>.org</em></span></a>
  <nav>{nav_links(active)}<a href="/about/" class="about">About</a></nav>
</header>
<main>
{body}
</main>
<footer>
  <div class="footgrid">
    <div class="footabout">
      <div class="brand small"><img src="/mark-small.png" alt="" width="20" height="27"><span class="wm"><b>Ribbon</b><i>checkup</i><em>.org</em></span></div>
      <p>{TAGLINE}</p>
      <p class="footblurb">Ribbon Checkup is a health education publication from {PUBLISHER}. Plain explanations of urine tests, lab numbers, and preventive screenings, written to the standard in our editorial policy.</p>
    </div>
    <div class="cols">
      <div><strong>Sections</strong>{foot_sections}</div>
      <div><strong>Start here</strong><a href="/guides/how-to-choose-a-urine-test-kit/">Choosing a urine test kit</a><a href="/health-explained/what-a-10-parameter-dipstick-measures/">The 10 parameter dipstick</a><a href="/health-explained/kidney-health-urine-tests/">Kidney urine tests</a><a href="/preventive-health/preventive-screenings-by-decade/">Screenings by decade</a><a href="/glossary/">Glossary</a></div>
      <div><strong>Ribbon Checkup</strong><a href="/about/">About</a><a href="/faq/">FAQ</a><a href="/articles/ribbon-checkup-org-and-com-which-site-is-which/">.org vs .com</a><a href="/editorial-policy/">Editorial policy</a><a href="/disclaimer/">Medical disclaimer</a><a href="/privacy/">Privacy</a></div>
    </div>
  </div>
  <p class="fine">Ribbon Checkup (ribboncheckup.org) is published by {PUBLISHER}, a Scanbase, Inc. company. Content on this site is general health information. It is not medical advice and does not replace a clinician. &copy; {year} {PUBLISHER}.</p>
</footer>
</body>
</html>"""

def card(a, big=False):
    s = SECTIONS[a["section"]]
    thumb = f'<img class="thumb" src="{img_url(a["image"], 800)}" alt="" loading="lazy" decoding="async">' if a.get("image") else ""
    return f"""<a class="card {s['color']}{' big' if big else ''}" href="/{a['section']}/{a['slug']}/">
  {thumb}<div class="cardbody"><span class="eyebrow">{s['name']}</span>
  <h3>{html.escape(a['title'])}</h3>
  <p>{html.escape(a['description'])}</p>
  <span class="meta">{a['words'] // 200 + 1} min read</span></div>
</a>"""

def article_page(a, all_articles):
    s = SECTIONS[a["section"]]
    url = f"{DOMAIN}/{a['section']}/{a['slug']}/"
    same = [r for r in all_articles if r["section"] == a["section"] and r["slug"] != a["slug"]]
    other = [r for r in all_articles if r["section"] != a["section"]]
    related = (same + other)[:3]
    rel_html = "".join(f'<li><a href="/{r["section"]}/{r["slug"]}/">{html.escape(r["title"])}</a> <span class="tag {SECTIONS[r["section"]]["color"]}">{SECTIONS[r["section"]]["name"]}</span></li>' for r in related)
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a["description"],
          "datePublished": a["date"], "dateModified": a.get("updated", a["date"]),
          "author": {"@type": "Organization", "name": PUBLISHER}, "publisher": {"@type": "Organization", "name": PUBLISHER, "url": DOMAIN + "/about/"},
          "mainEntityOfPage": url, "articleSection": s["name"], **({"image": img_url(a["image"], 1200)} if a.get("image") else {})}
    h2s = re.findall(r"^## (.+)$", a["body"], flags=re.M)
    toc = ""
    if len(h2s) >= 3:
        items = "".join(f'<li><a href="#{re.sub(r"[^a-z0-9]+", "-", h.lower()).strip("-")}">{html.escape(h)}</a></li>' for h in h2s)
        toc = f'<nav class="toc"><p class="eyebrow">In this piece</p><ol>{items}</ol></nav>'
    body = f"""
<article class="post {s['color']}">
  <p class="eyebrow"><a href="/{a['section']}/">{s['name']}</a> &middot; {a['date']} &middot; {a['words'] // 200 + 1} min read</p>
  <h1>{html.escape(a['title'])}</h1>
  <p class="lede">{html.escape(a['description'])}</p>
  {hero_figure(a)}
  {toc}
  <div class="prose">
{md_to_html(a['body'])}
  </div>
  <p class="reviewed">By the {PUBLISHER} editorial team. Reviewed against current clinical guidelines at publication. Report an error: <a href="mailto:editors@ribboncheckup.org">editors@ribboncheckup.org</a>. See our <a href="/editorial-policy/">editorial policy</a>.</p>
  <aside class="related">
    <h2>Keep reading</h2>
    <ul>{rel_html}</ul>
  </aside>
</article>"""
    extra = f'<script type="application/ld+json">{json.dumps(ld)}</script>'
    return layout(f"{a['title']} | {SITE_NAME}", a["description"], body, url, extra, "article", a["section"], og_image=img_url(a["image"], 1200) if a.get("image") else None)

def build():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir()
    for f in ["style.css", "favicon.png", "mark.png", "mark-small.png"]:
        shutil.copy(SRC / f, OUT / f)
    (OUT / "CNAME").write_text("ribboncheckup.org\n")
    (OUT / ".nojekyll").write_text("")

    articles = []
    for sec in SECTIONS:
        d = SRC / "content" / sec
        if d.exists():
            articles += [parse(p) for p in d.glob("*.md")]
    articles.sort(key=lambda a: (a["section"], int(a["order"])))

    for a in articles:
        d = OUT / a["section"] / a["slug"]; d.mkdir(parents=True)
        (d / "index.html").write_text(article_page(a, articles))

    # section indexes
    for k, s in SECTIONS.items():
        items = [a for a in articles if a["section"] == k]
        cards = "\n".join(card(a) for a in items)
        hero_pid = items[0]["image"] if items and items[0].get("image") else None
        hero_style = f' style="background-image:url(\'{img_url(hero_pid, 2400)}\')"' if hero_pid else ""
        body = f"""<section class="bleed hero-photo small {s['color']}"{hero_style}><div class="inner"><p class="eyebrow light">Section</p><h1>{s['name']}</h1><p class="lede light">{s['blurb']}</p></div></section>
<section class="grid">{cards}</section>"""
        (OUT / k).mkdir(exist_ok=True)
        (OUT / k / "index.html").write_text(layout(f"{s['name']} | {SITE_NAME}", s["blurb"], body, f"{DOMAIN}/{k}/", active=k))

    # home
    by_sec = {k: [a for a in articles if a["section"] == k] for k in SECTIONS}
    lead = next(a for a in articles if a["slug"] == "how-to-choose-a-urine-test-kit")
    feat = next(a for a in articles if a["slug"] == "why-kidney-disease-is-found-late")
    feat2 = [next(a for a in articles if a["slug"] == s) for s in ("how-to-use-home-health-tests-without-fooling-yourself", "preventive-screenings-by-decade", "how-to-take-blood-pressure-at-home")]
    HERO = "1606206591513-adbfbdd7a177"
    BAND = "1625690987114-86f5af994b49"
    sec_blocks = ""
    for i, (k, s) in enumerate(SECTIONS.items()):
        items = [x for x in by_sec[k] if x["slug"] not in (feat["slug"],) and x not in feat2][:3]
        sec_blocks += f"""<section class="secblock {s['color']}{' tint' if i % 2 else ''}">
  <div class="inner">
  <div class="sechead"><div><p class="eyebrow">{s['name']}</p><h2>{s['blurb']}</h2></div><a class="more" href="/{k}/">All {s['name'].lower()} &rarr;</a></div>
  <div class="grid three">{''.join(card(a) for a in items)}</div>
  </div>
</section>"""
    body = f"""<section class="bleed hero-photo" style="background-image:url('{img_url(HERO, 2400)}')">
  <div class="inner">
    <p class="eyebrow light">Ribbon Checkup</p>
    <h1>Understand your health.<br><span>Make informed choices.</span></h1>
    <p class="lede light">Plain explanations of tests, numbers, and screenings. What a result means, what it does not, and when to talk to someone.</p>
    <div class="cta">
      <a class="btn" href="/{lead['section']}/{lead['slug']}/">Start here</a>
      <a class="btn ghost light" href="/preventive-health/">Preventive checklist</a>
    </div>
  </div>
</section>
<section class="pillars">
  {''.join(f'<a href="/{k}/" class="pillar {s["color"]}"><strong>{s["name"]}</strong><span>{s["blurb"]}</span></a>' for k, s in SECTIONS.items())}
</section>
<section class="featured">
  <a class="featmain {SECTIONS[feat['section']]['color']}" href="/{feat['section']}/{feat['slug']}/">
    <img src="{img_url(feat['image'], 1600)}" alt="" loading="eager">
    <div class="featbody"><span class="eyebrow light">{SECTIONS[feat['section']]['name']}</span><h2>{html.escape(feat['title'])}</h2><p>{html.escape(feat['description'])}</p></div>
  </a>
  <div class="featlist">
    <p class="eyebrow">Most useful first</p>
    {''.join(f'<a class="featrow {SECTIONS[a["section"]]["color"]}" href="/{a["section"]}/{a["slug"]}/"><img src="{img_url(a["image"], 400)}" alt="" loading="lazy"><span><em>{SECTIONS[a["section"]]["name"]}</em><strong>{html.escape(a["title"])}</strong></span></a>' for a in feat2)}
  </div>
</section>
{sec_blocks}
<section class="bleed band" style="background-image:url('{img_url(BAND, 2400)}')">
  <div class="inner">
    <blockquote>Every piece says what a test measures, the range that counts as normal, the common reasons it reads wrong, and the point at which a home result should become a conversation with a clinician.</blockquote>
    <p><a href="/editorial-policy/">How we write &rarr;</a></p>
  </div>
</section>"""
    (OUT / "index.html").write_text(layout(f"{SITE_NAME}: {TAGLINE}", "Plain explanations of health tests, lab numbers, and preventive screenings. What a result means, what it does not, and when to see a clinician.", body, f"{DOMAIN}/", og_image=img_url(HERO, 1200)))

    # static pages
    for p in (SRC / "pages").glob("*.md"):
        a = parse(p)
        d = OUT / a["slug"]; d.mkdir(exist_ok=True)
        extra = ""
        if a.get("schema") == "faq":
            qa = re.findall(r"^### (.+?)\n\n(.+?)(?=\n\n|\Z)", a["body"], flags=re.M | re.S)
            faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q.strip(), "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"\[(.+?)\]\(.+?\)", r"\1", ans.strip())}} for q, ans in qa]}
            extra = f'<script type="application/ld+json">{json.dumps(faq)}</script>'
        body = f'<article class="post wide"><p class="eyebrow">{SITE_NAME}</p><h1>{html.escape(a["title"])}</h1><p class="lede">{html.escape(a["description"])}</p><div class="prose">{md_to_html(a["body"])}</div></article>'
        (d / "index.html").write_text(layout(f"{a['title']} | {SITE_NAME}", a["description"], body, f"{DOMAIN}/{a['slug']}/", extra))

    body = '<section class="hero small"><h1>Page not found</h1><p class="lede">That link is dead. <a href="/">Back to the front page.</a></p></section>'
    (OUT / "404.html").write_text(layout(f"Not found | {SITE_NAME}", "Page not found.", body, f"{DOMAIN}/404.html"))

    urls = [f"{DOMAIN}/"] + [f"{DOMAIN}/{k}/" for k in SECTIONS] + [f"{DOMAIN}/{p.stem}/" for p in (SRC / "pages").glob("*.md")] + [f"{DOMAIN}/{a['section']}/{a['slug']}/" for a in articles]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")
    print(f"Built {len(articles)} articles, {sum(a['words'] for a in articles)} words, {len(urls)} URLs")

if __name__ == "__main__":
    build()
