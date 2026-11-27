"""
El catálogo de sectores y las palabras con las que se busca cada uno en España.

La API de Meta no sabe de sectores: busca palabras en los anuncios. Por eso cada sector
tiene hasta 3 búsquedas. Mejor expresiones concretas («cuenta sin comisiones») que
palabras con varios sentidos («banco»). Las expresiones de varias palabras se buscan exactas.

Este archivo es la única fuente: la lista de la web (web/sectores.js) se genera con

    python -m motor.sectores
"""
from __future__ import annotations

import json
from pathlib import Path

from .solicitud import slug

# categoría → sector → búsquedas
CATALOGO: dict[str, dict[str, tuple[str, ...]]] = {
    "Deporte y fitness": {
        "Gimnasios": ("gimnasio", "gym"),
        "Yoga y pilates": ("pilates", "clases de yoga"),
        "Entrenamiento funcional": ("crossfit", "entrenamiento funcional", "box de entrenamiento"),
        "Entrenadores personales": ("entrenador personal", "entrenamiento personal"),
        "Tiendas de deporte": ("tienda de deportes", "material deportivo", "equipamiento deportivo"),
        "Nutrición deportiva": ("proteína whey", "creatina", "nutrición deportiva"),
        "Bicicletas": ("bicicleta eléctrica", "tienda de bicicletas", "bicicletas"),
        "Pádel": ("pádel", "palas de pádel", "pistas de pádel"),
        "Running": ("zapatillas de running", "carrera popular", "maratón"),
    },
    "Salud": {
        "Clínicas dentales": ("clínica dental", "implantes dentales", "dentista"),
        "Ortodoncia": ("ortodoncia invisible", "ortodoncia", "alineadores dentales"),
        "Clínicas estéticas": ("clínica estética", "medicina estética", "ácido hialurónico"),
        "Depilación láser": ("depilación láser", "depilación definitiva"),
        "Injerto capilar": ("injerto capilar", "caída del cabello", "trasplante capilar"),
        "Ópticas": ("gafas graduadas", "óptica", "lentillas"),
        "Audífonos": ("audífonos", "centro auditivo", "pérdida auditiva"),
        "Fisioterapia": ("fisioterapia", "fisioterapeuta"),
        "Psicología": ("psicólogo", "terapia online", "psicología"),
        "Nutrición y dietas": ("nutricionista", "plan de alimentación", "perder peso"),
        "Cirugía ocular": ("operación de miopía", "cirugía refractiva", "operarte la vista"),
        "Fertilidad": ("clínica de fertilidad", "reproducción asistida", "congelar óvulos"),
        "Farmacia y parafarmacia": ("parafarmacia", "farmacia online"),
        "Suplementos y vitaminas": ("complemento alimenticio", "vitaminas", "colágeno"),
        "Residencias de mayores": ("residencia de mayores", "residencia de ancianos", "centro de día"),
        "Cuidado a domicilio": ("cuidado de mayores", "ayuda a domicilio", "cuidadores a domicilio"),
    },
    "Belleza": {
        "Cosmética": ("cosmética", "cosmética natural"),
        "Cuidado de la piel": ("sérum facial", "crema antiarrugas", "rutina facial"),
        "Maquillaje": ("maquillaje", "base de maquillaje", "labial"),
        "Perfumes": ("perfume", "fragancia", "perfumería"),
        "Cuidado del cabello": ("champú", "mascarilla capilar", "cuidado del cabello"),
        "Peluquerías": ("peluquería", "salón de belleza"),
        "Barberías": ("barbería", "cuidado de la barba"),
        "Uñas": ("manicura", "uñas de gel", "centro de uñas"),
    },
    "Moda": {
        "Moda": ("nueva colección", "tienda de ropa", "moda"),
        "Moda mujer": ("moda mujer", "ropa de mujer", "vestidos"),
        "Moda hombre": ("moda hombre", "ropa de hombre", "camisas de hombre"),
        "Moda infantil": ("ropa infantil", "moda infantil", "ropa de niños"),
        "Ropa deportiva": ("ropa deportiva", "leggings deportivos"),
        "Calzado": ("zapatillas", "zapatos", "calzado"),
        "Joyería": ("joyería", "joyas", "pendientes de plata"),
        "Relojes": ("relojes", "reloj de pulsera"),
        "Bolsos y accesorios": ("bolsos", "mochilas", "complementos de moda"),
        "Gafas de sol": ("gafas de sol",),
        "Lencería y baño": ("lencería", "ropa interior", "bañadores"),
        "Moda sostenible": ("moda sostenible", "ropa sostenible", "algodón orgánico"),
    },
    "Comida y bebida": {
        "Supermercados": ("supermercado", "tu compra online"),
        "Comida a domicilio": ("comida a domicilio", "pide a domicilio", "envío a domicilio de comida"),
        "Restaurantes": ("restaurante", "reserva tu mesa"),
        "Comida preparada": ("comida preparada", "menú semanal", "platos preparados"),
        "Alimentación saludable": ("alimentación saludable", "productos ecológicos", "sin gluten"),
        "Café": ("café de especialidad", "cápsulas de café", "cafetera"),
        "Vino": ("bodega", "vino tinto", "denominación de origen"),
        "Cerveza": ("cerveza", "cerveza artesana"),
        "Bebidas y refrescos": ("refresco", "bebida energética", "bebida vegetal"),
        "Gourmet": ("jamón ibérico", "aceite de oliva virgen extra", "productos gourmet"),
        "Pastelería y panadería": ("pastelería", "panadería", "tartas por encargo"),
    },
    "Hogar": {
        "Muebles": ("muebles", "sofás", "tienda de muebles"),
        "Colchones": ("colchón", "colchones", "canapé abatible"),
        "Decoración": ("decoración del hogar", "decora tu casa", "textil hogar"),
        "Cocinas": ("muebles de cocina", "reforma de cocina", "cocinas a medida"),
        "Reformas": ("reformas integrales", "reforma de baño", "empresa de reformas"),
        "Ventanas": ("ventanas de PVC", "cambio de ventanas", "cerramientos"),
        "Electrodomésticos": ("electrodomésticos", "lavadora", "robot de cocina"),
        "Climatización": ("aire acondicionado", "calefacción", "caldera"),
        "Alarmas y seguridad": ("alarma para casa", "alarma para negocio", "sistema de alarma"),
        "Limpieza del hogar": ("limpieza del hogar", "aspirador", "productos de limpieza"),
        "Jardín": ("muebles de jardín", "césped artificial", "jardinería"),
        "Piscinas": ("piscinas", "mantenimiento de piscinas"),
        "Mudanzas": ("mudanzas", "empresa de mudanzas"),
    },
    "Energía": {
        "Luz y gas": ("tarifa de luz", "factura de la luz", "luz y gas"),
        "Placas solares": ("placas solares", "autoconsumo solar", "paneles solares"),
        "Aerotermia": ("aerotermia", "bomba de calor"),
        "Cargadores eléctricos": ("punto de recarga", "cargador de coche eléctrico"),
    },
    "Tecnología y telecomunicaciones": {
        "Telefonía e internet": ("fibra y móvil", "tarifa móvil", "internet en casa"),
        "Electrónica": ("electrónica", "televisor", "auriculares"),
        "Móviles reacondicionados": ("móvil reacondicionado", "reacondicionado"),
        "Informática": ("ordenador portátil", "monitor gaming", "PC gaming"),
        "Software para empresas": ("software de gestión", "programa de facturación", "CRM"),
        "Inteligencia artificial": ("inteligencia artificial", "asistente de IA"),
        "Ciberseguridad y VPN": ("antivirus", "VPN", "ciberseguridad"),
        "Alojamiento web y dominios": ("hosting", "crea tu web", "tu tienda online"),
        "Apps de citas": ("app de citas", "conocer gente", "encontrar pareja"),
        "Streaming": ("plataforma de streaming", "estreno en exclusiva", "series y películas"),
        "Videojuegos": ("videojuego", "juega gratis", "descarga el juego"),
    },
    "Banca y finanzas": {
        "Bancos": ("cuenta sin comisiones", "cuenta nómina", "cuenta online"),
        "Préstamos": ("préstamo personal", "préstamo rápido", "financiación"),
        "Hipotecas": ("hipoteca", "hipotecas", "broker hipotecario"),
        "Inversión": ("fondos de inversión", "invierte tu dinero", "plan de pensiones"),
        "Criptomonedas": ("criptomonedas", "bitcoin"),
        "Tarjetas y pagos": ("tarjeta de crédito", "tarjeta de débito", "TPV"),
        "Deudas": ("segunda oportunidad", "cancelar deudas", "reunificar deudas"),
        "Gestorías y asesorías": ("gestoría", "asesoría fiscal", "declaración de la renta"),
    },
    "Seguros": {
        "Seguros": ("seguro", "aseguradora"),
        "Seguros de coche": ("seguro de coche", "seguro de moto", "seguro de auto"),
        "Seguros de hogar": ("seguro de hogar", "seguro para tu casa"),
        "Seguros de salud": ("seguro de salud", "seguro médico"),
        "Seguros de vida": ("seguro de vida",),
        "Seguros de decesos": ("seguro de decesos",),
        "Seguros de mascotas": ("seguro de mascotas", "seguro para perros"),
    },
    "Inmobiliario": {
        "Inmobiliarias": ("inmobiliaria", "vende tu piso", "agencia inmobiliaria"),
        "Obra nueva": ("obra nueva", "promoción de viviendas", "viviendas de obra nueva"),
        "Alquiler": ("alquiler de pisos", "pisos en alquiler", "alquiler garantizado"),
        "Inversión inmobiliaria": ("inversión inmobiliaria", "crowdfunding inmobiliario"),
        "Trasteros": ("trasteros", "alquiler de trastero"),
        "Coworking y oficinas": ("coworking", "alquiler de oficinas"),
    },
    "Motor": {
        "Coches nuevos": ("coche nuevo", "concesionario", "prueba de conducción"),
        "Coches de segunda mano": ("coches de segunda mano", "coches de ocasión", "vende tu coche"),
        "Coches eléctricos e híbridos": ("coche eléctrico", "híbrido enchufable", "100% eléctrico"),
        "Renting": ("renting", "renting de coche"),
        "Alquiler de coches": ("alquiler de coches", "rent a car"),
        "Motos": ("motocicleta", "motos", "scooter"),
        "Talleres": ("taller mecánico", "revisión del coche", "cambio de aceite"),
        "Neumáticos": ("neumáticos",),
        "Autoescuelas": ("autoescuela", "carnet de conducir"),
        "Patinetes eléctricos": ("patinete eléctrico",),
    },
    "Educación": {
        "Academias de idiomas": ("academia de inglés", "curso de inglés", "aprender idiomas"),
        "Formación online": ("curso online", "formación online"),
        "Oposiciones": ("oposiciones", "preparar oposiciones", "academia de oposiciones"),
        "Formación profesional": ("formación profesional", "grado superior", "ciclo formativo"),
        "Universidades": ("universidad", "grado universitario"),
        "Másteres": ("máster", "posgrado", "MBA"),
        "Programación y datos": ("bootcamp", "curso de programación", "análisis de datos"),
        "Marketing digital": ("curso de marketing digital", "máster en marketing"),
        "Clases particulares": ("clases particulares", "academia de refuerzo"),
        "Colegios y escuelas infantiles": ("colegio privado", "escuela infantil", "guardería"),
        "Campamentos": ("campamento de verano", "campamentos"),
    },
    "Viajes y ocio": {
        "Viajes": ("viajes", "agencia de viajes", "paquete vacacional"),
        "Hoteles": ("hotel", "reserva directa"),
        "Vuelos": ("vuelos baratos", "vuelos desde"),
        "Cruceros": ("crucero", "cruceros"),
        "Turismo rural": ("casa rural", "turismo rural", "escapada rural"),
        "Campings": ("camping", "bungalows"),
        "Eventos y entradas": ("compra tus entradas", "festival de música", "concierto"),
        "Parques de ocio": ("parque de atracciones", "parque temático", "parque acuático"),
        "Cine y teatro": ("estreno en cines", "teatro", "musical"),
        "Libros": ("librería", "nueva novela", "ebook"),
    },
    "Familia y mascotas": {
        "Mascotas": ("mascotas", "tienda de animales"),
        "Comida para mascotas": ("pienso", "comida para perros", "comida para gatos"),
        "Veterinarios": ("clínica veterinaria", "veterinario"),
        "Bebés": ("productos para bebé", "cochecito de bebé", "pañales"),
        "Juguetes": ("juguetes", "juegos educativos"),
        "Bodas": ("vestidos de novia", "tu boda", "finca para bodas"),
        "Flores y regalos": ("floristería", "ramo de flores", "regalo personalizado"),
        "Funerarias": ("funeraria", "servicios funerarios"),
    },
    "Servicios y empresa": {
        "Abogados": ("abogados", "despacho de abogados", "reclama tu indemnización"),
        "Agencias de marketing": ("agencia de marketing", "agencia de publicidad", "posicionamiento SEO"),
        "Empleo": ("oferta de empleo", "estamos contratando", "trabaja con nosotros"),
        "Mensajería y paquetería": ("envío de paquetes", "mensajería urgente"),
        "Imprenta y publicidad": ("imprenta online", "rotulación", "merchandising"),
        "Franquicias": ("franquicia", "monta tu negocio"),
        "ONG y causas": ("hazte socio", "ONG", "dona ahora"),
    },
}


def _clave(texto: str) -> str:
    """Igual para singular y plural: «hotel» = «Hoteles», «viaje» = «viajes»."""
    palabras = []
    for p in slug(texto).split("-"):
        if len(p) > 3:
            p = p.removesuffix("s").removesuffix("e")
        palabras.append(p)
    return "-".join(palabras)


SECTORES: dict[str, tuple[str, ...]] = {nombre: t for grupo in CATALOGO.values() for nombre, t in grupo.items()}

# Primero los nombres de sector; después las búsquedas, sin pisar a ningún nombre
_INDICE = {_clave(nombre): nombre for nombre in SECTORES}
for _nombre, _terminos in SECTORES.items():
    for _t in _terminos:
        _INDICE.setdefault(_clave(_t), _nombre)


def buscar_sector(texto: str) -> str | None:
    """Nombre del sector del catálogo que corresponde a lo que ha escrito la persona."""
    return _INDICE.get(_clave(texto))


def terminos_de_busqueda(texto: str) -> tuple[list[str], bool]:
    """Devuelve (búsquedas, True si el sector está en el catálogo)."""
    nombre = buscar_sector(texto)
    return (list(SECTORES[nombre]), True) if nombre else ([texto], False)


# ----------------------------------------------------------------------------- web
RUTA_WEB = Path(__file__).resolve().parent.parent / "web" / "sectores.js"


def contenido_web() -> str:
    datos = [[categoria, [[n, list(t)] for n, t in grupo.items()]] for categoria, grupo in CATALOGO.items()]
    return ("// Generado desde motor/sectores.py con «python -m motor.sectores». No editar a mano.\n"
            f"window.SECTORES = {json.dumps(datos, ensure_ascii=False, separators=(',', ':'))};\n")


if __name__ == "__main__":
    RUTA_WEB.write_text(contenido_web(), encoding="utf-8", newline="\n")
    print(f"{len(SECTORES)} sectores en {len(CATALOGO)} categorías → {RUTA_WEB}")
