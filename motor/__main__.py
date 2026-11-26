"""
Genera un informe a mano, desde la terminal.

Ejemplos:
  python -m motor --industria "gimnasios" --pais ES --fuente ejemplo
  python -m motor --industria "seguros de coche" --pais ES --marcas "Mapfre, Línea Directa" --fuente meta

Para procesar automáticamente las solicitudes de la hoja: python -m motor.procesar
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import SinAnuncios, generar_informe
from .solicitud import Solicitud


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m motor", description="Genera un informe de anuncios de adsignal.")
    ap.add_argument("--industria", required=True, help="Sector, p. ej. «gimnasios»")
    ap.add_argument("--pais", default="ES", help="Código de país de la UE (ES, FR, IT…)")
    ap.add_argument("--marcas", default="", help="Marcas separadas por comas (opcional)")
    ap.add_argument("--fuente", choices=["ejemplo", "meta"], default="ejemplo",
                    help="«ejemplo» = datos inventados para probar; «meta» = API real (necesita META_TOKEN)")
    ap.add_argument("--ia", choices=["auto", "si", "no"], default="auto", help="«auto» usa Claude si hay ANTHROPIC_API_KEY")
    ap.add_argument("--salida", default="informes", help="Carpeta donde guardar el informe")
    a = ap.parse_args(argv)

    try:
        sol = Solicitud.desde_texto(a.industria, a.pais, a.marcas)
    except ValueError as e:
        print(f"Error en la solicitud: {e}", file=sys.stderr)
        return 2

    print(f"Informe de «{sol.industria}» en {sol.nombre_pais}")
    try:
        r = generar_informe(sol, a.fuente, {"auto": None, "si": True, "no": False}[a.ia], Path(a.salida))
    except SinAnuncios as e:
        print(f"{e} Prueba otro término o marcas concretas.", file=sys.stderr)
        return 4
    except RuntimeError as e:  # p. ej. errores de la API de Meta
        print(f"Error: {e}", file=sys.stderr)
        return 3
    print(f"Informe listo: {r.archivo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
