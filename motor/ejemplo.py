"""
Anuncios de EJEMPLO con el mismo formato que devuelve la API de Meta.
Sirven para probar todo el motor sin token. Las marcas son inventadas y el
informe lo indica siempre ("datos de ejemplo").
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from .solicitud import Solicitud, slug

MARCAS_FICTICIAS = ["Nova", "Prisma", "Vértice", "Lumen", "Atlas", "Alba", "Kora", "Brío"]

PLANTILLAS = [
    # (ángulo implícito, texto)  — sirven para cualquier sector
    ("Precio", "{P} desde {precio}. Sin permanencia y sin letra pequeña."),
    ("Precio", "{desc} en {p} solo esta semana. Aprovecha antes de que acabe."),
    ("Urgencia", "Últimos días: {oferta}. Después vuelve al precio normal."),
    ("Comunidad", "Más de {n} personas ya confían en nosotros. Únete a la comunidad {marca}."),
    ("Resultados", "Resultados que se notan desde el primer mes. Así lo cuentan nuestros clientes."),
    ("Calidad", "Calidad que se nota y dura años. Así trabajamos en {marca}."),
    ("Conveniencia", "Todo desde la app, cuando quieras y donde quieras. Empieza en 2 minutos."),
    ("Novedad", "Nuevo en {marca}: descubre lo último en {p}."),
    ("Confianza", "Garantía total: si no te convence, te devolvemos el dinero."),
    ("Local", "Ya estamos en tu ciudad. Ven a conocernos y {oferta}."),
]
OFERTAS = ["el primer mes gratis", "un 20 % de descuento", "envío gratis", "una prueba gratuita", "un regalo de bienvenida"]
PRECIOS = ["9,99 €", "19 €", "29,90 €", "4,99 €/mes", "49 €"]
DESCUENTOS = ["-20 %", "-30 %", "2x1", "-15 %"]
PLATAFORMAS = [["facebook", "instagram"], ["instagram"], ["facebook", "instagram", "audience_network"], ["facebook", "instagram", "messenger"]]


def anuncios_de_ejemplo(sol: Solicitud, hoy: date | None = None) -> list[dict]:
    hoy = hoy or sol.fecha
    rnd = random.Random(slug(sol.industria) + sol.pais)  # mismo sector = mismos datos
    producto = sol.industria.lower()
    marcas = sol.marcas or rnd.sample(MARCAS_FICTICIAS, 5)
    anuncios = []
    for i, marca in enumerate(marcas):
        page_id = str(100000 + i)
        n = rnd.randint(6, 28)
        estilo = rnd.sample(PLANTILLAS, 4)  # cada marca tiene 4 "argumentos" favoritos
        plataformas = rnd.choice(PLATAFORMAS)
        for j in range(n):
            angulo, plantilla = rnd.choice(estilo)
            texto = plantilla.format(
                p=producto, P=sol.industria.capitalize(), marca=marca, precio=rnd.choice(PRECIOS), desc=rnd.choice(DESCUENTOS),
                oferta=rnd.choice(OFERTAS), n=rnd.choice(["10.000", "50.000", "200.000"]),
            )
            dias = int(rnd.triangular(0, 120, 8))
            inicio = hoy - timedelta(days=dias)
            anuncios.append({
                "id": f"{page_id}{j:04d}",
                "page_id": page_id,
                "page_name": marca,
                "ad_creation_time": inicio.isoformat(),
                "ad_delivery_start_time": inicio.isoformat(),
                "ad_creative_bodies": [texto],
                "ad_creative_link_titles": [f"{marca} · {sol.industria}"],
                "publisher_platforms": plataformas if rnd.random() > 0.2 else rnd.choice(PLATAFORMAS),
                "languages": ["es"],
                "eu_total_reach": rnd.choice([1200, 5400, 18000, 64000, 230000]),
                "target_ages": rnd.choice([["18", "65+"], ["25", "54"], ["18", "34"]]),
                "target_gender": rnd.choice(["All", "All", "Women", "Men"]),
                "ad_snapshot_url": f"https://www.facebook.com/ads/library/?id={page_id}{j:04d}",
                "_ejemplo": True,
            })
    return anuncios
