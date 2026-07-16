# Análisis de conversación digital — Pancho Pelayo

Análisis de la conversación en Facebook de la página `FranciscoPelayoCovarrubias` (11 publicaciones, 1,862 comentarios) realizado por **Púrpura Solutions**: sentimiento, temas, críticas, atributos, detección de ataques orquestados y comparativo de narrativas, con un reporte HTML interactivo autocontenido como entregable.

**📊 Ver el reporte:** https://gchavez83.github.io/pancho-pelayo-scrapper/

## Pipeline

```bash
python scripts/prepara_datos.py       # comments_raw → comments_by_post + señales estadísticas
python scripts/consolida_analisis.py  # metadata + señales + analysis/* → consolidado.json
python scripts/genera_reporte.py      # consolidado.json + plantilla → reporte/reporte_pancho_pelayo.html
```

Los cambios visuales se hacen en `reporte/plantilla.html`; los textos del resumen ejecutivo y recomendaciones viven en `scripts/consolida_analisis.py`.

## Datos

La extracción se hizo con [Apify](https://apify.com) (`facebook-posts-scraper` y `facebook-comments-scraper`). Los datos crudos e intermedios (`data/comments_raw.json`, `data/comments_by_post/`, `data/analysis/`, `data/senales_estadisticas.json`, `data/consolidado.json`) **no se versionan** porque contienen nombres e IDs de perfiles reales; el pipeline los regenera localmente a partir de la extracción.

---

© Púrpura Solutions · 2026
