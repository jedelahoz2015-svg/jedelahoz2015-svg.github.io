#!/usr/bin/env python3
"""Verifica los enlaces del portafolio.

Uso (desde la raíz del proyecto):
    python3 tools/verificar_enlaces.py                 # internos + externos
    python3 tools/verificar_enlaces.py --solo-internos # sin red

Comprueba:
  - Enlaces internos: que el archivo exista y que el ancla (#id) exista en la página destino.
  - Recursos locales (CSS, JS, imágenes, PDF): que el archivo exista.
  - Enlaces externos https: que respondan con éxito (sigue redirecciones).
  - mailto: y tel: solo se valida el formato.

Resultados: OK, ROTO (error confirmado) y NO VERIFICABLE (el sitio bloquea a los scripts
o hubo un fallo de red; hay que abrirlo a mano). Termina con código 1 si hay enlaces ROTOS.
Solo usa la biblioteca estándar de Python 3.
"""
import argparse
import re
import socket
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urldefrag, urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
# Códigos con los que un sitio rechaza a los scripts aunque la página exista
BLOQUEO = {401, 403, 405, 406, 429, 451, 999}
SIN_VERIFICAR_DOMINIOS = {"www.linkedin.com", "linkedin.com"}  # exige sesión: siempre responde 999/redirige a login


class Pagina(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.enlaces, self.recursos = set(), [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("href"):
            self.enlaces.append(a["href"])
        elif tag == "link" and a.get("href") and a.get("rel") not in ("canonical",):
            self.recursos.append(a["href"])
        elif tag in ("script", "img", "source") and a.get("src"):
            self.recursos.append(a["src"])
        elif tag == "use" and a.get("href", "").startswith("#"):
            self.enlaces.append(a["href"])  # <use href="#icono"> debe existir en la página


def analizar(ruta):
    p = Pagina()
    p.feed(ruta.read_text(encoding="utf-8"))
    return p


def archivos_html():
    return sorted([ROOT / "index.html", ROOT / "404.html", *sorted((ROOT / "bitacora").glob("*.html"))])


def resolver_local(origen, href):
    """Devuelve (ruta_archivo, ancla) para un enlace relativo o absoluto desde la raíz."""
    base, ancla = urldefrag(href)
    base = unquote(base)
    if not base:
        return origen, ancla
    destino = ROOT / base.lstrip("/") if base.startswith("/") else (origen.parent / base)
    destino = destino.resolve()
    if destino.is_dir():
        destino = destino / "index.html"
    return destino, ancla


def revisar_internos(paginas):
    resultados = []  # (estado, pagina, enlace, detalle)
    for origen, p in paginas.items():
        rel = origen.relative_to(ROOT)
        for href in p.enlaces + p.recursos:
            if re.match(r"^(https?:|mailto:|tel:|data:|javascript:)", href) or href.startswith("//"):
                continue
            destino, ancla = resolver_local(origen, href)
            if not destino.exists():
                resultados.append(("ROTO", rel, href, "el archivo no existe"))
                continue
            if ancla and destino.suffix == ".html":
                ids = paginas[destino].ids if destino in paginas else analizar(destino).ids
                if ancla not in ids:
                    resultados.append(("ROTO", rel, href, f"no existe el ancla #{ancla}"))
                    continue
            resultados.append(("OK", rel, href, ""))
    return resultados


def probar_externo(url):
    host = urlparse(url).hostname or ""
    if host in SIN_VERIFICAR_DOMINIOS:
        return ("NO VERIFICABLE", "LinkedIn bloquea la verificación automática; ábrelo a mano")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "es,en;q=0.8"})
    for intento in range(2):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                cuerpo = r.read(80000).decode("utf-8", "ignore")
                titulo = re.search(r"<title[^>]*>(.*?)</title>", cuerpo, re.S | re.I)
                titulo = re.sub(r"\s+", " ", titulo.group(1)).strip()[:70] if titulo else "(sin título)"
                if re.search(r"not found|no encontrad|404", titulo, re.I):
                    return ("ROTO", f"responde {r.status} pero el título indica error: {titulo}")
                final = "" if r.geturl().rstrip("/") == url.rstrip("/") else f" → redirige a {r.geturl()}"
                return ("OK", f"{r.status} · {titulo}{final}")
        except urllib.error.HTTPError as e:
            if e.code in BLOQUEO:
                return ("NO VERIFICABLE", f"HTTP {e.code}: el sitio bloquea a los scripts; ábrelo a mano")
            if e.code >= 500 and intento == 0:
                continue
            return ("ROTO", f"HTTP {e.code}")
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
            if intento == 0:
                continue
            return ("NO VERIFICABLE", f"fallo de red: {getattr(e, 'reason', e)}")
    return ("NO VERIFICABLE", "sin respuesta")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--solo-internos", action="store_true", help="no hace peticiones de red")
    args = ap.parse_args()

    paginas = {f: analizar(f) for f in archivos_html() if f.exists()}
    internos = revisar_internos(paginas)
    rotos_int = [r for r in internos if r[0] == "ROTO"]
    print(f"Páginas revisadas: {len(paginas)}")
    print(f"Enlaces y recursos internos: {len(internos)} · rotos: {len(rotos_int)}")
    for _, pag, href, det in rotos_int:
        print(f"  ROTO  {pag}: {href} ({det})")

    formato = []
    externos = {}
    for origen, p in paginas.items():
        rel = str(origen.relative_to(ROOT))
        for href in p.enlaces:
            if href.startswith("mailto:"):
                if not re.fullmatch(r"mailto:[^@\s?]+@[^@\s?]+\.[^@\s?]+(\?.*)?", href):
                    formato.append((rel, href))
            elif href.startswith("tel:"):
                if not re.fullmatch(r"tel:\+\d{8,15}", href):
                    formato.append((rel, href))
            elif href.startswith("https://") or href.startswith("http://"):
                externos.setdefault(href, set()).add(rel)
                if href.startswith("http://"):
                    formato.append((rel, f"{href} (usa http, no https)"))
    print(f"mailto/tel con formato incorrecto: {len(formato)}")
    for rel, h in formato:
        print(f"  FORMATO  {rel}: {h}")

    rotos_ext = 0
    if args.solo_internos:
        print(f"Enlaces externos únicos: {len(externos)} (omitidos por --solo-internos)")
    else:
        print(f"Enlaces externos únicos: {len(externos)} (comprobando…)")
        urls = sorted(externos)
        with ThreadPoolExecutor(max_workers=6) as ex:
            res = list(ex.map(probar_externo, urls))
        orden = {"ROTO": 0, "NO VERIFICABLE": 1, "OK": 2}
        for (estado, det), url in sorted(zip(res, urls), key=lambda x: (orden[x[0][0]], x[1])):
            donde = ", ".join(sorted(externos[url]))
            print(f"  {estado:<14} {url}\n{'':17}{det}  [{donde}]")
        rotos_ext = sum(1 for e, _ in res if e == "ROTO")
        print(
            f"Externos: {sum(1 for e, _ in res if e == 'OK')} OK · {rotos_ext} rotos · "
            f"{sum(1 for e, _ in res if e == 'NO VERIFICABLE')} no verificables"
        )

    if rotos_int or rotos_ext or formato:
        print("\nHay enlaces con problemas.")
        sys.exit(1)
    print("\nSin enlaces rotos.")


if __name__ == "__main__":
    main()
