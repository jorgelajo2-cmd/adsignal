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

        info = (os.environ.get("GOOGLE_SA_JSON") or "").strip()
        if not info:
            raise RuntimeError("Falta GOOGLE_SA_JSON (el JSON de la cuenta de servicio de Google).")
        # Acepta el contenido del JSON o la ruta a un archivo.
        # OJO: nunca tratar el contenido como ruta: el error de Python incluiría la clave en el mensaje.
        try:
            texto = info if info.startswith("{") else Path(info).read_text(encoding="utf-8")
            datos = json.loads(texto)
        except Exception as e:
            raise RuntimeError(f"GOOGLE_SA_JSON no es un JSON válido ni la ruta a uno ({type(e).__name__}).") from None
        cliente = gspread.service_account_from_dict(datos)
        self.ws = cliente.open_by_key((sheet_id or os.environ["SHEET_ID"]).strip()).worksheet(pestana)
        self.cabecera = self.ws.row_values(1)
        faltan = [c for c in COLUMNAS if c not in self.cabecera]
        if faltan:
            raise RuntimeError(f"A la hoja le faltan columnas: {', '.join(faltan)}")

    def filas(self, *estados: str) -> list[dict]:
        # numericise_ignore: un id o un número de página no deben convertirse en número
        filas = self.ws.get_all_records(expected_headers=COLUMNAS, numericise_ignore=["all"])
        # _fila = número de fila real en la hoja (la 1 es la cabecera)
        return [{**f, "_fila": i + 2} for i, f in enumerate(filas) if str(f.get("estado", "")).strip().lower() in estados]

    def actualizar(self, fila: dict, **valores):
        for campo, valor in valores.items():
            self.ws.update_cell(fila["_fila"], self.cabecera.index(campo) + 1, valor)


class HojaCSV:
    def __init__(self, ruta: str | Path):
        self.ruta = Path(ruta)

    def _leer(self) -> list[dict]:
        with self.ruta.open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def filas(self, *estados: str) -> list[dict]:
        return [{**f, "_fila": i + 2} for i, f in enumerate(self._leer()) if f.get("estado", "").strip().lower() in estados]

    def actualizar(self, fila: dict, **valores):
        filas = self._leer()
        filas[fila["_fila"] - 2].update({k: str(v) for k, v in valores.items()})
        with self.ruta.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNAS)
            w.writeheader()
            w.writerows(filas)
