# -*- coding: utf-8 -*-
"""Fusiona posts_metadata + senales_estadisticas + analysis/*.json en un solo
JSON embebible en el reporte HTML, con agregados por narrativa y globales."""
import json, os, glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

NARRATIVAS = {
    "reel_yo_quiero": "liderazgo",
    "reel_sict_1": "contraste",
    "reel_sict_2": "contraste",
    "entrevista_huachicol": "contraste",
    "entrevista_gobernador": "propuestas",
    "reel_claro_que_se_puede": "liderazgo",
    "postal_esfuerzo": "cercanía",
    "postal_esperanza": "identidad sudcaliforniana",
    "reel_gusta_bcs": "identidad sudcaliforniana",
    "carrusel_olivos": "cercanía",
    "carrusel_csl_temo": "cercanía",
}

meta = json.load(open(os.path.join(DATA, "posts_metadata.json"), encoding="utf-8"))
senales = json.load(open(os.path.join(DATA, "senales_estadisticas.json"), encoding="utf-8"))
crudos = json.load(open(os.path.join(DATA, "comments_raw.json"), encoding="utf-8"))

import re as _re
def _norm(t):
    return _re.sub(r"\s+", " ", (t or "").strip().lower())

# índice global texto-normalizado -> autor (para ligar comentarios representativos a perfiles)
indice_autores = {}
for c in crudos:
    k = _norm(c.get("text"))
    if k and k not in indice_autores:
        indice_autores[k] = {
            "autor": c.get("profileName") or "",
            "autor_id": c.get("profileId") or "",
            "comment_url": c.get("commentUrl") or "",
        }

def enriquecer_representativos(lista):
    llaves = list(indice_autores.keys())
    for rc in lista:
        k = _norm(rc.get("texto"))
        m = indice_autores.get(k)
        if not m and len(k) >= 25:  # el agente pudo recortar la cita
            pref = k[:60]
            for kk in llaves:
                if kk.startswith(pref) or (len(kk) >= 25 and pref.startswith(kk[:60])):
                    m = indice_autores[kk]
                    break
        if m:
            rc["autor"] = m["autor"]
            rc["autor_url"] = ("https://www.facebook.com/" + m["autor_id"]) if m["autor_id"] else ""
            rc["comment_url"] = m["comment_url"]
        else:
            rc["autor"] = ""
    orden = {"positivo": 0, "negativo": 1, "neutro": 2}
    lista.sort(key=lambda rc: orden.get(rc.get("sentimiento"), 3))
    return lista

analisis = {}
faltantes = []
for p in meta["posts"]:
    ruta = os.path.join(DATA, "analysis", p["clave"] + ".json")
    if os.path.exists(ruta):
        analisis[p["clave"]] = json.load(open(ruta, encoding="utf-8"))
    else:
        faltantes.append(p["clave"])

if faltantes:
    print("FALTAN ANALISIS:", faltantes)
    raise SystemExit(1)

posts = []
for p in meta["posts"]:
    clave = p["clave"]
    a = analisis[clave]
    s = senales["por_post"][clave]
    sent = a["sentimiento"]
    tot_sent = max(1, sent["positivo"] + sent["negativo"] + sent["neutro"])
    interacciones = p["reacciones"] + p["comentarios"] + p["shares"]
    posts.append({
        "clave": clave,
        "titulo": p["titulo"],
        "url": p["url"],
        "tipo": p["tipo"],
        "narrativa": NARRATIVAS[clave],
        "fecha_publicacion": p.get("fecha_publicacion"),
        "texto": p["texto"],
        "reacciones": p["reacciones"],
        "desglose_reacciones": p.get("desglose_reacciones"),
        "comentarios_fb": p["comentarios"],
        "comentarios_analizados": s["n_comentarios"],
        "shares": p["shares"],
        "interacciones": interacciones,
        "sentimiento": sent,
        "pct_positivo": round(100 * sent["positivo"] / tot_sent, 1),
        "pct_negativo": round(100 * sent["negativo"] / tot_sent, 1),
        "temas": a["temas"],
        "criticas": a["criticas"],
        "atributos_positivos": a["atributos_positivos"],
        "comentarios_representativos": enriquecer_representativos(a["comentarios_representativos"]),
        "ataques_orquestados": a["ataques_orquestados"],
        "resumen": a["resumen"],
        "top_palabras": s["top_palabras"][:45],
        "autores_unicos": s["autores_unicos"],
        "pico_1h": s["pico_comentarios_en_1h"],
        "serie_temporal": s["serie_temporal"],
    })

# agregados por narrativa
narrs = {}
for post in posts:
    n = narrs.setdefault(post["narrativa"], {
        "narrativa": post["narrativa"], "posts": 0, "reacciones": 0,
        "comentarios": 0, "shares": 0, "interacciones": 0,
        "positivo": 0, "negativo": 0, "neutro": 0})
    n["posts"] += 1
    n["reacciones"] += post["reacciones"]
    n["comentarios"] += post["comentarios_fb"]
    n["shares"] += post["shares"]
    n["interacciones"] += post["interacciones"]
    for k in ("positivo", "negativo", "neutro"):
        n[k] += post["sentimiento"][k]
for n in narrs.values():
    n["interacciones_prom"] = round(n["interacciones"] / n["posts"])
    ts = max(1, n["positivo"] + n["negativo"] + n["neutro"])
    n["pct_positivo"] = round(100 * n["positivo"] / ts, 1)
    n["pct_negativo"] = round(100 * n["negativo"] / ts, 1)

tot = {
    "reacciones": sum(p["reacciones"] for p in posts),
    "comentarios_fb": sum(p["comentarios_fb"] for p in posts),
    "comentarios_analizados": sum(p["comentarios_analizados"] for p in posts),
    "shares": sum(p["shares"] for p in posts),
    "interacciones": sum(p["interacciones"] for p in posts),
    "positivo": sum(p["sentimiento"]["positivo"] for p in posts),
    "negativo": sum(p["sentimiento"]["negativo"] for p in posts),
    "neutro": sum(p["sentimiento"]["neutro"] for p in posts),
}
ts = max(1, tot["positivo"] + tot["negativo"] + tot["neutro"])
tot["pct_positivo"] = round(100 * tot["positivo"] / ts, 1)
tot["pct_negativo"] = round(100 * tot["negativo"] / ts, 1)

RESUMEN_EJECUTIVO = [
 "Las 11 publicaciones acumulan 20,033 reacciones, 2,321 comentarios (1,862 analizados uno por uno) y 2,871 compartidos. El sentimiento global es 60% positivo, 23% negativo y 17% neutro: una conversación dominada por la base de apoyo rumbo a 2027, con una oposición orgánica (mayormente pro-Morena) que disputa los hilos más visibles pero no controla la narrativa.",
 "El comparativo de narrativas muestra un intercambio claro entre alcance y afinidad. El contraste (SICT, huachicol) es el motor de volumen: 4,887 interacciones promedio por post, casi 10 veces más que cercanía, impulsado por el agravio compartido de las carreteras; pero es también la narrativa con el sentimiento más frágil (54.8% positivo) porque activa el contraataque (“pura lengua, anda en campaña”). En el otro extremo, cercanía e identidad sudcaliforniana generan la mejor calidad de conversación (65–66% positivo, y el único post sin un solo comentario negativo: Colonia Olivos) aunque con alcance limitado a la base dura. El liderazgo (lanzamiento y superación personal) equilibra ambos mundos: 3,506 interacciones promedio con 62% positivo.",
 "Lo que la gente le reconoce a Pancho: valentía para alzar la voz ante la federación, cercanía con la gente (“mi gallo Panchito”), perseverancia y experiencia de gobierno. Las críticas recurrentes que requieren gestión: oportunismo electoral, su gestión como alcalde de Comondú, la resistencia a la marca PAN, y —la crítica individual con más likes de todo el paquete— el señalamiento de acaparamiento de agua para sus ranchos.",
 "Sobre ataques orquestados: solo el reel de salida “Yo quiero” presenta indicios moderados de semi-coordinación (textos casi calcados entre cuentas distintas, una cuenta repitiendo 4 veces la misma burla y una oleada tardía de comentarios negativos idénticos sin likes). En las otras 10 publicaciones la crítica es orgánica, dispersa y de bajo volumen. No hay evidencia de una operación sistemática en su contra."
]
RECOMENDACIONES = [
 "Mantener el contraste como motor de alcance, pero cerrar cada pieza de denuncia con una propuesta concreta y verificable: la crítica más repetida y con más tracción es “propón en vez de atacar / anda en campaña”.",
 "Preparar de inmediato una respuesta documentada al tema del agua y los ranchos: es la crítica individual con más likes (43) del paquete y hoy no tiene contranarrativa; si escala, contamina la narrativa de cercanía.",
 "Blindar el flanco Comondú con resultados tangibles de su gestión como alcalde (obras, cifras, testimonios), pues es el ataque retrospectivo más frecuente de los detractores.",
 "Escalar el formato testimonial de cercanía a video: el testimonio de los medicamentos fue el activo más persuasivo del paquete; además, convertir las peticiones ciudadanas que emergen en los comentarios (hemodiálisis, extorsión policial) en contenido de gestión y respuesta.",
 "Apalancar el apoyo transversal detectado (“no soy panista, pero tiene razón”): construir la causa —carreteras, recursos federales— por encima del partido, porque la marca PAN genera más resistencia que la figura de Pancho.",
 "Verificar el historial de los validadores visibles antes de cada colaboración: el pasado morenista del aliado en Cabo San Lucas fue el principal ruido de esa pieza.",
 "Monitorear (sin confrontar) las cuentas del patrón semi-coordinado del reel de salida y guardar evidencia; si el patrón se repite en próximos lanzamientos, escalar a denuncia de comportamiento inauténtico ante Meta.",
 "Mezcla editorial sugerida: 2 piezas de contraste por semana para alcance + 1–2 de cercanía/identidad para afinidad y sentimiento, evitando depender solo del contraste porque erosiona el % positivo (54.8% vs 66.1%)."
]

salida = {
    "cliente": "Francisco “Pancho” Pelayo Covarrubias",
    "pagina": "FranciscoPelayoCovarrubias",
    "fecha_analisis": "2026-07-15",
    "posts": posts,
    "narrativas": sorted(narrs.values(), key=lambda n: -n["interacciones_prom"]),
    "totales": tot,
    "top_palabras_global": senales["top_palabras_global"][:80],
    "resumen_ejecutivo": RESUMEN_EJECUTIVO,
    "recomendaciones": RECOMENDACIONES,
}
with open(os.path.join(DATA, "consolidado.json"), "w", encoding="utf-8") as f:
    json.dump(salida, f, ensure_ascii=False)
print("OK consolidado.json")
for n in salida["narrativas"]:
    print(f"{n['narrativa']}: {n['posts']} posts, prom {n['interacciones_prom']} interacciones, {n['pct_positivo']}% positivo")
