"""Qué ha pedido la persona. Es lo que llega del formulario (vía Make / Google Sheets)."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date

# AdSignal analiza solo España. El campo «pais» se conserva porque la hoja y Make lo usan.
PAIS = "ES"
NOMBRE_PAIS = "España"


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "informe"


@dataclass
class Solicitud:
    industria: str
    pais: str = PAIS
    marcas: list[str] = field(default_factory=list)
    email: str = ""
    id: str = ""
    fecha: date = field(default_factory=date.today)

    def __post_init__(self):
        self.industria = self.industria.strip()
        self.pais = self.pais.strip().upper() or PAIS
        if not self.industria:
            raise ValueError("Falta el sector (industria).")
        # Viene de un formulario público y acaba en un título publicado
        if len(self.industria) > 60:
            raise ValueError("El nombre del sector es demasiado largo (máximo 60 caracteres).")
        if self.pais != PAIS:
            raise ValueError(f"País no válido: {self.pais}. AdSignal solo analiza España.")
        self.marcas = [m.strip() for m in self.marcas if m and m.strip()]

    @classmethod
    def desde_texto(cls, industria: str, pais: str = PAIS, marcas: str = "", email: str = "", id: str = ""):
        """Crea la solicitud a partir de los campos tal como llegan del formulario."""
        return cls(industria=industria, pais=pais, marcas=re.split(r"[,;\n]", marcas or ""), email=email, id=id)

    @property
    def nombre_pais(self) -> str:
        return NOMBRE_PAIS

    @property
    def nombre_archivo(self) -> str:
        base = f"{slug(self.industria)}-{self.pais.lower()}-{self.fecha.isoformat()}"
        # Con id, el nombre es único y difícil de adivinar (los informes se publican en la web)
        return f"{base}-{slug(self.id)[:10]}" if self.id else base
