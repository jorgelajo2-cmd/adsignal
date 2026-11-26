"""Una solicitud → un informe. Lo usan tanto la línea de comandos como el procesador automático."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import analisis, informe, metricas
from .solicitud import Solicitud


class SinAnuncios(RuntimeError):
    pass


@dataclass
class Resultado:
    archivo: Path
    metricas: dict
    analisis: dict
    ejemplo: bool


def generar_informe(sol: Solicitud, fuente: str, usar_ia: bool | None, carpeta: Path, log=print) -> Resultado:
    log(f"  recolectando anuncios ({fuente})…")
    if fuente == "meta":
        from .meta_api import recolectar
        anuncios = recolectar(sol, log=lambda m: log("  " + m))
    else:
        from .ejemplo import anuncios_de_ejemplo
        anuncios = anuncios_de_ejemplo(sol)
    if not anuncios:
        raise SinAnuncios(f"No hay anuncios activos de «{sol.industria}» en {sol.nombre_pais}.")

    log(f"  calculando métricas de {len(anuncios)} anuncios…")
    met = metricas.calcular(anuncios, sol.fecha)
    an = analisis.analizar(sol, met, usar_ia)
    log(f"  análisis hecho con: {an['fuente']}")
    ejemplo = fuente != "meta"
    archivo = informe.generar(sol, met, an, ejemplo=ejemplo, carpeta=carpeta)
    return Resultado(archivo, met, an, ejemplo)
