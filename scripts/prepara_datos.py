# -*- coding: utf-8 -*-
"""Separa comentarios por post y calcula señales estadísticas:
duplicados, cuentas repetidas, ráfagas temporales y frecuencias de palabras."""
import json, re, collections, os
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

meta = json.load(open(os.path.join(DATA, "posts_metadata.json"), encoding="utf-8"))
comments = json.load(open(os.path.join(DATA, "comments_raw.json"), encoding="utf-8"))

# mapa inputUrl -> clave del post
url_a_clave = {}
for p in meta["posts"]:
    url_a_clave[p["url"].rstrip("/")] = p["clave"]
    if "url_canonica" in p:
        url_a_clave[p["url_canonica"].rstrip("/")] = p["clave"]

por_post = collections.defaultdict(list)
sin_match = 0
for c in comments:
    clave = url_a_clave.get((c.get("inputUrl") or "").rstrip("/"))
    if not clave:
        sin_match += 1
        continue
    por_post[clave].append({
        "texto": (c.get("text") or "").strip(),
        "fecha": c.get("date"),
        "likes": c.get("likesCount") or 0,
        "autor_id": c.get("profileId") or "",
        "autor": c.get("profileName") or "",
        "respuestas": c.get("commentsCount") or 0,
        "es_respuesta": (c.get("threadingDepth") or 0) > 0,
    })

os.makedirs(os.path.join(DATA, "comments_by_post"), exist_ok=True)
for clave, lst in por_post.items():
    with open(os.path.join(DATA, "comments_by_post", clave + ".json"), "w", encoding="utf-8") as f:
        json.dump(lst, f, ensure_ascii=False, indent=1)

# ---------- señales de comportamiento atípico ----------
STOP = set("""de la que el en y a los del se las por un para con no una su al lo como mas más pero sus le ya o
este si porque esta entre cuando muy sin sobre también me hasta hay donde quien desde todo nos durante todos uno
les ni contra otros ese eso ante ellos e esto mí antes algunos qué unos yo otro otras otra él tanto esa estos
mucho quienes nada muchos cual poco ella estar estas algunas algo nosotros mi mis tú te ti tu tus ellas nosotras
vosotros vosotras os mío mía míos mías tuyo tuya tuyos tuyas suyo suya suyos suyas nuestro nuestra nuestros
nuestras vuestro vuestra vuestros vuestras esos esas es era eres fue ser son está están estás estoy he ha han
hemos va van vamos voy dios jaja jajaja jajajaja q x d k pa https http www com facebook""".split())

def tokens(t):
    t = re.sub(r"http\S+", " ", t.lower())
    return [w for w in re.findall(r"[a-záéíóúüñ#]{3,}", t) if w not in STOP]

senales = {}
freq_global = collections.Counter()
for clave, lst in por_post.items():
    textos = [c["texto"] for c in lst if c["texto"]]
    # duplicados exactos (normalizados)
    norm = collections.Counter(re.sub(r"\s+", " ", t.lower()) for t in textos if len(t) > 12)
    duplicados = {t: n for t, n in norm.items() if n >= 3}
    # cuentas que comentan repetidamente
    autores = collections.Counter(c["autor_id"] for c in lst if c["autor_id"])
    repetidores = {a: n for a, n in autores.items() if n >= 4}
    # ráfagas: comentarios por hora
    horas = collections.Counter()
    for c in lst:
        if c["fecha"]:
            horas[c["fecha"][:13]] += 1
    top_horas = horas.most_common(3)
    pico = top_horas[0][1] if top_horas else 0
    # frecuencias de palabras
    freq = collections.Counter()
    for t in textos:
        freq.update(tokens(t))
    freq_global.update(freq)
    # serie temporal en hora local BCS (UTC-7): por hora si la actividad cabe en 72h, si no por día
    fechas = sorted(datetime.strptime(c["fecha"][:19], "%Y-%m-%dT%H:%M:%S")
                    for c in lst if c["fecha"])
    serie = {"unidad": None, "buckets": [], "pct_primeras_24h": None}
    if fechas:
        from datetime import timedelta
        fechas = [f - timedelta(hours=7) for f in fechas]
        ini, fin = fechas[0], fechas[-1]
        en24 = sum(1 for f in fechas if f <= ini + timedelta(hours=24))
        serie["pct_primeras_24h"] = round(100 * en24 / len(fechas), 1)
        if (fin - ini) <= timedelta(hours=72):
            serie["unidad"] = "hora"
            paso, fmt_b = timedelta(hours=1), "%Y-%m-%d %H:00"
            cur = ini.replace(minute=0, second=0)
        else:
            serie["unidad"] = "día"
            paso, fmt_b = timedelta(days=1), "%Y-%m-%d"
            cur = ini.replace(hour=0, minute=0, second=0)
        conteo = collections.Counter(f.strftime(fmt_b) for f in fechas)
        while cur <= fin:
            k = cur.strftime(fmt_b)
            serie["buckets"].append([k, conteo.get(k, 0)])
            cur += paso
    senales[clave] = {
        "serie_temporal": serie,
        "n_comentarios": len(lst),
        "n_con_texto": len(textos),
        "autores_unicos": len(autores),
        "duplicados_3omas": duplicados,
        "cuentas_4omas_comentarios": repetidores,
        "pico_comentarios_en_1h": pico,
        "top_horas": top_horas,
        "top_palabras": freq.most_common(60),
    }

with open(os.path.join(DATA, "senales_estadisticas.json"), "w", encoding="utf-8") as f:
    json.dump({"por_post": senales, "top_palabras_global": freq_global.most_common(120),
               "comentarios_sin_match": sin_match}, f, ensure_ascii=False, indent=1)

print("sin_match:", sin_match)
for clave, s in sorted(senales.items(), key=lambda kv: -kv[1]["n_comentarios"]):
    print(f"{clave}: {s['n_comentarios']} coments, {s['autores_unicos']} autores, "
          f"dups>=3: {len(s['duplicados_3omas'])}, repetidores>=4: {len(s['cuentas_4omas_comentarios'])}, "
          f"pico 1h: {s['pico_comentarios_en_1h']}")
print("top global:", [w for w, _ in freq_global.most_common(15)])
