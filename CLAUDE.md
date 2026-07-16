# Pancho Pelayo Scrapper

Análisis de conversación digital en Facebook para el cliente **Francisco "Pancho" Pelayo Covarrubias** (político PAN, Baja California Sur, rumbo a la gubernatura 2027). Página analizada: `FranciscoPelayoCovarrubias`. Proyecto de **Púrpura Solutions**.

## Qué hace

Extrae publicaciones y comentarios de Facebook vía Apify, los analiza (sentimiento, temas, críticas, atributos, ataques orquestados, comparativo de narrativas) y genera un reporte HTML interactivo autocontenido.

## Estructura

```
instrucciones.txt        Brief del cliente: 11 URLs de posts + requisitos del reporte
Purpura_LogoFull.png     Logo (identidad de marca; púrpura #684d9b)
data/
  posts_metadata.json    Metadatos reales de los 11 posts (reacciones, comentarios, shares, textos)
  comments_raw.json      1,862 comentarios crudos descargados de Apify (CONTIENE DATOS PERSONALES)
  comments_by_post/      Comentarios separados por post (clave.json)
  analysis/              Análisis por post generado con IA (sentimiento, temas, críticas…)
  senales_estadisticas.json  Duplicados, ráfagas, cuentas repetidas, frecuencias de palabras
  consolidado.json       Todo fusionado + narrativas + resumen ejecutivo (input del reporte)
  logo_b64.txt           Logo optimizado en base64 (se incrusta en el HTML)
scripts/
  prepara_datos.py       comments_raw → comments_by_post + señales + series temporales
  consolida_analisis.py  metadata + señales + analysis/* → consolidado.json (incluye resumen ejecutivo y recomendaciones EDITABLES aquí)
  genera_reporte.py      consolidado.json + plantilla.html → reporte final
reporte/
  plantilla.html         Plantilla con placeholders /*__DATA__*/ y /*__LOGO__*/
  reporte_pancho_pelayo.html  ENTREGABLE (autocontenido, no editar a mano)
```

## Pipeline (regenerar el reporte)

```bash
python scripts/prepara_datos.py
python scripts/consolida_analisis.py
python scripts/genera_reporte.py
```

Cualquier cambio visual se hace en `reporte/plantilla.html` y se regenera con `genera_reporte.py`. Los textos del resumen ejecutivo y recomendaciones viven en `consolida_analisis.py` (constantes `RESUMEN_EJECUTIVO` y `RECOMENDACIONES`).

## Extracción con Apify (MCP)

- Sonda barata de conteos: `apify/facebook-posts-scraper` — $0.004/post; acepta URLs `reel/` y `share/p/` directas.
- Comentarios: `apify/facebook-comments-scraper` — $0.002/comentario; usar `includeNestedComments: true` y `viewOption: RANKED_UNFILTERED`.
- Flujo acordado con el usuario: **sonda → checkpoint de costo real → extracción**. Siempre poner `maxTotalChargeUsd` como tope.
- Facebook reporta más comentarios de los públicamente visibles (~20% son borrados/filtrados); el reporte muestra ambas cifras ("disponibles y analizados").

## Reporte HTML

- Un solo archivo, sin dependencias externas (logo y datos embebidos), es-MX, modo claro/oscuro.
- Identidad Púrpura: `#684d9b` (oscuro `#8f76cb`); rampa validada `#4a3572/#684d9b/#8163b4/#9d87d3` (invertida en dark). Sentimiento: positivo púrpura, negativo rojo `#e34948`, neutro gris.
- Filtro por post: chips envueltos en escritorio, `<select>` nativo en ≤640px (el usuario NO quiere scroll horizontal en el segmentador).
- Nube de palabras: colocación en espiral con colisiones (forma de nube real).
- Comentarios representativos: ligados a autor real (avatar de iniciales + link a perfil y al comentario).
- Gráfica temporal por post: comentarios por día, hora local BCS (UTC-7), % en primeras 24h.

## Convenciones y pendientes

- Todo en español (código, datos, reporte). Cifras con formato es-MX.
- Presupuesto Apify: cuenta con ~$29 USD restantes (tope autorizado $49). Gastado a la fecha: ~$3.85.
- **PENDIENTE (2026-07-16)**: subir a GitHub. ⚠️ Antes de hacer el repo público: `data/comments_raw.json`, `data/comments_by_post/` y `data/consolidado.json` contienen nombres y IDs de perfiles reales — valorar `.gitignore` o repo privado.
