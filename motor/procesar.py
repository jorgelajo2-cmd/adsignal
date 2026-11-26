"""
PROCESADOR: atiende la cola de solicitudes.

Por cada fila con estado = pendiente:
  1. la marca como "procesando" (para que otra ejecución no la coja a la vez)
  2. genera el informe y lo guarda en web/informes/ (lo que se publica)
  3. crea/actualiza el contacto en Brevo (CRM)
  4. envía el email con el enlace
  5. marca la fila como "enviado" (o "error" con el motivo)

Uso:
  python -m motor.procesar                  hoja real + Brevo (necesita las variables de entorno)
  python -m motor.procesar --prueba         CSV local + emails guardados en carpeta, sin credenciales

Variables (modo real): GOOGLE_SA_JSON, SHEET_ID, BREVO_API_KEY, REMITENTE_EMAIL, BASE_URL
Opcionales: META_TOKEN (si no está, usa datos de ejemplo), ANTHROPIC_API_KEY, BREVO_LISTA_ID
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from .correo import componer
from .pipeline import generar_informe
from .solicitud import Solicitud

RE_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def procesar_fila(fila: dict, hoja, correo, fuente: str, carpeta: Path, base_url: str) -> str:
    email = str(fila.get("email", "")).strip()
    if not RE_EMAIL.match(email):
        raise ValueError(f"Email no válido: «{email}»")
    if str(fila.get("consentimiento", "")).strip().lower() not in ("si", "sí", "on", "true", "1"):
        raise ValueError("Sin consentimiento para enviar emails")

    sol = Solicitud.desde_texto(
        industria=str(fila.get("industria", "")), pais=str(fila.get("pais", "") or "ES"),
        marcas=str(fila.get("marcas", "")), email=email, id=str(fila.get("id", "")),
    )
    r = generar_informe(sol, fuente, None, carpeta, log=lambda m: print("   " + m))
    url = f"{base_url.rstrip('/')}/informes/{r.archivo.name}"

    try:  # El CRM no debe impedir que llegue el informe
        correo.contacto(email, {
            "SECTOR": sol.industria, "PAIS": sol.pais,
            "UTM_SOURCE": fila.get("utm_source", ""), "UTM_CAMPAIGN": fila.get("utm_campaign", ""),
        })
    except Exception as e:
        print(f"   aviso: no se pudo guardar el contacto en Brevo ({e})")

    asunto, html = componer(sol, r.metricas, r.analisis, url, r.ejemplo)
    correo.enviar(email, asunto, html)
    return url


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m motor.procesar")
    ap.add_argument("--prueba", action="store_true", help="Usa solicitudes_prueba.csv y guarda los emails en salida_emails/")
    ap.add_argument("--csv", default="solicitudes_prueba.csv")
    ap.add_argument("--salida", default="web/informes")
    ap.add_argument("--max", type=int, default=10, help="Máximo de solicitudes por ejecución")
    a = ap.parse_args(argv)

    if a.prueba:
        from .correo import CorreoPrueba
        from .hoja import HojaCSV
        hoja, correo = HojaCSV(a.csv), CorreoPrueba()
        base_url = os.environ.get("BASE_URL", "http://localhost:8123")
    else:
        from .correo import CorreoBrevo
        from .hoja import HojaGoogle
        try:
            hoja, correo = HojaGoogle(), CorreoBrevo()
        except RuntimeError as e:  # nuestros propios mensajes: nunca contienen secretos
            print(f"Error de configuración: {e}", file=sys.stderr)
            return 1
        except Exception as e:  # errores de librerías: solo el tipo, por si el mensaje incluyera credenciales
            print(f"Error de configuración ({type(e).__name__}). Revisa los secretos GOOGLE_SA_JSON, SHEET_ID y BREVO_*.", file=sys.stderr)
            return 1
        base_url = os.environ.get("BASE_URL", "")
        if not base_url:
            print("Error de configuración: falta BASE_URL (la dirección pública de la web).", file=sys.stderr)
            return 1

    fuente = "meta" if os.environ.get("META_TOKEN") else "ejemplo"
    pendientes = hoja.pendientes()[: a.max]
    print(f"{len(pendientes)} solicitudes pendientes (datos: {fuente})")

    enviados = errores = 0
    for fila in pendientes:
        print(f"→ fila {fila['_fila']}: {fila.get('industria')} / {fila.get('pais')}")
        hoja.actualizar(fila, estado="procesando")
        try:
            url = procesar_fila(fila, hoja, correo, fuente, Path(a.salida), base_url)
        except Exception as e:
            errores += 1
            print(f"   ERROR: {e}")
            hoja.actualizar(fila, estado="error", error=str(e)[:300])
        else:
            enviados += 1
            print(f"   enviado: {url}")
            hoja.actualizar(fila, estado="enviado", informe=url, enviado_en=datetime.now().strftime("%Y-%m-%d %H:%M"), error="")

    print(f"Hecho: {enviados} enviados, {errores} con error.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
