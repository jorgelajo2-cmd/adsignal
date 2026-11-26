"""Rellena la plantilla HTML con las métricas y el análisis."""
from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .solicitud import Solicitud

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
_env = Environment(loader=FileSystemLoader(Path(__file__).parent / "plantillas"),
                   autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)


def generar(sol: Solicitud, met: dict, an: dict, ejemplo: bool, carpeta: Path) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    f = sol.fecha
    html = _env.get_template("informe.html").render(
        sol=sol, met=met, an=an, ejemplo=ejemplo,
        fecha_larga=f"{f.day} de {MESES[f.month - 1]} de {f.year}",
    )
    destino = carpeta / f"{sol.nombre_archivo}.html"
    destino.write_text(html, encoding="utf-8")
    # Guardamos también los datos: sirven para depurar y para el dashboard
    # Sin el email: este archivo se publica junto al informe
    solicitud = {k: v for k, v in sol.__dict__.items() if k != "email"} | {"fecha": f.isoformat()}
    datos = {"solicitud": solicitud, "ejemplo": ejemplo, "metricas": met, "analisis": an}
    (carpeta / f"{sol.nombre_archivo}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino
