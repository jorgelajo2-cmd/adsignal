"""
Nada sensible en sitios públicos.

El repositorio, los informes publicados y los registros de GitHub Actions se pueden ver
desde fuera. Aquí está lo que impide que el token de Meta o el email de alguien acaben ahí.
"""
from __future__ import annotations

import os
import re

_RE_EMAIL = re.compile(r"[^\s@<>«»\"'(),;:]+@[^\s@<>«»\"'(),;:]+\.[A-Za-z]{2,}")
_RE_TOKEN_URL = re.compile(r"(access_token=)[^&\s\"'<>]+", re.I)
_SECRETOS = ("META_TOKEN", "BREVO_API_KEY", "ANTHROPIC_API_KEY")


class FugaDeSecreto(RuntimeError):
    pass


def ocultar(texto) -> str:
    """Devuelve el texto sin emails ni claves. Úsalo antes de imprimir o guardar un error."""
    t = str(texto)
    for nombre in _SECRETOS:
        valor = (os.environ.get(nombre) or "").strip()
        if len(valor) >= 8:
            t = t.replace(valor, "[oculto]")
    t = _RE_TOKEN_URL.sub(r"\1[oculto]", t)
    return _RE_EMAIL.sub("[email]", t)


def comprobar_publicable(contenido: str):
    """Última barrera antes de escribir un archivo que se va a publicar."""
    if "access_token=" in contenido.lower():
        raise FugaDeSecreto("El informe contiene una dirección con access_token. No se guarda.")
    for nombre in _SECRETOS:
        valor = (os.environ.get(nombre) or "").strip()
        if len(valor) >= 8 and valor in contenido:
            raise FugaDeSecreto(f"El informe contiene el valor de {nombre}. No se guarda.")
