#!/usr/bin/env python3
"""Static site generator for ribboncheckup.org. Run: python3 build.py -> writes ./site"""
import re, shutil, datetime, html, json
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "site"
DOMAIN = "https://ribboncheckup.org"
SITE_NAME = "Ribbon Checkup"
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

def nav_links(active=None):
    return "".join(f'<a href="/{k}/"{" class=on" if k == active else ""}>{v["name"]}</a>' for k, v in SECTIONS.items())

def layout(title, description, body, url, extra_head="", kind="website", active=None):
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
<meta property="og:image" content="{DOMAIN}/mark.png">
<link rel="icon" href="/favicon.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
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
    <div>
      <div class="brand small"><img src="/mark-small.png" alt="" width="20" height="27"><span class="wm"><b>Ribbon</b><i>checkup</i><em>.org</em></span></div>
      <p>{TAGLINE}</p>
    </div>
    <div class="cols">
      <div>{foot_sections}</div>
      <div><a href="/about/">About</a><a href="/editorial-policy/">Editorial policy</a><a href="/disclaimer/">Medical disclaimer</a><a href="/privacy/">Privacy</a></div>
    </div>
  </div>
  <p class="fine">Content on this site is general health information. It is not medical advice and does not replace a clinician. &copy; {year} {SITE_NAME}.</p>
</footer>
</body>
</html>"""

def card(a, big=False):
    s = SECTIONS[a["section"]]
    return f"""<a class="card {s['color']}{' big' if big else ''}" href="/{a['section']}/{a['slug']}/">
  <span class="eyebrow">{s['name']}</span>
  <h3>{html.escape(a['title'])}</h3>
  <p>{html.escape(a['description'])}</p>
  <span class="meta">{a['words'] // 200 + 1} min read</span>
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
          "author": {"@type": "Organization", "name": SITE_NAME}, "publisher": {"@type": "Organization", "name": SITE_NAME},
          "mainEntityOfPage": url, "articleSection": s["name"]}
    body = f"""
<article class="post {s['color']}">
  <p class="eyebrow"><a href="/{a['section']}/">{s['name']}</a> &middot; {a['date']} &middot; {a['words'] // 200 + 1} min read</p>
  <h1>{html.escape(a['title'])}</h1>
  <p class="lede">{html.escape(a['description'])}</p>
  <div class="prose">
{md_to_html(a['body'])}
  </div>
  <p class="reviewed">Reviewed against current clinical guidelines at publication. Report an error: <a href="mailto:editors@ribboncheckup.org">editors@ribboncheckup.org</a>. See our <a href="/editorial-policy/">editorial policy</a>.</p>
  <aside class="related">
    <h2>Keep reading</h2>
    <ul>{rel_html}</ul>
  </aside>
</article>"""
    extra = f'<script type="application/ld+json">{json.dumps(ld)}</script>'
    return layout(f"{a['title']} | {SITE_NAME}", a["description"], body, url, extra, "article", a["section"])

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
        body = f"""<section class="hero small {s['color']}"><p class="eyebrow">Section</p><h1>{s['name']}</h1><p class="lede">{s['blurb']}</p></section>
<section class="grid">{cards}</section>"""
        (OUT / k).mkdir(exist_ok=True)
        (OUT / k / "index.html").write_text(layout(f"{s['name']} | {SITE_NAME}", s["blurb"], body, f"{DOMAIN}/{k}/", active=k))

    # home
    by_sec = {k: [a for a in articles if a["section"] == k] for k in SECTIONS}
    lead = by_sec["guides"][0]
    sec_blocks = ""
    for k, s in SECTIONS.items():
        items = by_sec[k][:3]
        sec_blocks += f"""<section class="secblock {s['color']}">
  <div class="sechead"><div><p class="eyebrow">{s['name']}</p><p class="blurb">{s['blurb']}</p></div><a class="more" href="/{k}/">All {s['name'].lower()} &rarr;</a></div>
  <div class="grid three">{''.join(card(a) for a in items)}</div>
</section>"""
    body = f"""<section class="hero home">
  <div class="herotext">
    <h1>Understand your health.<br><span>Make informed choices.</span></h1>
    <p class="lede">Plain explanations of tests, numbers, and screenings. What a result means, what it does not, and when to talk to someone.</p>
    <div class="cta">
      <a class="btn" href="/{lead['section']}/{lead['slug']}/">Start here</a>
      <a class="btn ghost" href="/preventive-health/">Preventive checklist</a>
    </div>
  </div>
  <img class="heromark" src="/mark.png" alt="" width="220" height="300">
</section>
<section class="pillars">
  {''.join(f'<a href="/{k}/" class="pillar {s["color"]}"><strong>{s["name"]}</strong><span>{s["blurb"]}</span></a>' for k, s in SECTIONS.items())}
</section>
{sec_blocks}
<section class="note">
  <h2>How we write</h2>
  <p>Every piece says what a test or number measures, the range that counts as normal, the common reasons it reads wrong, and the point at which a home result should become a conversation with a clinician. No miracle claims. No product pitches inside the content. Read the <a href="/editorial-policy/">editorial policy</a>.</p>
</section>"""
    (OUT / "index.html").write_text(layout(f"{SITE_NAME}: {TAGLINE}", "Plain explanations of health tests, lab numbers, and preventive screenings. What a result means, what it does not, and when to see a clinician.", body, f"{DOMAIN}/"))

    # static pages
    for p in (SRC / "pages").glob("*.md"):
        a = parse(p)
        d = OUT / a["slug"]; d.mkdir(exist_ok=True)
        body = f'<article class="post"><h1>{html.escape(a["title"])}</h1><div class="prose">{md_to_html(a["body"])}</div></article>'
        (d / "index.html").write_text(layout(f"{a['title']} | {SITE_NAME}", a["description"], body, f"{DOMAIN}/{a['slug']}/"))

    body = '<section class="hero small"><h1>Page not found</h1><p class="lede">That link is dead. <a href="/">Back to the front page.</a></p></section>'
    (OUT / "404.html").write_text(layout(f"Not found | {SITE_NAME}", "Page not found.", body, f"{DOMAIN}/404.html"))

    urls = [f"{DOMAIN}/"] + [f"{DOMAIN}/{k}/" for k in SECTIONS] + [f"{DOMAIN}/{p.stem}/" for p in (SRC / "pages").glob("*.md")] + [f"{DOMAIN}/{a['section']}/{a['slug']}/" for a in articles]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n")
    print(f"Built {len(articles)} articles, {sum(a['words'] for a in articles)} words, {len(urls)} URLs")

if __name__ == "__main__":
    build()
