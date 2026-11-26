"""
La COLA DE TRABAJO: la pestaña "Solicitudes" de Google Sheets.

Make escribe una fila por cada formulario (estado = pendiente).
El procesador lee las pendientes y, al terminar, actualiza estado / informe / enviado_en / error.

Dos versiones con los mismos métodos:
- HojaGoogle: la hoja real. Necesita una cuenta de servicio de Google (GOOGLE_SA_JSON) y SHEET_ID.
- HojaCSV:    un archivo .csv local con las mismas columnas, para probar sin credenciales.
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

COLUMNAS = ["fecha", "id", "email", "industria", "pais", "marcas", "consentimiento",
            "utm_source", "utm_medium", "utm_campaign", "utm_content", "pagina",
            "estado", "informe", "enviado_en", "error"]


class HojaGoogle:
    def __init__(self, sheet_id: str | None = None, pestana: str = "Solicitudes"):
        import gspread

        info = os.environ.get("GOOGLE_SA_JSON")
        if not info:
            raise RuntimeError("Falta GOOGLE_SA_JSON (el JSON de la cuenta de servicio de Google).")
        # Acepta el contenido del JSON o la ruta a un archivo
        datos = json.loads(Path(info).read_text(encoding="utf-8") if Path(info).is_file() else info)
        cliente = gspread.service_account_from_dict(datos)
        self.ws = cliente.open_by_key(sheet_id or os.environ["SHEET_ID"]).worksheet(pestana)
        self.cabecera = self.ws.row_values(1)
        faltan = [c for c in COLUMNAS if c not in self.cabecera]
        if faltan:
            raise RuntimeError(f"A la hoja le faltan columnas: {', '.join(faltan)}")

    def pendientes(self) -> list[dict]:
        filas = self.ws.get_all_records(expected_headers=COLUMNAS)
        # _fila = número de fila real en la hoja (la 1 es la cabecera)
        return [{**f, "_fila": i + 2} for i, f in enumerate(filas) if str(f.get("estado", "")).strip().lower() == "pendiente"]

    def actualizar(self, fila: dict, **valores):
        for campo, valor in valores.items():
            self.ws.update_cell(fila["_fila"], self.cabecera.index(campo) + 1, valor)


class HojaCSV:
    def __init__(self, ruta: str | Path):
        self.ruta = Path(ruta)

    def _leer(self) -> list[dict]:
        with self.ruta.open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def pendientes(self) -> list[dict]:
        return [{**f, "_fila": i + 2} for i, f in enumerate(self._leer()) if f.get("estado", "").strip().lower() == "pendiente"]

    def actualizar(self, fila: dict, **valores):
        filas = self._leer()
        filas[fila["_fila"] - 2].update({k: str(v) for k, v in valores.items()})
        with self.ruta.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNAS)
            w.writeheader()
            w.writerows(filas)
