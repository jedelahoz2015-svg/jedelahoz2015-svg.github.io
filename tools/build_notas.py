#!/usr/bin/env python3
"""Genera las páginas de la Bitácora técnica a partir de notas/*.json.

Uso (desde la raíz del proyecto):
    python3 tools/build_notas.py

Produce:
  - bitacora/<slug>.html   una página por nota
  - tarjetas del índice    entre <!-- notas:inicio --> y <!-- notas:fin --> en index.html
  - sitemap.xml            con la portada y todas las notas
Solo usa la biblioteca estándar de Python 3.
"""
import glob
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMINIO = "https://jesusdelahoz.com"
OG_IMAGE = f"{DOMINIO}/assets/og-image.jpg"
OG_ALT = "Jesús De La Hoz, Ingeniero de Sistemas en formación — 10.º semestre"
REQUERIDOS = ("orden", "slug", "categoria", "icono", "titulo", "resumen", "extracto", "secciones")

esc = lambda s: html.escape(s, quote=False)
esc_attr = lambda s: html.escape(s, quote=True)


def cargar():
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    iconos = set(re.findall(r'<symbol id="(i-[a-z]+)"', index))
    notas, errores = [], []
    for ruta in sorted(glob.glob(str(ROOT / "notas" / "*.json"))):
        nombre = Path(ruta).name
        try:
            n = json.loads(Path(ruta).read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errores.append(f"{nombre}: JSON inválido ({e})")
            continue
        faltan = [k for k in REQUERIDOS if k not in n]
        if faltan:
            errores.append(f"{nombre}: faltan campos {faltan}")
            continue
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", n["slug"]):
            errores.append(f"{nombre}: slug inválido (solo minúsculas, números y guiones)")
        if n["slug"] + ".json" != nombre:
            errores.append(f"{nombre}: el nombre del archivo debe ser {n['slug']}.json")
        if n["icono"] not in iconos:
            errores.append(f"{nombre}: icono '{n['icono']}' no existe. Opciones: {sorted(iconos)}")
        if not n["secciones"]:
            errores.append(f"{nombre}: la nota no tiene secciones")
        for r in n.get("referencias", []):
            if not str(r.get("url", "")).startswith("https://") or not r.get("texto"):
                errores.append(f"{nombre}: referencia inválida {r}")
        notas.append(n)
    slugs = [n["slug"] for n in notas]
    ordenes = [n["orden"] for n in notas]
    if len(set(slugs)) != len(slugs):
        errores.append("hay slugs repetidos")
    if len(set(ordenes)) != len(ordenes):
        errores.append("hay valores de 'orden' repetidos")
    if errores:
        print("No se generó nada. Corrige:\n  - " + "\n  - ".join(errores))
        sys.exit(1)
    return sorted(notas, key=lambda n: n["orden"])


def cuerpo(n):
    secciones = ""
    for s in n["secciones"]:
        parrafos = "".join(f"<p>{esc(p)}</p>" for p in s.get("parrafos", []))
        codigo = "".join(f"<pre><code>{esc(c)}</code></pre>" for c in s.get("codigo", []))
        secciones += f"<section><h2>{esc(s['titulo'])}</h2>{parrafos}{codigo}</section>"
    refs = n.get("referencias", [])
    if refs:
        lis = "".join(
            f'<li><a href="{esc_attr(r["url"])}" target="_blank" rel="noopener noreferrer">{esc(r["texto"])} <span aria-hidden="true">↗</span></a></li>'
            for r in refs
        )
        secciones += f'<aside class="article-references" aria-labelledby="referencias"><h2 id="referencias">Referencias técnicas</h2><ul>{lis}</ul></aside>'
    # mismo formato de salida que las páginas existentes
    return (
        secciones.replace("<section>", "\n          <section>")
        .replace("</section>", "\n          </section>")
        .replace("<aside", "\n          <aside")
        .replace("</aside>", "\n          </aside>")
        .replace("<li><a", "\n              <li><a")
    )


NAV = """<header class="nav" id="nav">
    <div class="container nav__inner">
      <a class="nav__brand" href="../index.html#inicio" aria-label="Jesús De La Hoz, ir al inicio">
        <span class="nav__mark" aria-hidden="true">JH</span>
        <span class="nav__name">Jesús De La Hoz</span>
      </a>
      <button class="nav__toggle" id="navToggle" type="button" aria-expanded="false" aria-controls="navMenu" aria-label="Abrir menú de navegación">
        <span class="nav__bars" aria-hidden="true"></span>
      </button>
      <nav class="nav__menu" id="navMenu" aria-label="Navegación principal">
        <ul class="nav__list">
          <li><a href="../index.html#inicio">Inicio</a></li>
          <li><a href="../index.html#sobre-mi">Sobre mí</a></li>
          <li><a href="../index.html#experiencia">Experiencia</a></li>
          <li><a href="../index.html#areas">Áreas de experiencia</a></li>
          <li><a href="../index.html#educacion">Educación</a></li>
          <li><a href="../index.html#habilidades">Habilidades</a></li>
          <li><a href="../index.html#bitacora" class="is-active" aria-current="page">Bitácora</a></li>
          <li><a href="../index.html#contacto" class="nav__cta">Contacto</a></li>
        </ul>
      </nav>
    </div>
  </header>"""

FOOT = """<footer class="footer">
    <div class="container footer__inner">
      <div>
        <p class="footer__name">Jesús De La Hoz</p>
        <p class="footer__role">Ingeniero de Sistemas en formación — 10.º semestre</p>
      </div>
      <p class="footer__copy">© <span id="year">2026</span> Jesús De La Hoz</p>
    </div>
  </footer>"""


def pagina(notas, i):
    n = notas[i]
    url = f"{DOMINIO}/bitacora/{n['slug']}.html"
    titulo, resumen = esc(n["titulo"]), esc_attr(n["resumen"])
    pn = ""
    if i > 0:
        p = notas[i - 1]
        pn += f'<a class="pn pn--prev" href="{p["slug"]}.html" rel="prev"><span>← Nota anterior</span><strong>{esc(p["titulo"])}</strong></a>'
    if i < len(notas) - 1:
        s = notas[i + 1]
        pn += f'<a class="pn pn--next" href="{s["slug"]}.html" rel="next"><span>Nota siguiente →</span><strong>{esc(s["titulo"])}</strong></a>'
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{titulo} | Jesús De La Hoz</title>
  <meta name="description" content="{resumen}">
  <meta name="author" content="Jesús De La Hoz">
  <meta name="theme-color" content="#0b1a33">
  <link rel="canonical" href="{url}">
  <link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
  <meta property="og:type" content="article">
  <meta property="og:locale" content="es_CO">
  <meta property="og:url" content="{url}">
  <meta property="og:title" content="{titulo} | Jesús De La Hoz">
  <meta property="og:description" content="{resumen}">
  <meta property="og:image" content="{OG_IMAGE}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{OG_ALT}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{titulo} | Jesús De La Hoz">
  <meta name="twitter:description" content="{resumen}">
  <meta name="twitter:image" content="{OG_IMAGE}">
  <link rel="stylesheet" href="../css/base.css">
  <link rel="stylesheet" href="../css/layout.css">
  <link rel="stylesheet" href="../css/sections.css">
  <link rel="stylesheet" href="../css/article.css">
</head>
<body>
  <a class="skip-link" href="#contenido">Saltar al contenido</a>

  {NAV}

  <main id="contenido">
    <article class="article">
      <div class="container article__shell">
        <a class="article__back" href="../index.html#bitacora"><span aria-hidden="true">←</span> Volver a la bitácora</a>
        <header class="article__head">
          <p class="eyebrow">{esc(n["categoria"])} · Bitácora técnica</p>
          <h1>{titulo}</h1>
          <p class="article__excerpt">{esc(n["extracto"])}</p>
        </header>
        <div class="article__body">{cuerpo(n)}
        </div>
        <nav class="article__pn" aria-label="Navegación entre notas">{pn}</nav>
        <div class="article__end">
          <a href="../index.html#bitacora">Explorar otras notas <span aria-hidden="true">↗</span></a>
          <a href="../index.html#contacto">Contactarme <span aria-hidden="true">↗</span></a>
        </div>
      </div>
    </article>
  </main>

  {FOOT}

  <script src="../js/main.js" defer></script>
</body>
</html>
"""


def tarjetas(notas):
    return "".join(
        f'          <li class="card note reveal"><svg class="icon" aria-hidden="true"><use href="#{n["icono"]}"/></svg>'
        f'<p class="card__kicker">{esc(n["categoria"])}</p>'
        f'<h3><a href="bitacora/{n["slug"]}.html">{esc(n["titulo"])}</a></h3><p>{esc(n["resumen"])}</p>'
        f'<div class="card__foot"><a class="note__read" href="bitacora/{n["slug"]}.html" aria-label="Leer nota: {esc_attr(n["titulo"])}">Leer nota <span aria-hidden="true">→</span></a></div></li>\n'
        for n in notas
    )


def main():
    notas = cargar()
    (ROOT / "bitacora").mkdir(exist_ok=True)
    for i, n in enumerate(notas):
        (ROOT / "bitacora" / f"{n['slug']}.html").write_text(pagina(notas, i), encoding="utf-8")

    ruta = ROOT / "index.html"
    index = ruta.read_text(encoding="utf-8")
    patron = re.compile(r"(<!-- notas:inicio -->\n).*?(\s*<!-- notas:fin -->)", re.S)
    if not patron.search(index):
        sys.exit("index.html no tiene los marcadores <!-- notas:inicio --> / <!-- notas:fin -->")
    ruta.write_text(patron.sub(lambda m: m.group(1) + tarjetas(notas).rstrip("\n") + m.group(2), index), encoding="utf-8")

    urls = [f"{DOMINIO}/"] + [f"{DOMINIO}/bitacora/{n['slug']}.html" for n in notas]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n"
    (ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    print(f"Listo: {len(notas)} notas generadas, índice y sitemap actualizados.")


if __name__ == "__main__":
    main()
