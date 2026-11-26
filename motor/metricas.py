"""
Los NÚMEROS del informe. Se calculan con código, nunca con IA, para que sean exactos
y se puedan comprobar.

Definiciones (aparecen también en el informe):
- Activo: el anuncio se está publicando en el país en la fecha del informe.
- Nuevo: empezó a publicarse en los últimos 7 días.
- Días activo: días desde que empezó a publicarse hasta la fecha del informe.
  Si una marca mantiene un anuncio muchas semanas, suele ser porque le funciona.
- Cuota de anuncios: % de los anuncios activos del informe que son de esa marca.
- Creatividades distintas: textos diferentes (muchas variantes = tests A/B o versiones locales).
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from statistics import median

NOMBRES_PLATAFORMA = {
    "facebook": "Facebook", "instagram": "Instagram", "messenger": "Messenger",
    "audience_network": "Audience Network", "threads": "Threads", "whatsapp": "WhatsApp",
}
DIAS_NUEVO = 7


def _fecha(valor) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _texto(ad: dict) -> str:
    cuerpos = ad.get("ad_creative_bodies") or []
    return " ".join(c for c in cuerpos if c).strip()


def _reparto(contador: Counter, total: int) -> list[dict]:
    return [
        {"nombre": NOMBRES_PLATAFORMA.get(k, k.replace("_", " ").title()), "pct": round(100 * v / total)}
        for k, v in contador.most_common()
    ] if total else []


def calcular(anuncios: list[dict], fecha_ref: date) -> dict:
    por_marca: dict[str, list[dict]] = {}
    for ad in anuncios:
        por_marca.setdefault(ad.get("page_id") or ad.get("page_name", "?"), []).append(ad)

    total = len(anuncios)
    todos_dias, plataformas_sector, marcas = [], Counter(), []

    for page_id, ads in por_marca.items():
        dias, plataformas, textos = [], Counter(), {}
        mas_longevo = None
        for ad in ads:
            inicio = _fecha(ad.get("ad_delivery_start_time"))
            d = (fecha_ref - inicio).days if inicio else None
            if d is not None:
                d = max(d, 0)
                dias.append(d)
                if mas_longevo is None or d > mas_longevo["dias"]:
                    mas_longevo = {"dias": d, "texto": _texto(ad), "url": ad.get("ad_snapshot_url", ""), "id": ad.get("id")}
            for p in ad.get("publisher_platforms") or []:
                plataformas[p] += 1
            t = _texto(ad)
            if t:
                # Para el análisis guardamos cada texto distinto una vez, con su antigüedad máxima
                textos[t] = max(textos.get(t, 0), d or 0)
        plataformas_sector.update(plataformas)
        todos_dias.extend(dias)
        edades = Counter(" - ".join(ad.get("target_ages") or []) for ad in ads if ad.get("target_ages"))
        generos = Counter(ad.get("target_gender") for ad in ads if ad.get("target_gender"))
        marcas.append({
            "page_id": page_id,
            "nombre": ads[0].get("page_name") or page_id,
            "activos": len(ads),
            "cuota": round(100 * len(ads) / total) if total else 0,
            "nuevos": sum(1 for d in dias if d <= DIAS_NUEVO),
            "mediana_dias": round(median(dias)) if dias else None,
            "max_dias": max(dias) if dias else None,
            "mas_longevo": mas_longevo,
            "plataformas": _reparto(plataformas, len(ads)),
            "creatividades": len(textos),
            "alcance_ue": sum(int(ad.get("eu_total_reach") or 0) for ad in ads),
            "edades": edades.most_common(1)[0][0] if edades else None,
            "genero": generos.most_common(1)[0][0] if generos else None,
            "textos": [{"texto": t, "dias": d} for t, d in sorted(textos.items(), key=lambda x: -x[1])][:40],
        })

    marcas.sort(key=lambda m: -m["activos"])
    return {
        "fecha_ref": fecha_ref.isoformat(),
        "total_anuncios": total,
        "n_marcas": len(marcas),
        "nuevos": sum(m["nuevos"] for m in marcas),
        "mediana_dias": round(median(todos_dias)) if todos_dias else None,
        "plataformas": _reparto(plataformas_sector, total),
        "marcas": marcas,
    }
