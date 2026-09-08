from __future__ import annotations

import io
import os
import re
from pathlib import Path
from urllib.parse import quote

import qrcode
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps

BASE_URL = "https://sbellomo79.github.io/Viaggio-in-Puglia"
ROOT = Path(__file__).resolve().parents[1]

CITIES = {
    "bari": "Bari",
    "gallipoli": "Gallipoli",
    "altamura": "Altamura",
    "ostuni": "Ostuni",
    "locorotondo": "Locorotondo",
    "martina-franca": "Martina Franca",
    "monopoli": "Monopoli",
    "polignano-a-mare": "Polignano a Mare",
    "grottaglie": "Grottaglie",
    "alberobello": "Alberobello",
    "otranto": "Otranto",
    "trani": "Trani",
    "vieste": "Vieste",
    "taranto": "Taranto",
    "modugno": "Modugno",
}

SEARCH_TERMS = {
    "bari": "Bari Puglia old town harbor",
    "gallipoli": "Gallipoli Puglia old town sea",
    "altamura": "Altamura Puglia cathedral old town",
    "ostuni": "Ostuni Puglia white city",
    "locorotondo": "Locorotondo Puglia panorama",
    "martina-franca": "Martina Franca Puglia old town",
    "monopoli": "Monopoli Puglia harbor old town",
    "polignano-a-mare": "Polignano a Mare Puglia cliffs sea",
    "grottaglie": "Grottaglie Puglia ceramic district",
    "alberobello": "Alberobello Puglia trulli",
    "otranto": "Otranto Puglia harbor cathedral",
    "trani": "Trani Puglia harbor cathedral",
    "vieste": "Vieste Puglia old town sea",
    "taranto": "Taranto Puglia waterfront old town",
    "modugno": "Modugno Puglia old town",
}

UA = "Viaggio-in-Puglia/1.0 (GitHub Pages project)"


def font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def text_center(draw: ImageDraw.ImageDraw, xy, text, fnt, fill):
    draw.text(xy, text, font=fnt, fill=fill, anchor="mm")


def wikimedia_image(city: str):
    params = {
        "action": "query",
        "generator": "search",
        "gsrnamespace": 6,
        "gsrsearch": SEARCH_TERMS[city],
        "gsrlimit": 8,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "format": "json",
    }
    r = requests.get("https://commons.wikimedia.org/w/api.php", params=params, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    data = r.json()
    pages = list((data.get("query") or {}).get("pages", {}).values())
    # Prefer landscape photos with normal file extensions.
    pages.sort(key=lambda p: 0 if str(p.get("title", "")).lower().endswith((".jpg", ".jpeg", ".png")) else 1)
    for p in pages:
        info = (p.get("imageinfo") or [{}])[0]
        url = info.get("url")
        if not url:
            continue
        meta = info.get("extmetadata") or {}
        artist = (meta.get("Artist") or {}).get("value", "")
        license_name = (meta.get("LicenseShortName") or {}).get("value", "")
        source = f"https://commons.wikimedia.org/wiki/{quote(p.get('title','').replace(' ', '_'))}"
        try:
            img_r = requests.get(url, headers={"User-Agent": UA}, timeout=45)
            img_r.raise_for_status()
            im = Image.open(io.BytesIO(img_r.content)).convert("RGB")
            return im, {
                "title": p.get("title", ""),
                "author": re.sub(r"<[^>]+>", "", artist).strip() or "Autore non indicato",
                "license": re.sub(r"<[^>]+>", "", license_name).strip() or "Licenza indicata su Wikimedia Commons",
                "source": source,
            }
        except Exception:
            continue
    return None, None


def fallback_background(city: str):
    im = Image.new("RGB", (1200, 900), "#cfdcd4")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 510, 1200, 900], fill="#a6b79d")
    d.rectangle([0, 440, 1200, 540], fill="#d8c7aa")
    if city == "altamura":
        for x, h in [(70,180),(220,230),(850,200),(1010,155)]:
            d.rectangle([x, 500-h, x+130, 500], fill="#e6d7bc")
        d.rectangle([420, 260, 780, 500], fill="#d1b995")
        d.polygon([(390,260),(810,260),(600,120)], fill="#b19672")
        d.ellipse([540,225,660,345], outline="#f5eddf", width=14)
    elif city == "locorotondo":
        d.ellipse([310,250,890,590], fill="#ded7c8")
        for i in range(10):
            x=90+i*110
            d.rounded_rectangle([x,460-(i%3)*28,x+95,560-(i%3)*28], radius=12, fill="#f6f3e9")
        d.rectangle([585,180,615,390], fill="#ae9576")
        d.polygon([(560,180),(640,180),(600,120)], fill="#9a8063")
        for x in range(80,1150,150):
            d.line([x,600,x+80,850], fill="#718d66", width=8)
    elif city == "grottaglie":
        d.rectangle([0,0,350,670], fill="#c7b292")
        d.rectangle([850,0,1200,670], fill="#e2d1b5")
        d.polygon([(350,670),(850,670),(960,900),(240,900)], fill="#a98c6c")
        pottery=[(170,600,"#7e9f99"),(330,690,"#c88d5c"),(885,600,"#6d8fa2"),(1040,690,"#c7a067"),(600,800,"#769169")]
        for x,y,c in pottery:
            d.ellipse([x-58,y-70,x+58,y+70], fill=c, outline="#705b46", width=7)
    elif city == "otranto":
        d.rectangle([0,585,1200,900], fill="#6297a1")
        d.rectangle([100,360,760,600], fill="#d9c5a3")
        d.rectangle([760,285,960,600], fill="#b9a17e")
        d.polygon([(300,360),(560,360),(430,230)], fill="#ad9575")
        d.ellipse([380,305,480,405], outline="#f1e8d6", width=12)
        d.rectangle([60,575,1010,615], fill="#a58b6d")
    else:
        # generic Puglian stone town with sea/land bands
        for i in range(9):
            x=60+i*120
            h=90+(i%4)*26
            d.rectangle([x,510-h,x+95,510], fill="#eadfca")
    return im, None


def make_qr(data: str):
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def make_card(city_slug: str, city_name: str):
    bg, credit = wikimedia_image(city_slug)
    if bg is None:
        bg, credit = fallback_background(city_slug)
    bg = ImageOps.fit(bg, (1200, 900), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    bg = ImageEnhance.Color(bg).enhance(1.05).filter(ImageFilter.GaussianBlur(0.5))
    overlay = Image.new("RGBA", bg.size, (255, 251, 241, 48))
    bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(bg, "RGBA")

    # Whitewash under the content to echo the wedding stationery style.
    d.rounded_rectangle([250, 115, 950, 805], radius=42, fill=(255,253,248,246), outline=(184,155,98,210), width=4)
    text_center(d, (600, 190), city_name.upper(), font(54), (78, 96, 80, 255))

    qr = make_qr(f"{BASE_URL}/{city_slug}.html")
    qr = qr.resize((430, 430), Image.Resampling.NEAREST)
    bg.paste(qr, (385, 260))
    text_center(d, (600, 728), "SCOPRI LA CITTÀ", font(30, True), (96, 98, 88, 255))
    text_center(d, (600, 767), "Il nostro viaggio in Puglia", font(25), (154, 128, 97, 255))
    return bg, credit


def update_html(city_slug: str):
    path = ROOT / f"{city_slug}.html"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    text = text.replace('href="../index.html"', f'href="{BASE_URL}/index.html"')
    # Make sure every city page uses the shared theme.
    if 'href="style.css"' not in text:
        text = text.replace('</head>', '<link rel="stylesheet" href="style.css"></head>', 1)
    # Add a QR card if the page does not already show its QR asset.
    qr_asset = f'qr-{city_slug}.png'
    if qr_asset not in text:
        block = (f'<div class="card qr-card" style="grid-column:1/-1;text-align:center;">'
                 f'<h2>Scopri {city_slug.replace("-", " ").title()}</h2>'
                 f'<img src="{qr_asset}" alt="QR code {city_name}" style="width:300px;height:300px;">'
                 f'</div>')
        text = text.replace('</div><div class="quote">', block + '</div><div class="quote">', 1)
    path.write_text(text, encoding="utf-8")
    return True


credits = [
    "QR code cards generated automatically for Viaggio in Puglia.",
    "Target format: one QR per city page, with a white quiet zone and a city-themed background.",
    "",
]

for slug, name in CITIES.items():
    out = ROOT / f"qr-{slug}.png"
    card, credit = make_card(slug, name)
    card.save(out, format="PNG", optimize=True)
    if credit:
        credits.append(f"{name}: {credit['title']} — {credit['author']} — {credit['license']} — {credit['source']}")
    else:
        credits.append(f"{name}: original illustrated fallback background generated locally (no external image source).")
    update_html(slug)

(ROOT / "IMAGE-CREDITS.txt").write_text("\n".join(credits) + "\n", encoding="utf-8")
print(f"Generated {len(CITIES)} QR cards and updated navigation.")
