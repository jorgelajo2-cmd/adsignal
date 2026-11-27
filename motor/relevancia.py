"""
Separa los anunciantes de un sector del ruido que trae buscar palabras sueltas.

Reglas, a partir de resultados reales en España:
  1. Fuera las apps de series y novelas y las tiendas con nombre generado.
  2. Un anuncio cuenta si el sector aparece donde se anuncia de qué va: nombre de la página,
     titular, enlace o el principio del texto. Una historia que menciona un gimnasio en el
     párrafo cinco no es publicidad de gimnasios.
  3. Una página entra si cuentan al menos la mitad de sus anuncios.
Van primero las páginas cuyo nombre o web nombran el sector.

No es infalible: para precisión total hay que indicar las marcas.
"""
from __future__ import annotations

import re

from .texto import palabras

INICIO_TEXTO = 220  # caracteres del cuerpo que cuentan

_PAGINA_RUIDO = re.compile(
    r"drama|reels\b|playet|shorts|novel|sto?ry|stories|reader|tales\b"
    r"|page\s?\d+\b|-(?:sell|buy|store|shop)\b|\b[a-z]*\d{2,}-\d+\b", re.I)
_TEXTO_RUIDO = re.compile(
    r"\bepisodios?\b|series cortas|dramas? cortos?|siguiente cap[ií]tulo|leer (?:el )?cap[ií]tulo", re.I)
# Palabras que no dicen de qué sector es algo
_VACIAS = {"de", "del", "la", "el", "en", "y", "a", "para", "tu", "con", "online", "apps", "app"}


def es_ruido(ad: dict) -> bool:
    if _PAGINA_RUIDO.search(ad.get("page_name") or ""):
        return True
    return bool(_TEXTO_RUIDO.search(" ".join(ad.get("ad_creative_bodies") or [])))


def _raiz(p: str) -> str:
    return p.removesuffix("s").removesuffix("e") if len(p) > 3 else p


def _contiene(texto: str, expresiones: list[list[str]]) -> bool:
    """¿Aparece alguna expresión, como palabras seguidas? Ignora acentos y plurales."""
    t = [_raiz(p) for p in palabras(texto)]
    for e in expresiones:
        n = len(e)
        if any(t[i:i + n] == e for i in range(len(t) - n + 1)):
            return True
    return False


def _expresiones(sector: str, terminos: list[str]) -> list[list[str]]:
    sueltas = [[p] for p in palabras(sector) if p not in _VACIAS]
    completas = [palabras(t) for t in terminos]
    # Una sola palabra del nombre vale si el sector es de una palabra («Vino», «Gimnasios»)
    base = sueltas if len(sueltas) == 1 else []
    return [[_raiz(p) for p in e] for e in base + completas if e]


def _nombra_el_sector(ad: dict, sector: str) -> bool:
    """Nombre de página o dominio con alguna palabra del sector, aunque vaya pegada («bancosabadell.com»)."""
    junto = "".join(palabras(" ".join([ad.get("page_name") or "", *(ad.get("ad_creative_link_captions") or [])])))
    return any(_raiz(p) in junto for p in palabras(sector) if p not in _VACIAS and len(p) > 3)


def es_del_sector(ad: dict, expresiones: list[list[str]]) -> bool:
    visibles = [ad.get("page_name") or "", *(ad.get("ad_creative_link_titles") or []),
                *(ad.get("ad_creative_link_captions") or []), *(ad.get("ad_creative_link_descriptions") or []),
                *((c or "")[:INICIO_TEXTO] for c in ad.get("ad_creative_bodies") or [])]
    return any(_contiene(v, expresiones) for v in visibles)


def ordenar_anunciantes(anuncios: list[dict], sector: str, terminos: list[str]) -> list[tuple[str, str, int]]:
    """(page_id, nombre, anuncios distintos) de las páginas que parecen del sector."""
    expresiones = _expresiones(sector, terminos)
    paginas: dict[str, dict] = {}
    for i, ad in enumerate(anuncios):
        pid = ad.get("page_id")
        if not pid:
            continue
        p = paginas.setdefault(pid, {"nombre": ad.get("page_name") or pid, "ads": {}, "ruido": False, "nombra": False})
        p["ruido"] = p["ruido"] or es_ruido(ad)
        p["nombra"] = p["nombra"] or _nombra_el_sector(ad, sector)
        p["ads"][ad.get("id", i)] = es_del_sector(ad, expresiones)
    validas = [(pid, p) for pid, p in paginas.items()
               if not p["ruido"] and 2 * sum(p["ads"].values()) >= len(p["ads"])]
    validas.sort(key=lambda x: (not x[1]["nombra"], -len(x[1]["ads"])))
    return [(pid, p["nombre"], len(p["ads"])) for pid, p in validas]
