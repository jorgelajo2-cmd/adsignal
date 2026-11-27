"""
Recolector: descarga anuncios de la Biblioteca de anuncios de Meta (endpoint ads_archive).

Necesita:
  META_TOKEN         token de acceso (ver INFRAESTRUCTURA.md, paso 1)
  META_API_VERSION   opcional, p. ej. "v23.0" (usa la que indique el Explorador de la API Graph)

Dos maneras de elegir las marcas:
  1. La persona da marcas  → buscamos la página de cada una. Si no hay una que se llame
                             como la marca, se dice «no encontrada»: nunca se adivina.
                             También vale el número de página o la URL de la Biblioteca.
  2. No da marcas          → probamos los anunciantes conocidos del sector (marcas.py). Si
                             hay menos de 3 con anuncios, completamos buscando el sector
                             (sectores.py) y filtrando el ruido (relevancia.py).

Seguridad: Meta incluye el token en ad_snapshot_url. Aquí se sustituye por el enlace
público del anuncio antes de que nadie más vea los datos.
"""
from __future__ import annotations

import getpass
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass, field

from .marcas import CONOCIDAS
from .relevancia import ordenar_anunciantes
from .sectores import buscar_sector, terminos_de_busqueda
from .seguridad import ocultar
from .solicitud import Solicitud
from .texto import palabras

CAMPOS = ",".join([
    "id", "page_id", "page_name", "ad_creation_time", "ad_delivery_start_time", "ad_delivery_stop_time",
    "ad_creative_bodies", "ad_creative_link_titles", "ad_creative_link_descriptions", "ad_creative_link_captions",
    "publisher_platforms", "languages", "eu_total_reach", "target_ages", "target_gender", "target_locations",
    "ad_snapshot_url",
])
VERSION_POR_DEFECTO = "v23.0"
MAX_MARCAS = 6
MIN_MARCAS = 3  # con menos marcas conocidas, se completa buscando
MAX_POR_MARCA = 500
TAMANO_PAGINA = 100
MAX_POR_BUSQUEDA = 300
# Al buscar un sector, descarta anunciantes extranjeros que escriben en otros idiomas
IDIOMAS_ESPANA = ["es", "ca", "gl", "eu"]
CAMPOS_BUSQUEDA = ("id,page_id,page_name,ad_creative_bodies,ad_creative_link_titles,"
                   "ad_creative_link_captions,ad_creative_link_descriptions")
# Lo que puede acompañar al nombre de una marca conocida en su página
_COLETILLAS = {"espana", "es", "spain", "oficial", "official", "grupo", "seguros", "aseguradora", "banco", "centros", "tiendas", "clinicas"}

_LIMITE = (4, 17, 32, 613)   # límite de peticiones
_ACCESO = (10, 190, 200)     # token caducado o sin permiso


class ErrorMeta(RuntimeError):
    pass


class ErrorMetaGlobal(ErrorMeta):
    """Falla para todas las solicitudes (token, límite, sin conexión): hay que reintentar más tarde."""


def enlace_publico(ad_id) -> str:
    return f"https://www.facebook.com/ads/library/?id={ad_id}"


def pedir_token_si_falta():
    """En una terminal, pide el token sin mostrarlo. No se guarda en ningún sitio."""
    if not os.environ.get("META_TOKEN") and sys.stdin.isatty():
        token = getpass.getpass("Pega tu token de Meta y pulsa Enter (no se verá nada): ")
        os.environ["META_TOKEN"] = "".join(c for c in token if c.isprintable()).strip()


def _url_base() -> str:
    version = (os.environ.get("META_API_VERSION") or "").strip() or VERSION_POR_DEFECTO
    return f"https://graph.facebook.com/{version}/ads_archive"


def _con_limite(url: str, limite: int) -> str:
    return re.sub(r"([?&]limit=)\d+", rf"\g<1>{limite}", url)


def _pedir(url: str, reintentos: int = 4) -> dict:
    for intento in range(reintentos):
        ultimo = intento == reintentos - 1
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read().decode("utf-8", "replace")).get("error", {})
            except Exception:
                err = {}
            codigo, mensaje = err.get("code"), ocultar(err.get("message", "error desconocido"))
            if codigo in _ACCESO:
                raise ErrorMetaGlobal(f"Meta rechaza el acceso (código {codigo}): {mensaje} "
                                      "Revisa que META_TOKEN no haya caducado.") from None
            # «Estás pidiendo demasiados datos»: se repite con páginas más pequeñas
            if codigo == 1 and "reduce" in mensaje.lower() and not ultimo:
                actual = re.search(r"[?&]limit=(\d+)", url)
                url = _con_limite(url, max(10, int(actual.group(1)) // 2 if actual else 25))
                continue
            if codigo in _LIMITE:
                if not ultimo:
                    time.sleep(30 * (intento + 1))
                    continue
                raise ErrorMetaGlobal(f"Meta ha cortado por límite de peticiones: {mensaje}") from None
            if (err.get("is_transient") or e.code >= 500) and not ultimo:
                time.sleep(5 * (intento + 1))
                continue
            if err.get("is_transient") or e.code >= 500:
                raise ErrorMetaGlobal(f"La API de Meta está fallando ({e.code}): {mensaje}") from None
            raise ErrorMeta(f"API de Meta {e.code}: {mensaje}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if not ultimo:
                time.sleep(5)
                continue
            raise ErrorMetaGlobal(f"Sin conexión con la API de Meta ({type(e).__name__}).") from None
        except Exception as e:  # su mensaje podría incluir la URL con el token: solo el tipo
            raise ErrorMeta(f"Respuesta inesperada de la API de Meta ({type(e).__name__}).") from None
    raise ErrorMetaGlobal("La API de Meta no responde")


def consultar(params: dict, max_anuncios: int) -> tuple[list[dict], bool]:
    """
    Recorre las páginas de resultados hasta max_anuncios.
    Devuelve (anuncios, True si quedaban más sin descargar).
    """
    token = (os.environ.get("META_TOKEN") or "").strip()
    if not token:
        raise ErrorMetaGlobal("Falta META_TOKEN. Consigue el token en developers.facebook.com (ver INFRAESTRUCTURA.md).")
    base = {"access_token": token, "ad_type": "ALL", "ad_active_status": "ACTIVE", "limit": TAMANO_PAGINA}
    url = _url_base() + "?" + urllib.parse.urlencode({**base, **params})
    anuncios: list[dict] = []
    while url:
        datos = _pedir(url)
        for ad in datos.get("data", []):
            if len(anuncios) >= max_anuncios:
                return anuncios, True
            if "ad_snapshot_url" in ad:
                ad["ad_snapshot_url"] = enlace_publico(ad.get("id", ""))
            anuncios.append(ad)
        url = datos.get("paging", {}).get("next")
        if url and len(anuncios) >= max_anuncios:
            return anuncios, True
    return anuncios, False


def parecido(marca: str, pagina: str) -> int:
    """2 = mismo nombre, 1 = la página contiene la marca como palabras completas, 0 = otra cosa."""
    m, p = palabras(marca), palabras(pagina)
    if not m or not p:
        return 0
    junta = "".join(m)
    if junta == "".join(p):
        return 2
    # «Basic Fit» ≈ «BasicFit España», pero «Nike» no es «Nikesha»
    for i in range(len(p)):
        trozo = ""
        for palabra in p[i:]:
            trozo += palabra
            if trozo == junta:
                return 1
            if len(trozo) >= len(junta):
                break
    return 0


def es_pagina_oficial(marca: str, pagina: str, sector: str) -> bool:
    """
    Más estricto que parecido(): para las marcas que elegimos nosotros. «Flex» no es «Flex Fitness
    Studio», pero «Altafit» sí es «ALTAFIT GIMNASIOS» cuando se buscan gimnasios.
    """
    nivel = parecido(marca, pagina)
    if nivel != 1:
        return nivel == 2
    junta, p = "".join(palabras(marca)), palabras(pagina)
    permitidas = _COLETILLAS | set(palabras(sector))
    # Se quita el trozo que es la marca; todo lo que sobra tiene que ser una coletilla conocida
    return any(all(x in permitidas for x in p[:i] + p[j:])
               for i in range(len(p)) for j in range(i + 1, len(p) + 1) if "".join(p[i:j]) == junta)


def id_de_pagina(texto: str) -> str | None:
    """Si la «marca» es un número de página o una URL de la Biblioteca, devuelve el número."""
    t = texto.strip()
    if re.fullmatch(r"\d{6,}", t):
        return t
    m = re.search(r"view_all_page_id=(\d+)", t)
    return m.group(1) if m else None


def _buscar_texto(termino: str, pais: str, max_anuncios: int, campos: str = "id,page_id,page_name",
                  idiomas: list[str] | None = None) -> list[dict]:
    params = {"search_terms": termino[:100], "ad_reached_countries": json.dumps([pais]), "fields": campos}
    if " " in termino:
        params["search_type"] = "KEYWORD_EXACT_PHRASE"
    if idiomas:
        params["languages"] = json.dumps(idiomas)
    anuncios, _ = consultar(params, max_anuncios)
    return anuncios


def buscar_anunciantes(termino: str, pais: str, max_anuncios: int = 600) -> list[tuple[str, str, int]]:
    """Páginas con anuncios activos que contienen el término: (page_id, nombre, anuncios distintos)."""
    ids, nombres = {}, {}
    for i, ad in enumerate(_buscar_texto(termino, pais, max_anuncios)):
        pid = ad.get("page_id")
        if pid:
            ids.setdefault(pid, set()).add(ad.get("id", i))
            nombres[pid] = ad.get("page_name") or pid
    cuenta = Counter({pid: len(v) for pid, v in ids.items()})
    return [(pid, nombres[pid], n) for pid, n in cuenta.most_common()]


def resolver_marca(nombre: str, pais: str, sector_estricto: str | None = None) -> tuple[str, str] | None:
    """
    Página de una marca: la que se llama igual y, si no hay, la que contiene su nombre.
    Con sector_estricto (marcas conocidas) solo vale la página oficial.
    """
    pid = id_de_pagina(nombre)
    if pid:
        return pid, pid
    candidatas = [(parecido(nombre, c[1]), c[2], c) for c in buscar_anunciantes(nombre, pais, max_anuncios=300)]
    validas = [c for c in candidatas if c[0] > 0
               and (sector_estricto is None or es_pagina_oficial(nombre, c[2][1], sector_estricto))]
    if not validas:
        return None
    elegida = max(validas, key=lambda c: (c[0], c[1]))[2]
    return elegida[0], elegida[1]


def anunciantes_de_sector(sector: str, pais: str):
    """
    Hace las búsquedas del sector y descarta el ruido.
    Devuelve (páginas ordenadas, anuncios encontrados, términos, está en el catálogo).
    """
    terminos, en_catalogo = terminos_de_busqueda(sector)
    anuncios = []
    for t in terminos:
        anuncios += _buscar_texto(t, pais, MAX_POR_BUSQUEDA, CAMPOS_BUSQUEDA, IDIOMAS_ESPANA)
    nombre = buscar_sector(sector) or sector
    return ordenar_anunciantes(anuncios, nombre, terminos), anuncios, terminos, en_catalogo


def marcas_conocidas(sector: str, pais: str, maximo: int = MAX_MARCAS, log=print) -> dict[str, str]:
    """Las primeras marcas conocidas del sector que tienen anuncios activos: {page_id: nombre}."""
    nombre = buscar_sector(sector)
    paginas: dict[str, str] = {}
    for marca in CONOCIDAS.get(nombre, ()):
        if len(paginas) >= maximo:
            break
        hallada = resolver_marca(marca, pais, sector_estricto=nombre)
        log(f"  conocida «{marca}» → {hallada[1] if hallada else 'sin anuncios activos'}")
        if hallada:
            paginas[hallada[0]] = hallada[1]
    return paginas


def anuncios_de_pagina(page_id: str, pais: str, max_anuncios: int = MAX_POR_MARCA) -> tuple[list[dict], bool]:
    params = {"search_page_ids": json.dumps([page_id]), "ad_reached_countries": json.dumps([pais]), "fields": CAMPOS}
    return consultar(params, max_anuncios)


@dataclass
class Recogida:
    anuncios: list[dict] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)  # lo que quien lee el informe debe saber


def recolectar(sol: Solicitud, max_marcas: int = MAX_MARCAS, max_por_marca: int = MAX_POR_MARCA, log=print) -> Recogida:
    r = Recogida()
    paginas: dict[str, str] = {}
    if sol.marcas:
        for m in sol.marcas[:max_marcas]:
            hallada = resolver_marca(m, sol.pais)
            log(f"  marca «{m}» → {hallada[1] + ' (' + hallada[0] + ')' if hallada else 'no encontrada'}")
            if hallada:
                paginas[hallada[0]] = hallada[1]
            else:
                r.avisos.append(f"No hemos encontrado anuncios activos de una página llamada «{m}» en {sol.nombre_pais}.")
        if len(sol.marcas) > max_marcas:
            r.avisos.append(f"El informe admite {max_marcas} marcas; el resto no se ha incluido.")
    else:
        paginas = marcas_conocidas(sol.industria, sol.pais, max_marcas, log)
        conocidas = len(paginas)
        if conocidas:
            r.avisos.append("Marcas: anunciantes conocidos del sector con anuncios activos. "
                            "No es una lista completa: puedes pedir las marcas que quieras comparar.")
        if conocidas < MIN_MARCAS:
            encontradas, _, terminos, en_catalogo = anunciantes_de_sector(sol.industria, sol.pais)
            nuevas = [(pid, n) for pid, n, _ in encontradas if pid not in paginas][:max_marcas - conocidas]
            paginas.update(nuevas)
            log(f"  anunciantes para {terminos}: {', '.join(n for _, n in nuevas) or 'ninguno'}")
            if nuevas:
                buscado = ", ".join(f"«{t}»" for t in terminos)
                r.avisos.append(f"{'Además, marcas' if conocidas else 'Marcas'} detectadas automáticamente buscando "
                                f"{buscado} en los anuncios: puede colarse alguna que no sea del sector.")
            if not en_catalogo:
                r.avisos.append(f"«{sol.industria}» no está en nuestro catálogo de sectores: se han buscado "
                                "esas palabras tal cual y los resultados pueden ser incompletos.")

    for pid, nombre in paginas.items():
        ads, quedan = anuncios_de_pagina(pid, sol.pais, max_por_marca)
        nombre = (ads[0].get("page_name") if ads else None) or nombre
        log(f"  {nombre}: {len(ads)}{'+' if quedan else ''} anuncios activos")
        if quedan:
            r.avisos.append(f"{nombre} tiene más de {max_por_marca} anuncios activos: solo se analizan {max_por_marca}, "
                            "así que su cuota real es mayor.")
        elif not ads:
            r.avisos.append(f"{nombre} no tiene anuncios activos en {sol.nombre_pais}.")
        r.anuncios += ads
    return r
