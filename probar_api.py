"""
Prueba de la API de la Biblioteca de anuncios de Meta.

Uso (PowerShell):
    $env:META_TOKEN = "tu_token"
    python probar_api.py <page_id> [<page_id> ...]

Opcional:
    $env:META_API_VERSION = "v23.0"   # versión de la API Graph (mira el Explorador)
    $env:META_PAIS = "ES"

Genera anuncios.csv y muestra un resumen por marca. Solo usa la librería estándar.
"""

import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime

VERSION = os.environ.get("META_API_VERSION", "v23.0")
PAIS = os.environ.get("META_PAIS", "ES")
MAX_PAGINAS = 5  # 5 x 50 = hasta 250 anuncios por marca

CAMPOS = [
    "id", "page_id", "page_name", "ad_creation_time",
    "ad_delivery_start_time", "ad_delivery_stop_time",
    "ad_creative_bodies", "ad_creative_link_titles",
    "ad_creative_link_descriptions", "ad_creative_link_captions",
    "publisher_platforms", "languages",
    "eu_total_reach", "target_ages", "target_gender", "target_locations",
    "ad_snapshot_url",
]


def pedir(url):
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8", "replace")
        try:
            msg = json.loads(cuerpo)["error"]["message"]
        except Exception:
            msg = cuerpo[:500]
        sys.exit(f"Error {e.code} de la API: {msg}")


def anuncios_de_pagina(token, page_id):
    params = {
        "access_token": token,
        "search_page_ids": json.dumps([page_id]),
        "ad_reached_countries": json.dumps([PAIS]),
        "ad_type": "ALL",
        "ad_active_status": "ACTIVE",
        "limit": 50,
        "fields": ",".join(CAMPOS),
    }
    url = f"https://graph.facebook.com/{VERSION}/ads_archive?" + urllib.parse.urlencode(params)
    for _ in range(MAX_PAGINAS):
        datos = pedir(url)
        yield from datos.get("data", [])
        url = datos.get("paging", {}).get("next")
        if not url:
            break


def unir(valor):
    if isinstance(valor, list):
        return " | ".join(str(v) for v in valor)
    if isinstance(valor, (dict,)):
        return json.dumps(valor, ensure_ascii=False)
    return "" if valor is None else str(valor)


def dias_activo(inicio):
    try:
        return (date.today() - datetime.fromisoformat(inicio[:10]).date()).days
    except Exception:
        return ""


def main():
    token = os.environ.get("META_TOKEN")
    if not token:
        sys.exit('Falta el token. Ejecuta antes:  $env:META_TOKEN = "tu_token"')
    page_ids = sys.argv[1:]
    if not page_ids:
        sys.exit("Indica al menos un page_id:  python probar_api.py 123456789")

    filas = []
    for pid in page_ids:
        anuncios = list(anuncios_de_pagina(token, pid))
        nombre = anuncios[0].get("page_name", pid) if anuncios else pid
        print(f"\n== {nombre} ({pid}): {len(anuncios)} anuncios activos en {PAIS}")
        for a in anuncios:
            fila = {c: unir(a.get(c)) for c in CAMPOS}
            fila["dias_activo"] = dias_activo(a.get("ad_delivery_start_time", ""))
            fila["fecha_extraccion"] = date.today().isoformat()
            filas.append(fila)
        for a in anuncios[:3]:
            texto = unir(a.get("ad_creative_bodies"))[:120].replace("\n", " ")
            print(f"   - [{a.get('ad_delivery_start_time', '')[:10]}] {texto}")

    if not filas:
        print("\nNo ha llegado ningún anuncio. Revisa los page_id y que las marcas anuncien en ese país.")
        return

    columnas = ["fecha_extraccion", "dias_activo"] + CAMPOS
    with open("anuncios.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)

    vacios = [c for c in CAMPOS if not any(f[c] for f in filas)]
    print(f"\nGuardado anuncios.csv ({len(filas)} filas).")
    if vacios:
        print("Campos que han llegado vacíos:", ", ".join(vacios))


if __name__ == "__main__":
    main()
