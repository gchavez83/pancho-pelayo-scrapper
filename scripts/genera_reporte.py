# -*- coding: utf-8 -*-
"""Inyecta data/consolidado.json en reporte/plantilla.html -> reporte/reporte_pancho_pelayo.html"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
datos = json.load(open(os.path.join(BASE, "data", "consolidado.json"), encoding="utf-8"))
plantilla = open(os.path.join(BASE, "reporte", "plantilla.html"), encoding="utf-8").read()

blob = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
logo = open(os.path.join(BASE, "data", "logo_b64.txt")).read().strip()
salida = plantilla.replace("/*__DATA__*/", blob, 1)
salida = salida.replace("/*__LOGO__*/", "data:image/png;base64," + logo, 1)
ruta = os.path.join(BASE, "reporte", "reporte_pancho_pelayo.html")
with open(ruta, "w", encoding="utf-8") as f:
    f.write(salida)
print("OK", ruta, f"({len(salida)//1024} KB)")
