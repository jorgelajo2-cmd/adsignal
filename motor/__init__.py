"""
adsignal · motor de informes

Flujo:  solicitud → recolectar anuncios → métricas → análisis → informe HTML

    solicitud.py   Qué ha pedido la persona (sector, marcas, email). Solo España
    sectores.py    Catálogo de sectores y sus búsquedas
    meta_api.py    Descarga anuncios de la Biblioteca de anuncios de Meta
    ejemplo.py     Genera anuncios de ejemplo para probar sin la API
    metricas.py    Calcula los números del informe (sin IA: siempre exactos)
    analisis.py    Interpreta los textos: con Claude o con reglas si no hay clave
    informe.py     Rellena la plantilla HTML con todo lo anterior
    __main__.py    Lo une todo:  python -m motor --industria "gimnasios"
"""
