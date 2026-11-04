"""Gera a pasta docs/ (GitHub Pages) com o PWA do StayScore a partir de stayscore.html."""
import os, re, shutil
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
os.makedirs(OUT, exist_ok=True)

page = open(os.path.join(ROOT, "stayscore.html"), encoding="utf-8").read()
page = page.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")

head = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#1e9b57" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0f1713" media="(prefers-color-scheme: dark)">
<meta name="description" content="StayScore: nota de 0 a 100, ocupação, diária e receita estimadas para aluguel por temporada no Rio de Janeiro.">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="StayScore">
<style>:root{color-scheme:light dark;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)} img{max-width:100%} [hidden]{display:none!important}</style>
<script src="listings.js"></script>
</head>
<body>
"""
tail = """
<script>
if ("serviceWorker" in navigator) { window.addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {})); }
</script>
</body>
</html>
"""
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(head + page + tail)

open(os.path.join(OUT, "manifest.webmanifest"), "w", encoding="utf-8").write("""{
  "name": "StayScore",
  "short_name": "StayScore",
  "description": "Inteligência de mercado para aluguel por temporada",
  "start_url": "./index.html",
  "scope": "./",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#f4f6f4",
  "theme_color": "#1e9b57",
  "lang": "pt-BR",
  "icons": [
    {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
    {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
    {"src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}
  ]
}
""")

open(os.path.join(OUT, "sw.js"), "w", encoding="utf-8").write("""const CACHE = "stayscore-v3";
const ASSETS = ["./", "./index.html", "./manifest.webmanifest", "./listings.js", "./icons/icon-192.png", "./icons/icon-512.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())); });
self.addEventListener("activate", e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (url.origin !== location.origin) return;               // mapas, fontes e Nominatim vão direto à rede
  e.respondWith(fetch(e.request).then(r => { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return r; })
    .catch(() => caches.match(e.request).then(r => r || caches.match("./index.html"))));
});
""")

# listings.js: placeholder até os dados reais do Inside Airbnb serem convertidos
lj = os.path.join(OUT, "listings.js")
if not os.path.exists(lj):
    open(lj, "w", encoding="utf-8").write("// Gerado por preparar_inside_airbnb.py. Enquanto vazio, o app usa a base de demonstração.\nwindow.LISTINGS_DATA = [];\nwindow.LISTINGS_DATE = \"\";\n")

# ícones
icons = os.path.join(OUT, "icons"); os.makedirs(icons, exist_ok=True)
def icon(size, maskable=False):
    im = Image.new("RGBA", (size, size), (30, 155, 87, 255))
    d = ImageDraw.Draw(im)
    if not maskable:
        im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, size - 1, size - 1], radius=size * 0.22, fill=(30, 155, 87, 255))
    s = size; cx = s / 2
    pad = 0.30 if maskable else 0.22
    # casa: telhado + corpo
    top = s * pad; bottom = s * (1 - pad); w = s * (1 - 2 * pad)
    d.polygon([(cx, top), (cx - w * 0.55, top + w * 0.42), (cx + w * 0.55, top + w * 0.42)], fill="white")
    d.rectangle([cx - w * 0.42, top + w * 0.38, cx + w * 0.42, bottom], fill="white")
    # arco de score dentro da casa
    r = w * 0.26; cy = top + w * 0.78
    d.arc([cx - r, cy - r, cx + r, cy + r], start=180, end=360, fill=(30, 155, 87, 255), width=max(3, int(s * 0.05)))
    d.arc([cx - r, cy - r, cx + r, cy + r], start=180, end=320, fill=(21, 122, 65, 255), width=max(3, int(s * 0.05)))
    return im
icon(192).save(os.path.join(icons, "icon-192.png"))
icon(512).save(os.path.join(icons, "icon-512.png"))
icon(180, maskable=True).save(os.path.join(icons, "apple-touch-icon.png"))
icon(512, maskable=True).save(os.path.join(icons, "icon-maskable-512.png"))
open(os.path.join(OUT, ".nojekyll"), "w").close()
print("PWA gerado em", OUT)
