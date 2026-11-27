"""
La INTERPRETACIÓN del informe: qué argumentos (ángulos) usa cada marca, qué ofertas,
y las conclusiones.

Dos modos:
- Claude (si hay ANTHROPIC_API_KEY): lee los textos y redacta. Recibe las métricas ya
  calculadas y se le prohíbe inventar números.
- Reglas (sin clave): clasifica por palabras clave y redacta con plantillas. Menos fino,
  pero gratis y siempre disponible.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from collections import Counter

from .solicitud import Solicitud

MODELO = "claude-opus-5-5"

ANGULOS = {
    # Ojo: "€" y "%" no van aquí porque se pierden al quitar acentos; los detecta RE_PRECIO.
    "Precio": ["precio", "descuento", "rebaja", "barato", "ahorra", "2x1", "sin permanencia"],
    "Urgencia": ["ultimos dias", "solo hoy", "solo esta semana", "hasta el", "antes de que", "quedan", "limitad", "aprovecha"],
    "Comunidad": ["comunidad", "unete", "personas", "socios", "confian", "miles"],
    "Resultados": ["resultados", "consigue", "transforma", "objetivo", "se notan"],
    "Calidad": ["calidad", "premium", "durar", "disenado", "el mejor"],
    "Conveniencia": ["app", "facil", "minutos", "donde quieras", "cuando quieras", "online", "a domicilio"],
    "Novedad": ["nuevo", "nueva", "descubre", "lanzamiento", "lo ultimo"],
    "Confianza": ["garantia", "devolvemos", "confianza", "opiniones", "valorad"],
    "Local": ["tu ciudad", "cerca de", "barrio", "ven a"],
}
RE_OFERTAS = [
    r"(?:\b(?:desde|por)\s+(?:solo\s+|sólo\s+)?)?\d+(?:[.,]\d+)?\s?(?:€|euros?\b)(?:\s?/\s?mes)?",
    r"-?\d+\s?%(?:\s?de descuento)?",
    r"2x1",
    r"(?:\w+\s){0,3}gratis(?:\s\w+)?",
    r"\bll[eé]vate\s+(?:una?|tu)\s+\w+",
    r"\bsin matr[ií]cula\b",
    r"\bblack friday\b",
]


def _norm(t: str) -> str:
    return unicodedata.normalize("NFKD", t.lower()).encode("ascii", "ignore").decode()


RE_PRECIO = re.compile(r"\d+(?:[.,]\d+)?\s?(?:€|eur\b|euros?\b)|\d+\s?%", re.I)


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _angulos_de(texto: str) -> list[str]:
    n = _norm(texto)
    angs = [a for a, claves in ANGULOS.items() if any(_norm(c) in n for c in claves)]
    if "Precio" not in angs and RE_PRECIO.search(texto):
        angs.insert(0, "Precio")
    return angs


def _ofertas_de(texto: str) -> list[str]:
    """Ofertas distintas de un texto, escritas siempre igual («1€» y «1 euro» son la misma)."""
    encontradas = []
    for patron in RE_OFERTAS:
        for m in re.finditer(patron, texto, flags=re.I):
            o = re.sub(r"\s?(?:€|euros?\b)", " €", " ".join(m.group(0).lower().split()))
            encontradas.append(o)
    return list(dict.fromkeys(encontradas))


# ----------------------------------------------------------------------------- reglas
def _por_reglas(sol: Solicitud, met: dict) -> dict:
    sector_angulos, por_marca = Counter(), {}
    for m in met["marcas"]:
        angs, ofertas = Counter(), Counter()
        for t in m["textos"]:
            completo = f"{t['texto']}\n{t.get('titulo', '')}"
            for a in _angulos_de(completo):
                angs[a] += 1
                sector_angulos[a] += 1
            for o in _ofertas_de(completo):
                ofertas[o] += 1
        top = [a for a, _ in angs.most_common(3)]
        frases = []
        frases.append(f"{_plural(m['activos'], 'anuncio activo', 'anuncios activos')} ({m['cuota']} % del total), "
                      f"{_plural(m['nuevos'], 'nuevo', 'nuevos')} esta semana.")
        if top:
            frases.append("Apuesta sobre todo por " + " y ".join(x.lower() for x in top[:2]) + ".")
        if m["max_dias"]:
            frases.append(f"Su anuncio más longevo lleva {m['max_dias']} días activo.")
        por_marca[m["page_id"]] = {
            "angulos": top,
            "ofertas": [o for o, _ in ofertas.most_common(3)],
            "tono": "",
            "conclusion": " ".join(frases),
        }

    marcas = met["marcas"]
    total_textos = sum(len(m["textos"]) for m in marcas) or 1
    lider = marcas[0] if marcas else None
    ang_top, ang_n = (sector_angulos.most_common(1)[0] if sector_angulos else ("—", 0))

    if lider and len(marcas) == 1:
        titular = f"{lider['nombre']} tiene {_plural(lider['activos'], 'anuncio activo', 'anuncios activos')} en {sol.nombre_pais}."
    elif lider and lider["cuota"] >= 35:
        # La cuota es sobre las marcas del informe, no sobre todo el sector
        titular = f"{lider['nombre']} publica el {lider['cuota']} % de los anuncios de las marcas analizadas."
    elif lider:
        titular = f"{lider['nombre']} lidera en anuncios y el argumento más repetido es {ang_top.lower()}."
    else:
        titular = "No hemos encontrado anuncios activos."
    subtitulo = (f"{_plural(met['total_anuncios'], 'anuncio activo', 'anuncios activos')} de "
                 f"{_plural(met['n_marcas'], 'marca', 'marcas')} en {sol.nombre_pais}. "
                 f"{met['nuevos']} {'empezó' if met['nuevos'] == 1 else 'empezaron'} en los últimos 7 días.")

    tendencias = []
    if sector_angulos:
        tendencias.append({"titulo": f"{ang_top} es el argumento más usado",
                           "detalle": f"Aparece en {round(100 * ang_n / total_textos)} % de las creatividades distintas."})
    if met["plataformas"]:
        pct = met["plataformas"][0]["pct"]
        primeras = [p["nombre"] for p in met["plataformas"] if p["pct"] == pct]
        if len(primeras) == 1:
            tendencias.append({"titulo": f"{primeras[0]} manda",
                               "detalle": f"El {pct} % de los anuncios se publica en {primeras[0]}."})
        else:  # empate: nombrar solo una sería engañoso
            juntas = ", ".join(primeras[:-1]) + " y " + primeras[-1]
            tendencias.append({"titulo": f"Empate: {juntas}",
                               "detalle": f"Cada una aparece en el {pct} % de los anuncios."})
    mas_activa = max(marcas, key=lambda m: m["nuevos"], default=None)
    if mas_activa and mas_activa["nuevos"] >= 2:
        tendencias.append({"titulo": f"{mas_activa['nombre']} acelera",
                           "detalle": f"Es la marca con más anuncios nuevos: {mas_activa['nuevos']} en 7 días."})
    if met["mediana_dias"] is not None and len(tendencias) < 3:
        tendencias.append({"titulo": "Cuánto duran los anuncios",
                           "detalle": f"La mitad de los anuncios lleva más de {met['mediana_dias']} días activos."})
    return {"fuente": "reglas", "titular": titular, "subtitulo": subtitulo, "tendencias": tendencias[:3], "marcas": por_marca}


# ----------------------------------------------------------------------------- Claude
ESQUEMA = {
    "type": "object",
    "properties": {
        "titular": {"type": "string"},
        "subtitulo": {"type": "string"},
        "tendencias": {"type": "array", "items": {
            "type": "object",
            "properties": {"titulo": {"type": "string"}, "detalle": {"type": "string"}},
            "required": ["titulo", "detalle"], "additionalProperties": False}},
        "marcas": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string"},
                "angulos": {"type": "array", "items": {"type": "string"}},
                "ofertas": {"type": "array", "items": {"type": "string"}},
                "tono": {"type": "string"},
                "conclusion": {"type": "string"},
            },
            "required": ["page_id", "angulos", "ofertas", "tono", "conclusion"], "additionalProperties": False}},
    },
    "required": ["titular", "subtitulo", "tendencias", "marcas"],
    "additionalProperties": False,
}

SISTEMA = """Eres analista de publicidad digital. Escribes informes de competencia a partir de anuncios de la Biblioteca de anuncios de Meta.

Reglas:
- Escribe en español de España, frases cortas y directas, sin adornos ni jerga de IA.
- Usa SOLO los números que vienen en los datos. No inventes ni estimes cifras.
- Cada afirmación tiene que poder comprobarse en los textos o métricas recibidos. Si algo no se puede saber, no lo digas.
- "angulos": 1 a 3 argumentos principales de la marca, con una o dos palabras cada uno (Precio, Comunidad, Resultados, Urgencia, Calidad, Conveniencia, Novedad, Confianza, Local, Sostenibilidad, Exclusividad, Salud… u otro si encaja mejor).
- "ofertas": promociones concretas que aparecen en los textos (máximo 3, tal como aparecen). Lista vacía si no hay.
- "tono": dos o tres palabras.
- "conclusion": una o dos frases con lo más útil para un competidor.
- "titular": la conclusión más interesante del sector en una frase. "subtitulo": el dato que la respalda.
- "tendencias": exactamente 3, cada una con un título de pocas palabras y un detalle de una frase con un dato.
- Incluye en "marcas" todas las marcas recibidas, con su page_id."""


def _por_claude(sol: Solicitud, met: dict) -> dict:
    import anthropic

    datos = {
        "sector": sol.industria, "pais": sol.nombre_pais, "fecha": met["fecha_ref"],
        "totales": {k: met[k] for k in ("total_anuncios", "n_marcas", "nuevos", "mediana_dias", "plataformas")},
        "marcas": [{
            "page_id": m["page_id"], "nombre": m["nombre"], "activos": m["activos"], "cuota_pct": m["cuota"],
            "nuevos_7_dias": m["nuevos"], "mediana_dias_activo": m["mediana_dias"], "max_dias_activo": m["max_dias"],
            "creatividades_distintas": m["creatividades"], "plataformas": m["plataformas"],
            "textos": [{"texto": t["texto"][:400], "titulo": t.get("titulo", "")[:150], "dias_activo": t["dias"]}
                       for t in m["textos"][:25]],
        } for m in met["marcas"]],
    }
    client = anthropic.Anthropic()
    resp = client.beta.messages.create(
        model=MODELO,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # si el modelo rechaza la petición, la API la reintenta en otro modelo
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": ESQUEMA}},
        system=SISTEMA,
        messages=[{"role": "user", "content": "Datos del informe (JSON):\n" + json.dumps(datos, ensure_ascii=False)}],
    )
    if resp.stop_reason != "end_turn":
        raise RuntimeError(f"Respuesta incompleta de Claude (stop_reason={resp.stop_reason})")
    texto = "".join(b.text for b in resp.content if b.type == "text")
    salida = json.loads(texto)
    salida["marcas"] = {m["page_id"]: m for m in salida["marcas"]}
    salida["fuente"] = "claude"
    return salida


def analizar(sol: Solicitud, met: dict, usar_ia: bool | None = None) -> dict:
    """Devuelve titular, subtítulo, tendencias y el análisis de cada marca."""
    base = _por_reglas(sol, met)
    if usar_ia is None:
        usar_ia = bool(os.environ.get("ANTHROPIC_API_KEY"))
    if not usar_ia or not met["marcas"]:
        return base
    try:
        ia = _por_claude(sol, met)
    except Exception as e:  # sin conexión, sin saldo, rechazo… el informe sale igual, con reglas
        print(f"[analisis] Claude no disponible ({type(e).__name__}: {e}). Uso reglas.", file=sys.stderr)
        return base
    # Si a Claude se le olvida alguna marca, la completamos con las reglas
    for pid, a in base["marcas"].items():
        ia["marcas"].setdefault(pid, a)
    return ia
