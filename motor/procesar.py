"""
PROCESADOR: atiende la cola de solicitudes en dos fases.

  generar   pendiente → procesando → generado
            Crea el informe en web/informes/ y guarda el contacto en Brevo.
            Si no hay anuncios, avisa por email (sin_resultados).

  enviar    generado → enviando → enviado
            Solo cuando el informe YA está publicado, para que el enlace del email funcione.

Entre una fase y otra, GitHub Actions publica la web.

Estados de una fila: pendiente, procesando, generado, enviando, enviado, sin_resultados, error.
Si falla algo que afecta a todas (token caducado, límite de Meta), la fila vuelve a
«pendiente» y se reintenta en la siguiente ejecución.

Uso:
  python -m motor.procesar generar          hoja real (necesita las variables de entorno)
  python -m motor.procesar enviar
  python -m motor.procesar --prueba         las dos fases con un CSV local, sin credenciales

Variables (modo real): GOOGLE_SA_JSON, SHEET_ID, BREVO_API_KEY, REMITENTE_EMAIL, BASE_URL
Opcionales: META_TOKEN (si no está, usa datos de ejemplo), ANTHROPIC_API_KEY, BREVO_LISTA_ID

Todo lo que se imprime aquí es público (registros de Actions): ni emails ni claves.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date, datetime
from pathlib import Path

from .correo import componer, componer_sin_resultados
from .meta_api import ErrorMetaGlobal
from .pipeline import SinAnuncios, generar_informe
from .seguridad import ocultar
from .solicitud import Solicitud

RE_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _decir(texto: str):
    print(ocultar(texto))


def _leer_solicitud(fila: dict) -> Solicitud:
    email = str(fila.get("email", "")).strip()
    if not RE_EMAIL.match(email):
        raise ValueError("Email no válido")
    if str(fila.get("consentimiento", "")).strip().lower() not in ("si", "sí", "on", "true", "1"):
        raise ValueError("Sin consentimiento para enviar emails")
    return Solicitud.desde_texto(
        industria=str(fila.get("industria", "")), pais=str(fila.get("pais", "") or "ES"),
        marcas=str(fila.get("marcas", "")), email=email, id=str(fila.get("id", "")),
    )


def _guardar_contacto(correo, sol: Solicitud, fila: dict):
    try:  # El CRM no debe impedir que llegue el informe
        correo.contacto(sol.email, {
            "SECTOR": sol.industria, "PAIS": sol.pais,
            "UTM_SOURCE": fila.get("utm_source", ""), "UTM_CAMPAIGN": fila.get("utm_campaign", ""),
        })
    except Exception as e:
        _decir(f"   aviso: no se pudo guardar el contacto en Brevo ({e})")


def generar(hoja, correo, fuente: str, carpeta: Path, base_url: str, maximo: int = 10) -> int:
    """Fase 1. Devuelve el número de problemas que hay que revisar."""
    # «procesando» al empezar = una ejecución anterior se cortó a medias (solo corre una a la vez)
    filas = hoja.filas("pendiente", "procesando")[:maximo]
    print(f"{len(filas)} solicitudes por generar (datos: {fuente})")
    problemas = 0
    for fila in filas:
        _decir(f"→ fila {fila['_fila']}: {fila.get('industria')} / {fila.get('pais')}")
        hoja.actualizar(fila, estado="procesando")
        try:
            sol = _leer_solicitud(fila)
            try:
                r = generar_informe(sol, fuente, None, carpeta, log=lambda m: _decir("   " + m))
            except SinAnuncios as e:
                asunto, html = componer_sin_resultados(sol, e.avisos, base_url)
                correo.enviar(sol.email, asunto, html)
                _guardar_contacto(correo, sol, fila)
                hoja.actualizar(fila, estado="sin_resultados", enviado_en=_ahora(), error=str(e)[:300])
                _decir("   sin anuncios: avisado por email")
                continue
            _guardar_contacto(correo, sol, fila)
            url = f"{base_url.rstrip('/')}/informes/{r.archivo.name}"
            hoja.actualizar(fila, estado="generado", informe=url, error="")
            _decir(f"   generado: {r.archivo.name}")
        except ErrorMetaGlobal as e:
            hoja.actualizar(fila, estado="pendiente", error=ocultar(e)[:300])
            _decir(f"   PARADO: {e}")
            return problemas + 1
        except Exception as e:
            problemas += 1
            _decir(f"   ERROR: {e}")
            hoja.actualizar(fila, estado="error", error=ocultar(e)[:300])
    return problemas


def publicado(url: str, intentos: int = 12, espera: int = 10) -> bool:
    for i in range(intentos):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        if i < intentos - 1:
            time.sleep(espera)
    return False


def enviar(hoja, correo, carpeta: Path, base_url: str, esta_publicado=publicado) -> int:
    """Fase 2. Devuelve el número de problemas que hay que revisar."""
    filas = hoja.filas("generado")
    print(f"{len(filas)} informes por enviar")
    problemas = 0
    for fila in filas:
        url = str(fila.get("informe", ""))
        nombre = url.rsplit("/", 1)[-1].removesuffix(".html")
        datos_json = carpeta / f"{nombre}.json"
        try:
            sol = _leer_solicitud(fila)
            if not nombre or not datos_json.is_file():
                # El informe no llegó a guardarse en el repositorio: se vuelve a generar
                hoja.actualizar(fila, estado="pendiente", informe="")
                _decir(f"→ fila {fila['_fila']}: falta el informe, se generará otra vez")
                problemas += 1
                continue
            if not esta_publicado(url):
                _decir(f"→ fila {fila['_fila']}: todavía no está publicado, se enviará en la próxima ejecución")
                problemas += 1
                continue
            datos = json.loads(datos_json.read_text(encoding="utf-8"))
            sol.fecha = date.fromisoformat(datos["solicitud"]["fecha"])
            pdf_url = url.removesuffix(".html") + ".pdf" if (carpeta / f"{nombre}.pdf").is_file() else None
            asunto, html = componer(sol, datos["metricas"], datos["analisis"], url, datos["ejemplo"],
                                    pdf_url=pdf_url, base_url=base_url)
            # Si se corta justo aquí, preferimos revisar a mano antes que enviar dos veces
            hoja.actualizar(fila, estado="enviando")
            correo.enviar(sol.email, asunto, html)
            hoja.actualizar(fila, estado="enviado", enviado_en=_ahora(), error="")
            _decir(f"→ fila {fila['_fila']}: enviado")
        except Exception as e:
            problemas += 1
            _decir(f"→ fila {fila['_fila']}: ERROR: {e}")
            hoja.actualizar(fila, estado="error", error=ocultar(e)[:300])
    return problemas


def _avisar_a_actions(**valores):
    """Deja datos para los pasos siguientes del flujo de GitHub Actions."""
    ruta = os.environ.get("GITHUB_OUTPUT")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as f:
            f.writelines(f"{k}={v}\n" for k, v in valores.items())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m motor.procesar")
    ap.add_argument("fase", nargs="?", choices=["generar", "enviar", "todo"], default="todo")
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
            print(f"Error de configuración: {ocultar(e)}", file=sys.stderr)
            return 1
        except Exception as e:  # errores de librerías: solo el tipo, por si el mensaje incluyera credenciales
            print(f"Error de configuración ({type(e).__name__}). Revisa los secretos GOOGLE_SA_JSON, SHEET_ID y BREVO_*.", file=sys.stderr)
            return 1
        base_url = (os.environ.get("BASE_URL") or "").strip()
        if not base_url:
            print("Error de configuración: falta BASE_URL (la dirección pública de la web).", file=sys.stderr)
            return 1

    carpeta = Path(a.salida)
    problemas = 0
    if a.fase in ("generar", "todo"):
        fuente = "meta" if (os.environ.get("META_TOKEN") or "").strip() else "ejemplo"
        problemas += generar(hoja, correo, fuente, carpeta, base_url, a.max)
        _avisar_a_actions(por_enviar=len(hoja.filas("generado")))
    if a.fase in ("enviar", "todo"):
        # En modo prueba no hay web publicada que comprobar
        problemas += enviar(hoja, correo, carpeta, base_url, **({"esta_publicado": lambda url: True} if a.prueba else {}))
    _avisar_a_actions(problemas=problemas)
    print(f"Hecho. Problemas: {problemas}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
