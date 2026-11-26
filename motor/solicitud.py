"""Qué ha pedido la persona. Es lo que llega del formulario (vía Make / Google Sheets)."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date

# Países de la UE: los únicos para los que la API de Meta da TODOS los anuncios (DSA).
PAISES_UE = {
    "ES": "España", "PT": "Portugal", "FR": "Francia", "IT": "Italia", "DE": "Alemania",
    "NL": "Países Bajos", "BE": "Bélgica", "IE": "Irlanda", "AT": "Austria", "PL": "Polonia",
    "SE": "Suecia", "DK": "Dinamarca", "FI": "Finlandia", "GR": "Grecia", "CZ": "Chequia",
    "RO": "Rumanía", "HU": "Hungría", "SK": "Eslovaquia", "BG": "Bulgaria", "HR": "Croacia",
    "SI": "Eslovenia", "LT": "Lituania", "LV": "Letonia", "EE": "Estonia", "LU": "Luxemburgo",
    "CY": "Chipre", "MT": "Malta",
}


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "informe"


@dataclass
class Solicitud:
    industria: str
    pais: str = "ES"
    marcas: list[str] = field(default_factory=list)
    email: str = ""
    id: str = ""
    fecha: date = field(default_factory=date.today)

    def __post_init__(self):
        self.industria = self.industria.strip()
        self.pais = self.pais.strip().upper()
        if not self.industria:
            raise ValueError("Falta el sector (industria).")
        if self.pais not in PAISES_UE:
            raise ValueError(f"País no válido: {self.pais}. Solo países de la UE: {', '.join(PAISES_UE)}")
        self.marcas = [m.strip() for m in self.marcas if m and m.strip()]

    @classmethod
    def desde_texto(cls, industria: str, pais: str = "ES", marcas: str = "", email: str = "", id: str = ""):
        """Crea la solicitud a partir de los campos tal como llegan del formulario."""
        return cls(industria=industria, pais=pais, marcas=re.split(r"[,;\n]", marcas or ""), email=email, id=id)

    @property
    def nombre_pais(self) -> str:
        return PAISES_UE[self.pais]

    @property
    def nombre_archivo(self) -> str:
        base = f"{slug(self.industria)}-{self.pais.lower()}-{self.fecha.isoformat()}"
        # Con id, el nombre es único y difícil de adivinar (los informes se publican en la web)
        return f"{base}-{slug(self.id)[:10]}" if self.id else base
