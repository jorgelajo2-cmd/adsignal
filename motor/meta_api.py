"""
Recolector: descarga anuncios de la Biblioteca de anuncios de Meta (endpoint ads_archive).

Necesita:
  META_TOKEN         token de acceso (ver INFRAESTRUCTURA.md, paso 1)
  META_API_VERSION   opcional, p. ej. "v23.0" (usa la que indique el Explorador de la API Graph)

Dos maneras de elegir las marcas:
  1. La persona da marcas  → buscamos la página de cada una por su nombre.
  2. No da marcas          → buscamos anuncios con el nombre del sector y nos quedamos
                             con las páginas que más anuncios tienen.
"""
from __future__ import annotations

import json
import os
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

from .solicitud import Solicitud

CAMPOS = ",".join([
    "id", "page_id", "page_name", "ad_creation_time", "ad_delivery_start_time", "ad_delivery_stop_time",
    "ad_creative_bodies", "ad_creative_link_titles", "ad_creative_link_descriptions", "ad_creative_link_captions",
    "publisher_platforms", "languages", "eu_total_reach", "target_ages", "target_gender", "target_locations",
    "ad_snapshot_url",
])


class ErrorMeta(RuntimeError):
    pass


def _url_base() -> str:
    return f"https://graph.facebook.com/{os.environ.get('META_API_VERSION', 'v23.0')}/ads_archive"


def _pedir(url: str, reintentos: int = 3) -> dict:
    for intento in range(reintentos):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read().decode("utf-8", "replace")).get("error", {})
            except Exception:
                err = {}
            # 4 / 17 / 613 = límite de peticiones: esperamos y reintentamos
            if err.get("code") in (4, 17, 613) and intento < reintentos - 1:
                time.sleep(30 * (intento + 1))
                continue
            raise ErrorMeta(f"API de Meta {e.code}: {err.get('message', 'error desconocido')}") from None
        except urllib.error.URLError as e:
            if intento < reintentos - 1:
                time.sleep(5)
                continue
            raise ErrorMeta(f"Sin conexión con la API de Meta: {e.reason}") from None
    raise ErrorMeta("La API de Meta no responde")


def _consultar(params: dict, max_anuncios: int):
    """Generador que recorre todas las páginas de resultados (paginación) hasta max_anuncios."""
    token = os.environ.get("META_TOKEN")
    if not token:
        raise ErrorMeta("Falta META_TOKEN. Consigue el token en developers.facebook.com (ver INFRAESTRUCTURA.md).")
    base = {"access_token": token, "ad_type": "ALL", "ad_active_status": "ACTIVE", "limit": 100}
    url = _url_base() + "?" + urllib.parse.urlencode({**base, **params})
    n = 0
    while url and n < max_anuncios:
        datos = _pedir(url)
        for ad in datos.get("data", []):
            yield ad
            n += 1
            if n >= max_anuncios:
                return
        url = datos.get("paging", {}).get("next")


def _norm(t: str) -> str:
    return unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode().replace(" ", "")


def buscar_anunciantes(termino: str, pais: str, max_anuncios: int = 600) -> list[tuple[str, str, int]]:
    """Páginas con más anuncios activos que contienen el término. Devuelve (page_id, nombre, n_anuncios)."""
    cuenta, nombres = Counter(), {}
    params = {"search_terms": termino, "ad_reached_countries": json.dumps([pais]), "fields": "page_id,page_name"}
    for ad in _consultar(params, max_anuncios):
        cuenta[ad["page_id"]] += 1
        nombres[ad["page_id"]] = ad.get("page_name", ad["page_id"])
    return [(pid, nombres[pid], n) for pid, n in cuenta.most_common()]


def resolver_marca(nombre: str, pais: str) -> tuple[str, str] | None:
    """Encuentra la página oficial de una marca: la que más anuncios tiene entre las que se llaman parecido."""
    candidatas = buscar_anunciantes(nombre, pais, max_anuncios=300)
    objetivo = _norm(nombre)
    parecidas = [c for c in candidatas if objetivo in _norm(c[1]) or _norm(c[1]) in objetivo]
    elegida = (parecidas or candidatas or [None])[0]
    return (elegida[0], elegida[1]) if elegida else None


def anuncios_de_pagina(page_id: str, pais: str, max_anuncios: int = 200) -> list[dict]:
    params = {"search_page_ids": json.dumps([page_id]), "ad_reached_countries": json.dumps([pais]), "fields": CAMPOS}
    return list(_consultar(params, max_anuncios))


def recolectar(sol: Solicitud, max_marcas: int = 6, max_por_marca: int = 200, log=print) -> list[dict]:
    if sol.marcas:
        paginas = []
        for m in sol.marcas[:max_marcas]:
            r = resolver_marca(m, sol.pais)
            log(f"  marca «{m}» → {r[1] + ' (' + r[0] + ')' if r else 'no encontrada'}")
            if r:
                paginas.append(r)
    else:
        top = buscar_anunciantes(sol.industria, sol.pais)
        paginas = [(pid, nombre) for pid, nombre, _ in top[:max_marcas]]
        log(f"  anunciantes para «{sol.industria}»: {', '.join(n for _, n in paginas) or 'ninguno'}")

    anuncios = []
    for pid, nombre in paginas:
        ads = anuncios_de_pagina(pid, sol.pais, max_por_marca)
        log(f"  {nombre}: {len(ads)} anuncios activos")
        anuncios += ads
    return anuncios
