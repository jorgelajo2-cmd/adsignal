"""
Prueba de la API de la Biblioteca de anuncios de Meta con tu token. Solo España.

Uso (PowerShell):
    python probar_api.py "Basic-Fit" "AltaFit"             anuncios de unas marcas → anuncios.csv
    python probar_api.py 123456789                         (número de página)
    python probar_api.py --sectores Gimnasios Bancos Vino  qué anunciantes encuentra cada sector
                                                           → sectores_prueba.json

Si no hay META_TOKEN en el entorno, lo pide sin mostrarlo y no lo guarda.
Ningún archivo que genera contiene el token.
"""

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import date

from motor.meta_api import CAMPOS, ErrorMeta, anunciantes_de_sector, marcas_conocidas, pedir_token_si_falta, recolectar
from motor.seguridad import comprobar_publicable
from motor.solicitud import PAIS, Solicitud


def unir(valor):
    if isinstance(valor, list):
        return " | ".join(json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else str(v) for v in valor)
    if isinstance(valor, dict):
        return json.dumps(valor, ensure_ascii=False)
    return "" if valor is None else str(valor)


def dias_activo(inicio):
    try:
        return (date.today() - date.fromisoformat(inicio[:10])).days
    except (TypeError, ValueError):
        return ""


def probar_sectores(sectores: list[str]) -> int:
    """Para revisar a quién elige cada sector, sin descargar todos los anuncios de cada marca."""
    resultado = {}
    for sector in sectores:
        print(f"\n== {sector}")
        conocidas = marcas_conocidas(sector, PAIS)
        # La búsqueda se hace siempre aquí, para poder revisar el filtro aunque haya marcas conocidas
        paginas, anuncios, terminos, en_catalogo = anunciantes_de_sector(sector, PAIS)
        resultado[sector] = {
            "terminos": terminos, "en_catalogo": en_catalogo, "conocidas": conocidas,
            "filtradas": [{"id": p, "nombre": n, "anuncios": c} for p, n, c in paginas[:25]],
            "anuncios": anuncios,
        }
        print(f"  búsqueda {terminos}, tras filtrar quedan {len(paginas)} anunciantes. Primeros:")
        for _, n, c in paginas[:8]:
            print(f"   {c:>4}  {n}")
        texto = json.dumps(resultado, ensure_ascii=False)
        comprobar_publicable(texto)
        # Se guarda tras cada sector: si Meta corta por límite, lo hecho no se pierde
        with open("sectores_prueba.json", "w", encoding="utf-8") as f:
            f.write(texto)
    print("\nGuardado sectores_prueba.json")
    return 0


def main(argv=None) -> int:
    for salida in (sys.stdout, sys.stderr):
        salida.reconfigure(errors="replace")  # emojis en consolas antiguas de Windows
    ap = argparse.ArgumentParser(description="Prueba la API de anuncios de Meta (España).")
    ap.add_argument("marcas", nargs="*", help="Nombres de marca, números de página o URL de la Biblioteca")
    ap.add_argument("--sectores", nargs="+", default=[], help="Sectores a revisar")
    a = ap.parse_args(argv)
    if not a.marcas and not a.sectores:
        ap.error('indica alguna marca (python probar_api.py "Basic-Fit") o --sectores')

    pedir_token_si_falta()
    try:
        if a.sectores:
            return probar_sectores(a.sectores)
        r = recolectar(Solicitud(industria="prueba", marcas=a.marcas), log=print)
    except ErrorMeta as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1

    for aviso in r.avisos:
        print(f"AVISO: {aviso}")
    if not r.anuncios:
        print("\nNo ha llegado ningún anuncio. Compara con https://www.facebook.com/ads/library")
        return 0

    campos = CAMPOS.split(",")
    columnas = ["fecha_extraccion", "dias_activo"] + campos
    filas = []
    for ad in r.anuncios:
        fila = {c: unir(ad.get(c)) for c in campos}
        fila["dias_activo"] = dias_activo(ad.get("ad_delivery_start_time"))
        fila["fecha_extraccion"] = date.today().isoformat()
        filas.append(fila)
    comprobar_publicable(json.dumps(filas, ensure_ascii=False))
    with open("anuncios.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=columnas)
        w.writeheader()
        w.writerows(filas)

    print()
    for nombre, n in Counter(f["page_name"] for f in filas).most_common():
        print(f"== {nombre}: {n} anuncios")
        for f in [x for x in filas if x["page_name"] == nombre][:3]:
            texto = f["ad_creative_bodies"][:110].replace("\n", " ")
            print(f"   - [{f['ad_delivery_start_time'][:10]}] {texto}")
    print(f"\nGuardado anuncios.csv ({len(filas)} filas).")
    vacios = [c for c in campos if not any(f[c] for f in filas)]
    if vacios:
        print("Campos que han llegado vacíos:", ", ".join(vacios))
    return 0


if __name__ == "__main__":
    sys.exit(main())
