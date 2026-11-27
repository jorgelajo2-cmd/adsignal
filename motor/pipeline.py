"""Una solicitud → un informe. Lo usan tanto la línea de comandos como el procesador automático."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import analisis, informe, metricas
from .seguridad import ocultar
from .solicitud import Solicitud


class SinAnuncios(RuntimeError):
    def __init__(self, mensaje: str, avisos: list[str] | None = None):
        super().__init__(mensaje)
        self.avisos = avisos or []


@dataclass
class Resultado:
    archivo: Path
    metricas: dict
    analisis: dict
    ejemplo: bool
    pdf: Path | None = None


def generar_informe(sol: Solicitud, fuente: str, usar_ia: bool | None, carpeta: Path, log=print) -> Resultado:
    log(f"  recolectando anuncios ({fuente})…")
    avisos: list[str] = []
    if fuente == "meta":
        from .meta_api import recolectar
        recogida = recolectar(sol, log=lambda m: log("  " + m))
        anuncios, avisos = recogida.anuncios, recogida.avisos
    else:
        from .ejemplo import anuncios_de_ejemplo
        anuncios = anuncios_de_ejemplo(sol)
    if not anuncios:
        raise SinAnuncios(f"No hay anuncios activos de «{sol.industria}» en {sol.nombre_pais}.", avisos)

    log(f"  calculando métricas de {len(anuncios)} anuncios…")
    met = metricas.calcular(anuncios, sol.fecha)
    met["avisos"] = avisos
    an = analisis.analizar(sol, met, usar_ia)
    log(f"  análisis hecho con: {an['fuente']}")
    ejemplo = fuente != "meta"
    archivo = informe.generar(sol, met, an, ejemplo=ejemplo, carpeta=carpeta)
    pdf = None
    try:  # Si el PDF falla, el informe web y el email siguen adelante
        from .pdf import generar_pdf
        pdf = generar_pdf(archivo)
        log(f"  PDF generado: {pdf.name}")
    except Exception as e:
        log(f"  aviso: no se pudo generar el PDF ({type(e).__name__}: {ocultar(e)[:150]})")
    return Resultado(archivo, met, an, ejemplo, pdf)
