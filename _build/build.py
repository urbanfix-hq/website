#!/usr/bin/env python3
"""Build the three language pages of urbanfix.city from _build/page.html.

Run from the repo root:  python3 _build/build.py
Writes index.html (English), fr/index.html, ar/index.html, sitemap.xml and robots.txt.
Texts come from the T dictionary inside page.html (one place to edit); each page gets
its words baked into the HTML so search engines can read every language.
Needs Node.js (to read the dictionary). Jekyll ignores this _build folder.
"""
import html, json, re, subprocess, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = 'https://urbanfix.city'
URL = {'en': '/', 'fr': '/fr/', 'ar': '/ar/'}
OUT = {'en': 'index.html', 'fr': 'fr/index.html', 'ar': 'ar/index.html'}
LOCALE = {'en': 'en_US', 'fr': 'fr_FR', 'ar': 'ar_AR'}
LASTMOD = '2026-11-26'

SEO = {
 'en': ("UrbanFix – Citizen issue reporting and public space maintenance platform",
        "UrbanFix helps municipalities and their service providers turn citizens' photo reports into tracked, routed and fixed jobs. Mobile app and web back office, in Arabic, French and English."),
 'fr': ("UrbanFix – Plateforme de signalement citoyen et de maintenance de l'espace public",
        "UrbanFix aide les communes et leurs prestataires à transformer les signalements photo des citoyens en interventions suivies, orientées et réparées. Application mobile et back-office web, en arabe, français et anglais."),
 'ar': ("UrbanFix – منصة بلاغات المواطنين وصيانة الفضاءات العامة",
        "تساعد UrbanFix البلديات ومقدّمي خدماتها على تحويل بلاغات المواطنين المصوّرة إلى تدخّلات متابَعة ومحالة ومُصلَحة. تطبيق جوّال وواجهة إدارة على الويب، بالعربية والفرنسية والإنجليزية."),
}

tpl = (ROOT / '_build' / 'page.html').read_text(encoding='utf-8')

# Read the T dictionary with Node (it is a JS object literal).
m = re.search(r"const ENDPOINT=.*?;.*?\n(const T=\{.*?\n\});\n", tpl, re.S)
js = "const TO='webform@urbanfix.city';\n" + m.group(1) + "\nconsole.log(JSON.stringify(T));"
T = json.loads(subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True).stdout)

def head(lang):
    title, desc = SEO[lang]
    e = lambda v: html.escape(v, quote=True)
    alt = ''.join(f'<link rel="alternate" hreflang="{l}" href="{SITE}{u}">\n' for l, u in URL.items())
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "@id": f"{SITE}/#org", "name": "UrbanFix", "url": f"{SITE}/",
         "logo": f"{SITE}/assets/logo-full.png",
         "contactPoint": {"@type": "ContactPoint", "telephone": "+216-55-588-291", "contactType": "sales",
                          "availableLanguage": ["Arabic", "French", "English"]}},
        {"@type": "WebSite", "@id": f"{SITE}/#site", "url": f"{SITE}/", "name": "UrbanFix",
         "publisher": {"@id": f"{SITE}/#org"}, "inLanguage": ["en", "fr", "ar"]},
        {"@type": "SoftwareApplication", "name": "UrbanFix", "applicationCategory": "BusinessApplication",
         "operatingSystem": "Web, Android, iOS", "description": desc, "inLanguage": lang,
         "url": f"{SITE}{URL[lang]}", "publisher": {"@id": f"{SITE}/#org"}}]}
    return (f'<link rel="canonical" href="{SITE}{URL[lang]}">\n{alt}'
            f'<link rel="alternate" hreflang="x-default" href="{SITE}/">\n'
            f'<meta name="theme-color" content="#1167B0">\n'
            f'<meta property="og:type" content="website">\n<meta property="og:site_name" content="UrbanFix">\n'
            f'<meta property="og:title" content="{e(title)}">\n<meta property="og:description" content="{e(desc)}">\n'
            f'<meta property="og:url" content="{SITE}{URL[lang]}">\n<meta property="og:locale" content="{LOCALE[lang]}">\n'
            f'<meta property="og:image" content="{SITE}/assets/og-{lang}.png">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
            f'<meta name="twitter:card" content="summary_large_image">\n'
            f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')

def page(lang):
    d = T[lang]
    s = tpl.replace('%%TITLE%%', html.escape(SEO[lang][0], quote=False)) \
           .replace('%%DESC%%', html.escape(SEO[lang][1], quote=True)) \
           .replace('%%SEO%%', head(lang))
    s = s.replace('<html lang="en" dir="ltr">', f'<html lang="{lang}" dir="{"rtl" if lang == "ar" else "ltr"}">', 1)
    cut = s.index('<script>\n{')            # only bake text into the HTML part, not the script
    body, script = s[:cut], s[cut:]
    def fill(mo):
        v = d.get(mo.group(2))
        return mo.group(1) + (html.escape(v, quote=False) if v is not None else mo.group(3)) + '<'
    body = re.sub(r'(<[^>]*\bdata-i="([^"]+)"[^>]*>)([^<]*)<', fill, body)
    body = re.sub(r'(data-ph="([^"]+)"[^>]*?placeholder=")[^"]*"',
                  lambda mo: mo.group(1) + html.escape(d.get(mo.group(2), ''), quote=True) + '"', body)
    body = body.replace(f'data-lang="{lang}">', f'data-lang="{lang}" aria-current="page">', 1)
    return body + script

for lang, path in OUT.items():
    f = ROOT / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(page(lang), encoding='utf-8')
    print('wrote', path)

urls = ''.join(
    f'<url><loc>{SITE}{u}</loc><lastmod>{LASTMOD}</lastmod>'
    + ''.join(f'<xhtml:link rel="alternate" hreflang="{l2}" href="{SITE}{u2}"/>' for l2, u2 in URL.items())
    + f'<xhtml:link rel="alternate" hreflang="x-default" href="{SITE}/"/></url>\n' for u in URL.values())
(ROOT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                                  'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + urls + '</urlset>\n', encoding='utf-8')
(ROOT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n', encoding='utf-8')
print('wrote sitemap.xml, robots.txt')
