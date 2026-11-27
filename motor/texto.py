"""Utilidades de texto compartidas."""
from __future__ import annotations

import re
import unicodedata


def palabras(texto: str) -> list[str]:
    """Palabras en minúsculas y sin acentos (conserva alfabetos no latinos)."""
    sin = "".join(c for c in unicodedata.normalize("NFKD", texto.casefold()) if not unicodedata.combining(c))
    return re.findall(r"[^\W_]+", sin)
