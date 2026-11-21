#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VictoriumSoft SEO v17 patcher.
Downloads the public site's exact current GitHub repository (unless --source is supplied),
then builds a complete updated site and an upload-only patch without destroying code.
Python stdlib only. Never requires a GitHub token.
"""
from __future__ import annotations
import argparse
from datetime import date
from html import escape, unescape
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

DOMAIN = "https://www.victoriumsoft.site"
REPO = "muzafferodemis1907gfb-oss/victoriumsoft-site"
BRAND = "VictoriumSoft"
DEV_LINK = "https://play.google.com/store/apps/developer?id=Victorium+Soft"
EMAIL = "victoriumsoft@gmail.com"
VERSION = "v17"
HERE = Path(__file__).resolve().parent
PUBLIC_APPS = [
    # slug, name, package, type, category, snippet
    ("arcpitch", "ArcPitch: Soccer Career", "com.victoriumsoft.arcpitch", "game", "SportsGame", "Disk futbolu, akıllı paslar, hassas şutlar ve kulüp kariyeri sunan Android futbol oyunu."),
    ("balloon-pop", "Balloon Pop: Tap & Burst", "com.victoriumsoft.balons", "game", "ArcadeGame", "Renkli balon patlatma, refleks ve zamanlama temelli mobil arcade oyunu."),
    ("ekim-dostum", "Ekim Dostum", "com.victoriumsoft.ekimdostum", "app", "ProductivityApplication", "Tarla, ekili ürün, sulama, görev ve tarımsal üretim kayıtlarını takip etmeye yardımcı Android uygulaması."),
    ("orbcascade", "OrbCascade: Reflex Arcade", "com.victoriumsoft.orbcascade", "game", "ArcadeGame", "Refleks, doğru zamanlama, renk değişimi ve enerji dalgalarına dayanan arcade bulmaca oyunu."),
    ("pomodorox", "PomodoroX", "com.victoriumsoft.pomodorox", "app", "EducationalApplication", "Pomodoro odak zamanlayıcısı, ders çalışma, görev planlama ve verimli mola yönetimi uygulaması."),
    ("namaz-app", "NamazApp", "com.victoriumsoft.namazapp", "app", "LifestyleApplication", "Namaz vakitleri, kıble, Kur'an okuma, zikir ve İslami takvim araçlarını birleştiren uygulama."),
    ("water-reminder", "Water Reminder Hydrate Daily", "com.waterreminder.hydratedaily", "app", "HealthApplication", "Günlük su takibi, hedef belirleme ve kişiselleştirilebilir içme hatırlatıcıları."),
    ("maze-of-fate", "Maze Of Fate", "com.victoriumsoft.mazeoffate", "game", "PuzzleGame", "Labirentlerde doğru yolu bul, seviyeleri tamamla ve ödüller topla."),
    ("qubrift", "QUBRIFT", "com.qubrift.android", "game", "PuzzleGame", "Düşen bloklar, kombinasyonlar ve risk-ödül mekanikleriyle tempolu arcade bulmaca oyunu."),
    ("varnyx", "VARNYX: Stealth Horror Escape", "com.victoriumsoft.varnyxgames", "game", "ActionGame", "Birinci şahıs gizlilik ve korku temalı kaçış oyunu; mekanik tehditlerden saklan ve çıkışı bul."),
    ("utopiax-oracle", "UtopiaX: Coffee & Astrology", "com.victoriumsoft.utopiaxoracle", "app", "EntertainmentApplication", "Kahve fincanı fotoğrafları, sembolik yorumlar ve astroloji temalı eğlence uygulaması."),
    ("meravix", "MeraVix", "com.victoriumsoft.meravix", "app", "BusinessApplication", "Hayvancılık, arıcılık, sürü kayıtları ve çiftlik operasyonlarını tek yerde takip et."),
]
TEST_APPS = ("okeyv", "pokervix", "pukzio", "puzzleonx", "stakvio")
PUB = {x[0]: x for x in PUBLIC_APPS}

# URL title/description map (native text is in Turkish, EN button still translates interface).
PAGES = {
    "index.html": ("VictoriumSoft | Mobil Oyun, Android Uygulama ve Yazılım Geliştirme", "VictoriumSoft: Android oyunları, mobil uygulamalar, web yazılımı ve Ar-Ge. Google Play'deki 12 ürünümüzü keşfet, projeni bize anlat."),
    "about.html": ("Hakkımızda | VictoriumSoft Oyun ve Yazılım Stüdyosu", "VictoriumSoft'un oyun, Android uygulama ve web yazılımı çalışmalarını, vizyonunu ve geliştirme yaklaşımını keşfedin."),
    "support.html": ("Destek ve İletişim | VictoriumSoft", "VictoriumSoft oyunları ve mobil uygulamaları için destek, geri bildirim ve iletişim kanalları. Yardım için bize ulaşın."),
    "privacy.html": ("Gizlilik Politikası | VictoriumSoft", "VictoriumSoft web sitesinin gizlilik bilgileri ve kullanıcı verilerinin işlenmesine ilişkin açıklamalar."),
    "project.html": ("Mobil Uygulama, Oyun ve Web Projesi Teklifi | VictoriumSoft", "Mobil uygulama, Android oyunu, web sitesi veya yapay zekâ projenizi VictoriumSoft'a anlatın; ihtiyaçlarınıza özel proje teklifi alın."),
}
for slug, name, pkg, typ, category, desc in PUBLIC_APPS:
    PAGES[f"apps/{slug}.html"] = (f"{name} | Android | VictoriumSoft", f"{desc} Google Play'de VictoriumSoft tarafından yayınlandı.")
for slug in TEST_APPS:
    PAGES[f"apps/{slug}.html"] = (f"{slug.upper()} | Google Play Kapalı Test | VictoriumSoft", f"VictoriumSoft'un {slug} projesi Google Play'de kapalı test sürecinde. Yakında yayında.")

class MetaImage(HTMLParser):
    def __init__(self):
        super().__init__(); self.image = None
    def handle_starttag(self, tag, attrs):
        if tag != 'meta': return
        x=dict(attrs)
        if x.get('property') in ('og:image', 'og:image:url') or x.get('name')=='twitter:image':
            u=x.get('content','')
            if u.startswith('http') and not self.image: self.image=unescape(u)


def get_url(url, timeout=22):
    req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (VictoriumSoft SEO asset sync; contact victoriumsoft@gmail.com)','Accept':'text/html,image/*,*/*'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def download_repo(target:Path):
    url=f"https://codeload.github.com/{REPO}/zip/refs/heads/main"
    data=get_url(url,timeout=90)
    root=target.resolve()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for member in z.infolist():
            path=(root/member.filename).resolve()
            if not path.is_relative_to(root): raise ValueError('Unsafe ZIP path')
        z.extractall(root)
    dirs=[p for p in target.iterdir() if p.is_dir()]
    if len(dirs)!=1: raise RuntimeError('Unexpected GitHub archive layout')
    return dirs[0]


def read(p:Path): return p.read_text(encoding='utf-8')
def write(p:Path,s:str):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(s,encoding='utf-8')


def remove_meta(html:str):
    # Remove ONLY SEO-specific tags being replaced; retain Search Console verification.
    html=re.sub(r'<title\b[^>]*>.*?</title>', '', html, flags=re.I|re.S)
    for name in ['description','robots','twitter:card','twitter:title','twitter:description','twitter:image','twitter:image:alt']:
        html=re.sub(r'<meta\b(?=[^>]*\bname\s*=\s*["\']'+re.escape(name)+r'["\'])[^>]*>', '', html, flags=re.I)
    for name in ['og:title','og:description','og:url','og:type','og:site_name','og:image','og:image:alt','og:locale']:
        html=re.sub(r'<meta\b(?=[^>]*\bproperty\s*=\s*["\']'+re.escape(name)+r'["\'])[^>]*>', '', html, flags=re.I)
    html=re.sub(r'<link\b(?=[^>]*\brel\s*=\s*["\']canonical["\'])[^>]*>', '', html, flags=re.I)
    return html


def jsonld(obj):
    return json.dumps(obj,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e')


def add_seo_head(html:str,path:str,title:str,desc:str,indexable:bool,structured:list|None=None,site:Path|None=None):
    if '<head>' not in html: raise RuntimeError(f'Missing head: {path}')
    url=(DOMAIN+'/' if path=='index.html' else DOMAIN+'/'+path)
    app_slug=Path(path).stem if path.startswith('apps/') else None
    icon_local=(site/'assets/apps/published'/f'{app_slug}-icon.png') if site and app_slug else None
    app_icon=(f'{DOMAIN}/assets/apps/published/{app_slug}-icon.png'
              if app_slug in PUB and icon_local and icon_local.exists()
              else f'{DOMAIN}/assets/victoriumsoft-brand-poster.png')
    html=remove_meta(html)
    # Preserve existing LD+JSON scripts except the old basic Organization-only block on homepage.
    if path=='index.html':
        html=re.sub(r'<script\s+type="application/ld\+json"\s*>\s*\{(?:(?!</script>).)*?"@type"\s*:\s*"Organization"(?:(?!</script>).)*?</script>','',html,flags=re.S)
    head=[
       f'<title>{escape(title)}</title>',
       f'<meta name="description" content="{escape(desc,quote=True)}" />',
       '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />' if indexable else '<meta name="robots" content="noindex,follow" />',
       f'<link rel="canonical" href="{escape(url,quote=True)}" />',
       f'<meta property="og:type" content="website" />',
       f'<meta property="og:site_name" content="VictoriumSoft" />',
       f'<meta property="og:locale" content="tr_TR" />',
       f'<meta property="og:url" content="{escape(url,quote=True)}" />',
       f'<meta property="og:title" content="{escape(title,quote=True)}" />',
       f'<meta property="og:description" content="{escape(desc,quote=True)}" />',
       f'<meta property="og:image" content="{escape(app_icon,quote=True)}" />',
       f'<meta property="og:image:alt" content="{escape(app_slug or "VictoriumSoft",quote=True)} görseli" />',
       '<meta name="twitter:card" content="summary_large_image" />',
       f'<meta name="twitter:title" content="{escape(title,quote=True)}" />',
       f'<meta name="twitter:description" content="{escape(desc,quote=True)}" />',
       f'<meta name="twitter:image" content="{escape(app_icon,quote=True)}" />'
    ]
    if structured:
        for obj in structured:
            head.append(f'<script type="application/ld+json">{jsonld(obj)}</script>')
    # Append at end of head to avoid interfering with viewport/charset and Google verification.
    html=html.replace('</head>','\n  <!-- VictoriumSoft SEO v17: static metadata for crawlers -->\n  '+'\n  '.join(head)+'\n</head>',1)
    return html


def org_schema():
    return {'@context':'https://schema.org','@type':'Organization','@id':DOMAIN+'/#organization',
            'name':'VictoriumSoft','url':DOMAIN+'/','email':EMAIL,
            'logo':{'@type':'ImageObject','url':DOMAIN+'/assets/victoriumsoft-logo.png'},
            'sameAs':[DEV_LINK,'https://www.instagram.com/victoriumsoft/','https://www.tiktok.com/@victoriumsoft6']}


def home_schemas():
    items=[{'@type':'ListItem','position':i+1,'name':app[1],'url':f'{DOMAIN}/apps/{app[0]}.html'} for i,app in enumerate(PUBLIC_APPS)]
    return [org_schema(),{'@context':'https://schema.org','@type':'WebSite','@id':DOMAIN+'/#website','url':DOMAIN+'/','name':'VictoriumSoft','inLanguage':'tr-TR','publisher':{'@id':DOMAIN+'/#organization'}},
            {'@context':'https://schema.org','@type':'ItemList','name':'VictoriumSoft Google Play uygulamaları ve oyunları','itemListOrder':'https://schema.org/ItemListOrderAscending','numberOfItems':len(PUBLIC_APPS),'itemListElement':items}]


def app_schemas(app):
    slug,name,pkg,typ,category,desc=app
    page=f'{DOMAIN}/apps/{slug}.html'
    appobj={'@context':'https://schema.org', '@type':['MobileApplication','VideoGame'] if typ=='game' else 'MobileApplication',
            '@id':page+'#application','name':name,'description':desc, 'url':page,
            'operatingSystem':'Android','applicationCategory':'GameApplication' if typ=='game' else category,
            'isAccessibleForFree':True,
            'offers':{'@type':'Offer','price':'0','priceCurrency':'TRY','url':f'https://play.google.com/store/apps/details?id={pkg}'},
            'publisher':{'@id':DOMAIN+'/#organization'}}
    # Do not invent aggregateRating, ratingCount, installs, awards or reviews.
    breadcrumb={'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[
      {'@type':'ListItem','position':1,'name':'Ana Sayfa','item':DOMAIN+'/'},
      {'@type':'ListItem','position':2,'name':name,'item':page}]}
    return [appobj,breadcrumb]


def informative_schema(path):
    title,desc=PAGES[path];url=DOMAIN+'/'+path
    return [{'@context':'https://schema.org','@type':'WebPage','name':title,'url':url,'description':desc,'inLanguage':'tr-TR','isPartOf':{'@id':DOMAIN+'/#website'}}]


def cindex(html:str):
    # Updated public status, counters and text. No HTML reserialization.
    html=html.replace('9 ürün üretimde · 7 proje Google Play kapalı testte', '12 uygulama ve oyun Google Play’de yayında · 5 proje kapalı testte')
    html=re.sub(r'(<strong class="counter" data-count=")\d+("[^>]*>0</strong><span data-i18n="metaGames")',r'\g<1>12\2',html)
    html=re.sub(r'(<strong class="counter" data-count=")\d+("[^>]*>0</strong><span data-i18n="metaComing")',r'\g<1>5\2',html)
    html=html.replace('7 proje kapalı testte','5 proje kapalı testte')
    html=html.replace('9 ürün üretimde', '12 ürün Google Play’de yayında')
    html=html.replace('com.victoriumsoft.utopiaxoracle</option>', 'com.victoriumsoft.utopiaxoracle</option>')
    # Remove only the two cards whose state changed; do not remove unrelated cards.
    for slug in ('utopiax-oracle','varnyx'):
        pattern=rf'\s*<a class="project-card app-card testing-card reveal" href="apps/{slug}\.html"\b.*?</a>'
        html,n=re.subn(pattern,'',html,count=1,flags=re.S)
        # href is preceded by a quote, so \b can fail; fallback
        if n==0:
            pattern=rf'\s*<a\b[^>]*class="project-card app-card testing-card reveal"[^>]*href="apps/{slug}\.html"[^>]*>.*?</a>'
            html=re.sub(pattern,'',html,count=1,flags=re.S)
    for name in ('UtopiaX Oracle','VARNYX'):
        html=html.replace(f'<option>{name}</option>','')
    # New published cards: inject just before the published-grid closing tag.
    added = []
    for order,slug in [(10,'varnyx'),(11,'utopiax-oracle'),(12,'meravix')]:
        app=PUB[slug]; name=app[1];desc=app[5];typ=app[3]
        tag={'varnyx':'HORROR / STEALTH','utopiax-oracle':'ENTERTAINMENT / COFFEE','meravix':'FARM / LIVESTOCK'}[slug]
        label={'varnyx':'Aksiyon','utopiax-oracle':'Eğlence','meravix':'İş'}[slug]
        added.append(f'''\n        <a class="project-card app-card reveal" data-kind="{'game' if typ=='game' else 'app'}" href="apps/{slug}.html" aria-label="{escape(name,quote=True)} detaylarını aç">
          <div class="card-top"><span class="tag">{tag}</span><span>{order:02d}</span></div>
          <div class="project-art app-art seo-app-art seo-app-art-{slug}"><div class="app-icon-wrap"><img loading="lazy" decoding="async" width="220" height="220" src="assets/apps/published/{slug}-icon.png" alt="{escape(name,quote=True)} resmi Google Play uygulama simgesi" /></div><span class="store-pill">Google Play</span></div>
          <div class="card-copy"><h3>{escape(name)}</h3><div class="published-card-meta"><span class="live-badge" data-i18n="liveOnPlay">Google Play’de yayında</span><span class="rating-chip" data-i18n="ratingNew">★ Yeni</span><span class="category-chip">{label}</span></div><p>{escape(desc)}</p><span class="card-link" data-i18n="viewApp">Uygulamayı incele →</span></div>
        </a>''')
    marker='<div class="project-grid published-grid">'
    pos=html.find(marker)
    if pos<0: raise RuntimeError('Published grid not found; site layout may have changed')
    # insert at first direct closing div after final published card, before logo showcase
    show=html.find('<div class="logo-showcase-panel',pos)
    if show<0: raise RuntimeError('Published logo showcase missing')
    end=html.rfind('\n      </div>',pos,show)
    if end<0: raise RuntimeError('Published grid closing tag missing')
    missing=[t for slug,t in zip(('varnyx','utopiax-oracle','meravix'),added) if f'href="apps/{slug}.html"' not in html[pos:show]]
    if missing: html=html[:end]+''.join(missing)+'\n'+html[end:]
    # Add icon badges for published logo section.
    logos=''.join(f'''\n          <a class="published-logo-item" href="apps/{slug}.html"><div class="published-logo-image"><img loading="lazy" decoding="async" width="118" height="118" src="assets/apps/published/{slug}-icon.png" alt="{escape(PUB[slug][1],quote=True)} simgesi" /></div><strong>{escape(PUB[slug][1])}</strong><span class="live-badge" data-i18n="liveOnPlay">Google Play’de yayında</span></a>''' for slug in ('varnyx','utopiax-oracle','meravix'))
    key='<div class="published-logo-grid">';i=html.find(key)
    if i>=0:
        j=html.find('\n        </div>',i)
        if j>=0 and 'apps/meravix.html' not in html[i:j]: html=html[:j]+logos+html[j:]
    # Add compact published release rail links.
    key='<div class="release-rail" role="list">';i=html.find(key)
    if i>=0:
        j=html.find('\n      </div>',i)
        if j>=0:
            extra=''.join(f'''\n        <a class="release-chip" role="listitem" href="apps/{slug}.html"><img loading="lazy" width="54" height="54" src="assets/apps/published/{slug}-icon.png" alt="{escape(PUB[slug][1],quote=True)}" /><span><b>{escape(PUB[slug][1])}</b><small>{'Oyun' if PUB[slug][3]=='game' else 'Uygulama'}</small></span><i>↗</i></a>''' for slug in ('maze-of-fate','qubrift','varnyx','utopiax-oracle','meravix'))
            if 'apps/meravix.html' not in html[i:j]: html=html[:j]+extra+html[j:]
    # keep SEO graphic labels honest: screenshot origin of Varnyx/Utopia is console, others official sync attempted.
    # Current Google Play branding: no obsolete marketing claim on homepage.
    html=html.replace('OrbCascade: Bubble Shooter','OrbCascade: Reflex Arcade')
    html=html.replace('Fizik tabanlı futbol bulmacaları, farklı dünyalar, engeller ve hassas atış mekaniği.', 'Disk futbolu, paslar, hassas şutlar ve kulüp kariyeri odaklı spor deneyimi.')
    html=html.replace('Gökyüzü krallığında renk eşleştirme, bubble shooter seviyeleri ve rahat tempolu bulmaca oynanışı.', 'Renk değişimi, refleks ve doğru zamanlama gerektiren arcade bulmaca deneyimi.')
    html=html.replace('Bu bölümde Google Play', 'Bu bölümde Google Play')
    return html


def translations(js:str):
    updates={
      'heroStatus':('12 uygulama ve oyun Google Play’de yayında · 5 proje kapalı testte','12 apps and games live on Google Play · 5 in closed testing'),
      'metaGames':('Google Play’de yayınlanan ürün','products published on Google Play'),
      'metaComing':('Kapalı testte · yakında yayınlanacak proje','closed-test projects · coming soon'),
      'portfolioSummary':('12 uygulama ve oyun yayında · 5 proje kapalı testte','12 published apps and games · 5 projects in closed testing'),
      'testCount':('5 proje kapalı testte','5 projects in closed testing'),
      'comingText':('Kapalı testteki 5 proje: OkeyV, POKERVIX Poker, Pukzio, PuzzleonX ve STAKVIO. Yayın öncesi test süreçleri sürüyor.',
                    'Five projects remain in closed testing: OkeyV, POKERVIX Poker, Pukzio, PuzzleonX and STAKVIO.'),
      'orbText':('Renk değişimi, refleks ve doğru zamanlama gerektiren arcade bulmaca deneyimi.',
                 'An arcade puzzle experience built around color changes, reflexes and careful timing.'),
      'arcpitchText':('Disk futbolu, paslar, hassas şutlar ve kulüp kariyeri odaklı spor deneyimi.',
                      'Disc soccer gameplay with passes, precise shots and a club career.'),
      'publishedLogosText':('VictoriumSoft’un Google Play’de yayınlanan oyun ve uygulamalarının simgeleri.',
                            'Icons of VictoriumSoft games and apps published on Google Play.'),
      'heroText':('VictoriumSoft; Android oyunları, mobil uygulamalar ve web yazılımları geliştirir. 12 ürünümüzü inceleyin; proje geliştirme için bize ulaşın.',
                   'VictoriumSoft develops Android games, mobile apps and web software. Explore our 12 products or get in touch about your project.'),
    }
    for k,(tr,en) in updates.items():
        p=re.compile(r'(?<![\w])'+re.escape(k)+r':\s*"(?:\\.|[^"\\])*"')
        matches=list(p.finditer(js))
        if len(matches)<2:
            print(f'[warn] Translation key {k} not found twice: {len(matches)}')
            continue
        new=[];last=0
        for i,m in enumerate(matches):
            val=tr if i==0 else en
            new.append(js[last:m.start()]+f'{k}:'+json.dumps(val,ensure_ascii=False))
            last=m.end()
        js=''.join(new)+js[last:]
    return js


def upgrade_old_page(html:str,app):
    slug,name,pkg,typ,category,desc=app
    html=html.replace('GAME · GOOGLE PLAY TEST', 'GAME · GOOGLE PLAY')
    html=re.sub(r'(?s)<h1>.*?</h1>',f'<h1>{escape(name)}</h1>',html,count=1)
    subtitle=f'<p class="detail-subtitle" data-tr="Google Play’de yayında" data-en="Live on Google Play">Google Play’de yayında</p>'
    html=re.sub(r'(?s)<p class="detail-subtitle"\b[^>]*>.*?</p>',subtitle,html,count=1)
    d=f'<p class="detail-description" data-tr="{escape(desc,quote=True)}" data-en="{escape(desc,quote=True)}">{escape(desc)}</p>'
    html=re.sub(r'(?s)<p class="detail-description"\b[^>]*>.*?</p>',d,html,count=1)
    html=html.replace('data-tr="Kapalı testte · yakında yayında" data-en="Closed testing · publishing soon"','data-tr="Google Play’de yayında" data-en="Live on Google Play"')
    # Replace any test notice with accurate production statement; leave the rest of page intact.
    html=re.sub(r'<section class="detail-section"><div class="coming-notice reveal">.*?</div></section>',
      f'<section class="detail-section"><div class="coming-notice reveal"><span class="kicker">GOOGLE PLAY</span><h2>{escape(name)} Google Play’de</h2><p>{escape(desc)}</p><p><a href="https://play.google.com/store/apps/details?id={pkg}" target="_blank" rel="noopener noreferrer">Google Play mağaza sayfasını aç →</a></p></div></section>',html,count=1,flags=re.S)
    # Replace the hero testing/soon label in generic pages.
    html=html.replace('GOOGLE PLAY CLOSED TEST','GOOGLE PLAY')
    html=html.replace('Kapalı testte · yakında yayında','Google Play’de yayında')
    html=html.replace('data-tr="Kapalı test" data-en="Closed test"','data-tr="Yayında" data-en="Published"')
    html=html.replace('data-tr="Yakında" data-en="Coming Soon"','data-tr="Yayında" data-en="Published"')
    # Ensure actual icon replaces the letter placeholder, if present.
    html=html.replace('<div class="testing-emblem">V</div>',f'<img loading="eager" src="../assets/apps/published/{slug}-icon.png" alt="{escape(name,quote=True)} uygulama simgesi" />')
    html=html.replace('<div class="testing-emblem">UO</div>',f'<img loading="eager" src="../assets/apps/published/{slug}-icon.png" alt="{escape(name,quote=True)} uygulama simgesi" />')
    # Insert meaningful editorial section for thin old test detail pages; no marketing hype.
    extra=f'''<section class="detail-section"><div class="detail-section-head"><div><span class="kicker">ANDROID</span><h2>{escape(name)} hakkında</h2></div></div><p class="seo-app-description">{escape(desc)} Uygulamanın güncel mağaza sürümü ve ayrıntılı özellikleri için Google Play sayfasını ziyaret edebilirsiniz.</p><div class="seo-app-showcase"><img loading="lazy" decoding="async" width="220" height="220" src="../assets/apps/published/{slug}-icon.png" alt="{escape(name,quote=True)} simgesi" /><a class="btn btn-primary" href="https://play.google.com/store/apps/details?id={pkg}" target="_blank" rel="noopener noreferrer">Google Play’de görüntüle ↗</a></div></section>'''
    html=html.replace('</main>',extra+'</main>',1)
    return html


def new_meravix():
    app=PUB['meravix']; name=app[1]; desc=app[5]
    return f'''<!doctype html>
<html lang="tr"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" /><meta name="theme-color" content="#080611" /><link rel="icon" href="../assets/victoriumsoft-logo.png" /><link rel="stylesheet" href="../style.css" /></head>
<body class="detail-body" id="top"><div class="noise" aria-hidden="true"></div><div class="cursor-glow" aria-hidden="true"></div>
<header class="topbar detail-topbar"><a class="brand" href="../index.html"><img src="../assets/victoriumsoft-logo.png" alt="VictoriumSoft logosu"/><span>VictoriumSoft</span></a><nav class="desktop-nav"><a href="../index.html#projects">Yayınlananlar</a><a href="../about.html">Hakkımızda</a><a href="../index.html#contact">İletişim</a></nav><div class="header-actions"><button class="lang-btn" id="langBtn" type="button">EN</button><button class="menu-btn" id="menuBtn" type="button" aria-expanded="false"><span></span><span></span></button></div></header>
<aside class="mobile-menu" id="mobileMenu" aria-hidden="true"><a href="../index.html#projects">Yayınlananlar</a><a href="../index.html#contact">İletişim</a></aside>
<main class="detail-main"><section class="detail-hero"><div class="detail-app-visual reveal"><div class="detail-icon-stage"><img loading="eager" src="../assets/apps/published/meravix-icon.png" alt="MeraVix uygulama simgesi" /></div></div><div class="detail-copy reveal delay-1"><span class="kicker">LIVESTOCK · BEEKEEPING · ANDROID</span><h1>MeraVix</h1><p class="detail-subtitle" data-tr="Hayvancılık ve arıcılık yönetimi" data-en="Livestock and beekeeping management">Hayvancılık ve arıcılık yönetimi</p><p class="detail-description" data-tr="{escape(desc,quote=True)}" data-en="An Android application for livestock, beekeeping and farm operations.">{escape(desc)}</p><div class="detail-actions"><a class="btn btn-primary" href="https://play.google.com/store/apps/details?id=com.victoriumsoft.meravix" target="_blank" rel="noopener noreferrer">Google Play’de aç ↗</a><a class="btn btn-ghost" href="../index.html#projects">← Yayınlananlar</a></div><div class="detail-badges"><span class="detail-badge">Android</span><span class="detail-badge">Google Play</span><span class="detail-badge">VictoriumSoft</span></div></div></section>
<section class="detail-section"><div class="detail-section-head"><div><span class="kicker">MeraVix</span><h2>Çiftlik kayıtlarınızı tek yerde yönetin</h2></div><p>Hayvanlar, arılıklar ve günlük çiftlik işlemleri için temel kayıtları düzenlemek ve kendi verilerinizle çalışmak üzere geliştirilmiş mobil uygulama.</p></div><div class="seo-app-showcase"><img src="../assets/apps/published/meravix-icon.png" alt="MeraVix simgesi" width="160" height="160" loading="lazy"/><a class="btn btn-primary" href="https://play.google.com/store/apps/details?id=com.victoriumsoft.meravix" target="_blank" rel="noopener noreferrer">Google Play mağaza sayfası ↗</a></div></section>
</main><footer class="detail-footer"><div class="footer-bottom"><p>© <span id="year"></span> VictoriumSoft</p><a href="#top" class="back-top">↑</a></div></footer><script src="../detail.js"></script></body></html>'''


def ensure_icons(site:Path,allow_network:bool):
    dest=site/'assets/apps/published';dest.mkdir(parents=True,exist_ok=True)
    for slug in ('varnyx','utopiax-oracle','meravix'):
        pkg=PUB[slug][2];target=dest/(slug+'-icon.png')
        if allow_network:
            try:
                url=f'https://play.google.com/store/apps/details?id={pkg}&hl=en&gl=US'
                data=get_url(url).decode('utf-8',errors='replace')
                parser=MetaImage();parser.feed(data)
                if parser.image:
                    icon=get_url(parser.image,timeout=20)
                    # Avoid saving HTML/Cloudflare bot response as icon.
                    if len(icon)>500 and (icon.startswith(b'\x89PNG') or icon.startswith(b'\xff\xd8') or icon[:4]==b'RIFF'):
                        suffix='.png' if icon.startswith(b'\x89PNG') else '.jpg' if icon.startswith(b'\xff\xd8') else '.webp'
                        # Keep a correct MIME extension; when not PNG, use exact suffix in HTML.
                        # Most Google Play icon responses are PNG or WEBP; convert to PNG if Pillow present.
                        if suffix!='.png':
                            try:
                                from PIL import Image
                                with Image.open(io.BytesIO(icon)) as im:
                                    im.convert('RGBA').save(target,'PNG',optimize=True)
                            except ImportError:
                                print(f'[warn] Pillow missing for {slug} conversion, using fallback icon')
                            except Exception as err: print(f'[warn] icon conversion {slug}: {err}')
                        else: target.write_bytes(icon)
                if target.exists() and target.stat().st_size>1000:
                    print(f'[ok] Official icon downloaded from Google Play: {slug}')
                    continue
            except Exception as err:
                print(f'[warn] Could not fetch official {slug} icon: {str(err)[:120]}')
        shutil.copy2(HERE/'assets'/(slug+'-icon.png'),target)
        print(f'[fallback] {slug}: local fallback icon used; replace with your official 512x512 PNG for best results')


def build_sitemap(site:Path):
    ET.register_namespace('','http://www.sitemaps.org/schemas/sitemap/0.9')
    ns='{http://www.sitemaps.org/schemas/sitemap/0.9}'
    root=ET.Element(ns+'urlset')
    urls=['index.html','about.html','support.html','privacy.html','project.html']+[f'apps/{slug}.html' for slug,*_ in PUBLIC_APPS]
    for path in urls:
        if not (site/path).exists(): continue
        u=ET.SubElement(root,ns+'url');loc=ET.SubElement(u,ns+'loc')
        loc.text=DOMAIN+'/' if path=='index.html' else DOMAIN+'/'+path
        # lastmod is not fabricated: we just regenerated page content today
        lm=ET.SubElement(u,ns+'lastmod');lm.text=date.today().isoformat()
    data=ET.tostring(root,encoding='unicode',xml_declaration=True)
    write(site/'sitemap.xml',data+'\n')
    write(site/'robots.txt',f'User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n')


def css_update(site:Path):
    p=site/'style.css';s=read(p)
    addon='''
/* VictoriumSoft SEO v17: published products and accessible app assets */
.seo-app-art { background: radial-gradient(circle at 50% 27%, rgba(168,85,247,.16), transparent 47%), linear-gradient(145deg,#0e0b1c,#080712); }
.seo-app-art-varnyx { background:radial-gradient(circle at 50% 20%,rgba(214,60,84,.18),transparent 42%),#0e0a16; }
.seo-app-art-utopiax-oracle { background:radial-gradient(circle at 40% 32%,rgba(209,159,66,.18),transparent 42%),#130d19; }
.seo-app-art-meravix { background:radial-gradient(circle at 60% 24%,rgba(77,180,118,.15),transparent 45%),#071813; }
.seo-app-showcase {display:flex;align-items:center;gap:22px;flex-wrap:wrap;padding:18px 0 24px}
.seo-app-showcase img {width:min(160px,35vw);height:auto;aspect-ratio:1;object-fit:cover;border-radius:26%;border:1px solid rgba(255,255,255,.12)}
.seo-app-description {font-size:16px;line-height:1.75;color:var(--muted);max-width:860px}
@media(max-width:700px){.seo-app-showcase{align-items:stretch}.seo-app-showcase .btn{max-width:100%}}
'''
    if 'VictoriumSoft SEO v17:' not in s:
        write(p,s+'\n'+addon)


def update_sw(site:Path):
    p=site/'service-worker.js'
    if not p.exists(): return
    s=read(p)
    s=re.sub(r"(const CACHE_NAME\s*=\s*['\"])[^'\"]+",r'\g<1>victoriumsoft-v17',s,count=1)
    write(p,s)


def make_outputs(site:Path,changed:set[str],out_dir:Path):
    full=out_dir/'victoriumsoft-site-v17-seo-full.zip'
    patch=out_dir/'victoriumsoft-v17-SEO-PATCH.zip'
    for dest,paths in [(full,[p for p in site.rglob('*') if p.is_file()]),
                       (patch,[site/p for p in sorted(changed) if (site/p).is_file()])]:
        with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
            for p in paths:
                relative=p.relative_to(site)
                z.write(p,Path('victoriumsoft-site')/relative if dest==full else relative)
    print('Complete site: ',full)
    print('GitHub upload patch:',patch)
    return full,patch


def validate(site:Path):
    bad=[];seo=[]
    html_paths=list(site.glob('*.html'))+list((site/'apps').glob('*.html'))
    for p in html_paths:
        s=read(p)
        if p.name!='404.html':
            if s.count('rel="canonical"')!=1: bad.append(f'Canonical count {p}: {s.count("rel=\"canonical\"")}')
            if not re.search(r'<meta\s+name="description"',s): bad.append(f'Description missing: {p}')
            for block in re.findall(r'<script\s+type="application/ld\+json"\s*>(.*?)</script>',s,flags=re.S):
                try: json.loads(block)
                except Exception as exc: bad.append(f'Invalid JSON-LD {p}: {exc}')
        for path in re.findall(r'(?:src|href)=["\']([^"\']+)["\']',s):
            if path.startswith(('#','http://','https://','mailto:','tel:','data:','javascript:')):continue
            resolved=p.parent/path.split('?')[0].split('#')[0]
            if not resolved.exists():
                # asset could be a dynamically rendered URL from original code: print warning, don't fail build
                if 'assets/apps/published/' in path or path.endswith(('.css','.js','.html')): seo.append(f'Possibly missing: {p.relative_to(site)} -> {path}')
    for key in ['apps/varnyx.html','apps/utopiax-oracle.html','apps/meravix.html']:
        if not (site/key).exists(): bad.append(f'Missing public page: {key}')
    sitemap=ET.parse(site/'sitemap.xml')
    urls=[x.text for x in sitemap.getroot().iter() if x.tag.endswith('loc')]
    if len(urls)!=17: bad.append(f'Expected 17 canonical sitemap URLs; found {len(urls)}')
    if bad: raise RuntimeError('Validation failed:\n'+'\n'.join(bad))
    print(f'[ok] Validated {len(html_paths)} HTML pages, {len(urls)} sitemap URLs')
    if seo:print('[info] Additional existing relative resource checks: '+'; '.join(seo[:8]))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',help='Existing extracted GitHub repository directory; omits automatic download')
    parser.add_argument('--offline',action='store_true',help='Do not request real icon URLs from Google Play')
    args=parser.parse_args()
    out=HERE/'victoriumsoft-v17-output'
    if out.exists():shutil.rmtree(out)
    out.mkdir()
    if args.source:
        source=Path(args.source).resolve()
    else:
        print('Downloading current public GitHub repo. No token required...')
        source=download_repo(out/'_download')
    if not (source/'index.html').exists(): raise RuntimeError('Source must contain index.html')
    site=out/'victoriumsoft-site'
    shutil.copytree(source,site,ignore=shutil.ignore_patterns('.git','node_modules','.DS_Store'))
    changed=set()
    # App icon fetch and fallback
    ensure_icons(site,not args.offline)
    for slug in ('varnyx','utopiax-oracle','meravix'):
        changed.add(f'assets/apps/published/{slug}-icon.png')
    # Preserve all original site HTML and JS, touching only metadata/copy/status sections.
    path=site/'index.html';old=read(path);new=cindex(old)
    if old!=new:write(path,new);changed.add('index.html')
    for slug in ('varnyx','utopiax-oracle'):
        p=site/'apps'/f'{slug}.html'
        if p.exists():
            old=read(p);new=upgrade_old_page(old,PUB[slug]);write(p,new);changed.add(f'apps/{slug}.html')
    p=site/'apps/meravix.html'
    if not p.exists(): write(p,new_meravix());changed.add('apps/meravix.html')
    # Update outdated brand titles on affected app pages only (without removing other content).
    for slug in ('arcpitch','orbcascade'):
        p=site/'apps'/f'{slug}.html'
        if p.exists():
            s=read(p)
            s=re.sub(r'<h1>[^<]*</h1>',f'<h1>{escape(PUB[slug][1])}</h1>',s,count=1)
            if slug=='orbcascade': s=s.replace('OrbCascade: Bubble Shooter','OrbCascade: Reflex Arcade')
            write(p,s);changed.add(f'apps/{slug}.html')
    for path,(title,desc) in PAGES.items():
        p=site/path
        if not p.exists():
            print(f'[skip] {path}: not in source repo');continue
        seo=None
        if path=='index.html': seo=home_schemas()
        elif path.startswith('apps/') and Path(path).stem in PUB: seo=app_schemas(PUB[Path(path).stem])
        elif not path.startswith('apps/'): seo=informative_schema(path)
        content=add_seo_head(read(p),path,title,desc,Path(path).stem not in TEST_APPS,seo,site)
        write(p,content);changed.add(path)
    # 404 must NOT be indexed.
    p=site/'404.html'
    if p.exists():
        s=read(p);s=re.sub(r'<meta\s+name="robots"[^>]*>', '',s,flags=re.I)
        s=s.replace('</head>','<meta name="robots" content="noindex,follow" /></head>',1)
        write(p,s);changed.add('404.html')
    p=site/'script.js'
    if p.exists():write(p,translations(read(p)));changed.add('script.js')
    css_update(site);changed.add('style.css')
    update_sw(site);changed.add('service-worker.js')
    build_sitemap(site);changed.update(['sitemap.xml','robots.txt'])
    validate(site)
    full,patch=make_outputs(site,changed,out)
    report=(
      '# VictoriumSoft SEO v17 — Kurulum ve Değişiklikler\n\n'
      'Güncel halka açık uygulama portföyü: 12 Google Play ürünü; 5 proje kapalı testte.\n\n'
      'Sabit ve taranabilir title, description, canonical, Open Graph, Twitter Card; Organization, WebSite, ItemList ve MobileApplication yapılandırılmış verileri.\n'
      'Gerçek olmayan rating/review verileri eklenmedi. Eski linkler ve JavaScript/CSS özellikleri silinmedi.\n'
      'Kapalı testteki 5 bilgi sayfası noindex,follow olarak ayarlandı; sitemap sadece herkese açık içerik içerir.\n'
      'Varolan Google site verification etiketi korunur.\n\n'
      'Güncel simgeler önce resmî Play Store meta görselinden indirilmeye çalışılır. İndirilemezse:\n'
      '- VARNYX/UtopiaX: kullanıcı tarafından sağlanmış eski Play Console ekran görüntüsündeki simge kırpıntısı kullanılır.\n'
      '- MeraVix: üzerinde GEÇİCİ SİMGE yazan geçici marka sembolü kullanılır. Bunu gerçek Google Play ikonu ile değiştirin.\n\n'
      '### Yayınlama\n'
      '1. `victoriumsoft-v17-SEO-PATCH.zip` dosyasını çıkartın.\n'
      '2. İçindeki **dosyalar ve klasörleri** GitHub repo köküne yollarını koruyarak yükleyin (ZIP dosyasının kendisini değil).\n'
      '3. GitHub Commit changes ile tamamlayın. Vercel otomatik yayınlar.\n'
      '4. Search Console URL Denetimi ile ana sayfayı ve yeni üç uygulama sayfasını indekslemeye gönderin.\n'
      '5. Rich Results Test ile yapılandırılmış verileri kontrol edin. Google sıralaması garanti edilmez.\n'
      f'\nCanonical: {DOMAIN}/\nSitemap: {DOMAIN}/sitemap.xml\n'
      )
    write(out/'SEO-V17-KURULUM.md',report)
    print('DONE:',out)

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('ERROR:',e, file=sys.stderr)
        raise
