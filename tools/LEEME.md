# Herramientas del proyecto

Todas usan solo Python 3 (ya incluido en macOS). Se ejecutan desde la raíz del proyecto.

## `build_notas.py`
Genera la bitácora desde `notas/*.json`. Ver `notas/LEEME.md`.

## `verificar_enlaces.py`
Revisa los enlaces de `index.html`, `404.html` y `bitacora/*.html`.

```
python3 tools/verificar_enlaces.py                  # internos + externos (necesita internet)
python3 tools/verificar_enlaces.py --solo-internos  # sin red, rápido
```

- **Internos y recursos locales** (CSS, JS, imágenes, PDF, anclas `#id`): ROTO si el archivo o el ancla no existe.
- **Externos `https`**: OK si responde con éxito (sigue redirecciones); ROTO si da 404 u otro error del servidor; NO VERIFICABLE si el sitio bloquea a los scripts (403, 429, 999…) o hay fallo de red. Esos hay que abrirlos a mano.
- **`mailto:` y `tel:`**: solo se valida el formato.
- Termina con código 1 si hay enlaces rotos, así puede usarse antes de publicar.

Limitaciones: LinkedIn siempre sale como no verificable. El enlace de WhatsApp Web (`web.whatsapp.com`) lo construye `js/main.js` al pulsar el botón y no está en el HTML, por lo que no se revisa. Que una página responda 200 no garantiza que su contenido siga siendo el mismo.
