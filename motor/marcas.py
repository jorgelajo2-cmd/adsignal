"""
Anunciantes conocidos de cada sector en España.

Buscar palabras en los anuncios trae ruido (apps de series, tiendas dudosas). Por eso, en los
sectores principales se prueban primero estas marcas, de más a menos conocida, y solo salen
en el informe las que tienen anuncios activos. Para añadir una, escríbela tal como se llama
su página de Facebook.
"""

CONOCIDAS: dict[str, tuple[str, ...]] = {
    # Deporte
    "Gimnasios": ("Basic-Fit", "Altafit", "VivaGym", "McFit", "Anytime Fitness", "Synergym", "Forus", "GO fit", "Fitness Park", "Metropolitan"),
    "Tiendas de deporte": ("Decathlon", "Sprinter", "JD Sports", "Intersport", "Forum Sport"),
    "Nutrición deportiva": ("Myprotein", "HSN", "Prozis", "Life Pro"),
    # Salud
    "Clínicas dentales": ("Vitaldent", "Sanitas Dental", "Adeslas Dental", "Caredent", "Asisa Dental", "Dentix", "DentalCoop"),
    "Ortodoncia": ("Impress", "Invisalign", "Vitaldent"),
    "Clínicas estéticas": ("Clínicas Dorsia", "Clínica Menorca", "Centros Ideal"),
    "Depilación láser": ("Centros Ideal", "Centros Único", "Láser 2000"),
    "Injerto capilar": ("Insparya", "Svenson"),
    "Ópticas": ("Multiópticas", "General Optica", "Alain Afflelou", "Opticalia", "Soloptical"),
    "Audífonos": ("GAES", "Audika", "Amplifon"),
    "Cirugía ocular": ("Clínica Baviera", "Miranza"),
    "Psicología": ("TherapyChat", "Unobravo", "ifeel"),
    # Belleza y moda
    "Cosmética": ("Primor", "Druni", "Freshly Cosmetics", "Sephora", "L'Oréal Paris", "NIVEA"),
    "Perfumes": ("Druni", "Primor", "Sephora", "Douglas", "Perfumería Júlia"),
    "Peluquerías": ("Marco Aldany", "Llongueras"),
    "Moda": ("Zara", "Mango", "MANGO Man", "SHEIN", "Springfield", "Pull&Bear", "Stradivarius", "El Corte Inglés"),
    "Calzado": ("Pikolinos", "Camper", "Skechers", "Deichmann"),
    "Joyería": ("Pandora", "TOUS", "Aristocrazy", "PDPAOLA"),
    "Gafas de sol": ("Hawkers", "Northweek"),
    "Lencería y baño": ("women'secret", "Etam", "Calzedonia", "Intimissimi"),
    # Comida y bebida
    "Supermercados": ("Mercadona", "Carrefour", "Lidl", "Alcampo", "Eroski", "ALDI", "Consum"),
    "Comida a domicilio": ("Glovo", "Just Eat", "Uber Eats", "Telepizza", "Domino's Pizza"),
    "Restaurantes": ("McDonald's", "Burger King", "KFC", "Foster's Hollywood", "VIPS", "GOIKO"),
    "Café": ("Nespresso", "Marcilla", "Saimaza", "Incapto"),
    "Vino": ("Bodeboca", "Vivino", "Familia Torres", "Campo Viejo", "Marqués de Riscal", "Vinoselección"),
    "Cerveza": ("Mahou", "Estrella Galicia", "Cruzcampo", "Estrella Damm", "Ambar"),
    # Hogar y energía
    "Muebles": ("IKEA", "Conforama", "JYSK", "Kave Home", "Merkamueble", "Maisons du Monde"),
    "Colchones": ("Flex", "Pikolin", "Maxcolchon", "Emma"),
    "Electrodomésticos": ("MediaMarkt", "Worten", "Cecotec"),
    "Alarmas y seguridad": ("Securitas Direct", "Prosegur Alarmas", "ADT", "Movistar Prosegur Alarmas"),
    "Luz y gas": ("Iberdrola", "Endesa", "Naturgy", "Repsol", "TotalEnergies", "Octopus Energy", "Holaluz"),
    "Placas solares": ("Holaluz", "SotySolar", "Solarprofit", "Iberdrola"),
    # Tecnología
    "Telefonía e internet": ("Movistar", "Orange", "Vodafone", "Yoigo", "DIGI", "MásMóvil", "Pepephone", "Lowi"),
    "Electrónica": ("MediaMarkt", "PcComponentes", "Samsung", "Xiaomi"),
    "Móviles reacondicionados": ("Back Market", "Swappie"),
    "Streaming": ("Netflix", "Disney+", "Movistar Plus+", "Filmin", "SkyShowtime"),
    "Apps de citas": ("Meetic", "Tinder", "Bumble"),
    # Dinero y seguros
    "Bancos": ("BBVA", "CaixaBank", "Banco Santander", "Banco Sabadell", "ING", "Openbank", "Bankinter", "Unicaja", "ABANCA", "Revolut"),
    "Préstamos": ("Cofidis", "Younited", "Cetelem"),
    "Hipotecas": ("iAhorro", "Trioteca"),
    "Inversión": ("MyInvestor", "Indexa Capital", "Trade Republic"),
    "Seguros": ("MAPFRE", "Allianz", "AXA", "Línea Directa", "Mutua Madrileña", "Santalucía"),
    "Seguros de coche": ("MAPFRE", "Línea Directa", "Verti", "Allianz Direct", "AMV Seguros", "Mutua Madrileña", "Qualitas Auto", "Génesis"),
    "Seguros de hogar": ("Línea Directa", "MAPFRE", "Santalucía", "Tuio"),
    "Seguros de salud": ("Sanitas", "Adeslas", "Asisa", "DKV"),
    "Seguros de decesos": ("Santalucía", "Ocaso"),
    # Inmobiliario y motor
    "Inmobiliarias": ("Tecnocasa", "Redpiso", "Century 21", "RE/MAX", "Engel & Völkers"),
    "Obra nueva": ("Neinor Homes", "AEDAS Homes", "Vía Célere"),
    "Coches nuevos": ("SEAT", "Toyota", "Renault", "Volkswagen", "Kia", "Hyundai", "Peugeot", "CUPRA", "Dacia", "MG"),
    "Coches de segunda mano": ("Flexicar", "OcasionPlus", "Clicars", "coches.net"),
    "Coches eléctricos e híbridos": ("Tesla", "BYD", "MG", "Kia", "Hyundai"),
    "Renting": ("Arval", "Northgate", "Ayvens"),
    "Talleres": ("Midas", "Norauto", "Carglass"),
    # Educación y viajes
    "Academias de idiomas": ("Wall Street English", "British Council", "Vaughan", "Babbel", "Preply"),
    "Formación online": ("Domestika", "Udemy"),
    "Oposiciones": ("MasterD", "Adams Formación", "OpositaTest"),
    "Universidades": ("UNIR", "UOC", "Universidad Europea", "VIU"),
    "Másteres": ("EAE Business School", "ESIC", "IMF", "OBS Business School"),
    "Viajes": ("Viajes El Corte Inglés", "B the travel brand", "Halcón Viajes", "Logitravel", "eDreams"),
    "Hoteles": ("Meliá", "Barceló", "NH Hotels", "Iberostar", "RIU Hotels"),
    "Vuelos": ("Iberia", "Vueling", "Ryanair", "Air Europa", "easyJet"),
    "Cruceros": ("MSC Cruceros", "Costa Cruceros"),
    # Otros
    "Mascotas": ("Tiendanimal", "Kiwoko", "zooplus"),
    "Comida para mascotas": ("Royal Canin", "Purina", "Dogfy Diet"),
    "Empleo": ("InfoJobs", "Adecco", "Randstad"),
    "Mensajería y paquetería": ("SEUR", "MRW", "Correos"),
}
