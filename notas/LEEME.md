# Cómo agregar o editar una nota de la bitácora

Cada nota es un archivo `notas/<slug>.json`. El script genera la página, la tarjeta del índice y el `sitemap.xml`.

## Agregar una nota
1. Copia `notas/_plantilla.json.ejemplo` a `notas/<slug>.json` (el nombre debe coincidir con el campo `slug`).
2. Edita el contenido.
3. Desde la raíz del proyecto: `python3 tools/build_notas.py`
4. Revisa en local (`python3 -m http.server 4173`) y haz commit.

## Campos
| Campo | Obligatorio | Uso |
|---|---|---|
| `orden` | sí | Posición en la bitácora y en "nota anterior/siguiente". No se puede repetir. |
| `slug` | sí | URL: `bitacora/<slug>.html`. Solo minúsculas, números y guiones. No lo cambies después de publicar (rompe enlaces). |
| `categoria` | sí | Etiqueta sobre el título. |
| `icono` | sí | Uno de los iconos del proyecto (`i-cmdb`, `i-monitor`, `i-incident`, `i-endpoint`, `i-service`, `i-bmc`, `i-integration`, ...). El script avisa si no existe. |
| `titulo`, `resumen`, `extracto` | sí | Título; resumen de la tarjeta y meta descripción; texto bajo el título. |
| `secciones` | sí | Lista de `{ "titulo", "parrafos": [...], "codigo": [...] }`. `codigo` es opcional y se muestra en bloques copiables. |
| `referencias` | no | Lista de `{ "texto", "url" }`. Abren en pestaña nueva. La URL debe empezar por `https://`. |

## Reglas
- El texto es plano; el script escapa `&`, `<` y `>` automáticamente.
- Si borras un `.json`, borra también su `bitacora/<slug>.html` (el script no elimina páginas).
- No edites a mano `bitacora/*.html`, el bloque entre `<!-- notas:inicio -->` y `<!-- notas:fin -->` de `index.html` ni `sitemap.xml`: se sobrescriben.
- Si el dominio cambia, actualiza `DOMINIO` en `tools/build_notas.py`.
