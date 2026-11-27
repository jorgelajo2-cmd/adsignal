# AdSignal

**Informes automáticos de los anuncios de tu competencia.** Eliges entre 150 sectores en la web y recibes por email un informe con lo que anuncian las marcas de ese mercado en España en Meta: quién publica más anuncios, qué lanza, qué ofertas usa y qué anuncios mantiene activos más tiempo.

🔗 **Web:** https://jorgelajo2-cmd.github.io/adsignal

---

## Cómo funciona

```
Landing ──► Make (webhook) ──► Google Sheets "Solicitudes"  ← cola de trabajo (estado: pendiente)
                                        │
            GitHub Actions (programado)
                                        │  1. generar: API de la Biblioteca de anuncios de Meta
                                        │              métricas (código, siempre exactas)
                                        │              análisis de textos (Claude o reglas)
                                        │              informe HTML + PDF, contacto en Brevo (CRM)
                                        │  2. publicar: GitHub Pages (web e informes)
                                        │  3. enviar:   email con el enlace, ya publicado
                                        ▼
            estado: enviado · sin_resultados · error
```

## Seguridad y fiabilidad

- Meta incluye el token en el enlace de cada anuncio: se sustituye por el enlace público al recoger los datos, y nada que lo contenga llega a guardarse.
- Los registros de GitHub Actions son públicos: no muestran emails ni claves.
- Si el token caduca o Meta limita las peticiones, las solicitudes siguen pendientes y se reintentan.
- Una marca que no se encuentra se indica en el informe; nunca se sustituye por otra parecida.

| Pieza | Herramienta | Qué demuestra |
|---|---|---|
| Captación | Landing propia + UTMs + evento `generate_lead` | Funnel y medición |
| Integración | Make (webhook → Google Sheets) | Automatización no-code, mapeo de datos |
| Cola de trabajo | Google Sheets con `id` y `estado` | Diseño de procesos robustos (sin duplicados, trazabilidad de errores) |
| Datos | API de la Biblioteca de anuncios de Meta | Trabajo con APIs, paginación, límites |
| Análisis | Python + Claude | Métricas de paid media, IA con salida estructurada |
| CRM y email | Brevo (atributos, listas, email transaccional) | Segmentación y automatización de email |
| Orquestación | GitHub Actions + Pages | Despliegue y ejecución programada |

## Métricas del informe

- **Cuota de anuncios** por marca (share of voice en número de anuncios activos)
- **Anuncios nuevos** en los últimos 7 días
- **Días activo**: un anuncio que dura semanas suele ser uno que funciona
- **Variantes**: textos distintos (tests A/B, versiones locales)
- **Plataformas**: Facebook, Instagram, Messenger, Audience Network
- **Argumentos y ofertas**: precio, comunidad, urgencia, garantía…

Los números se calculan con código. La IA solo interpreta los textos y tiene prohibido inventar cifras.

## Estructura

```
web/                 Landing, privacidad e informes publicados
motor/               Motor de informes
  solicitud.py       Validación de la petición (sector y marcas; solo España)
  meta_api.py        Recolector de la API de Meta
  sectores.py        Catálogo de sectores y sus búsquedas (genera web/sectores.js)
  marcas.py          Anunciantes conocidos de los sectores principales
  relevancia.py      Descarta el ruido al buscar por palabras
  seguridad.py       Evita que claves o emails acaben en sitios públicos
  metricas.py        Cálculo de métricas
  analisis.py        Interpretación con Claude o reglas
  informe.py         Generación del HTML
  hoja.py            Cola de trabajo en Google Sheets
  correo.py          Brevo: email y contactos
  procesar.py        Procesador de solicitudes pendientes
.github/workflows/   Ejecución programada y publicación
```

## Uso local

```bash
pip install -r requirements.txt
python -m motor --industria "gimnasios"                    # un informe con datos de ejemplo
python -m motor.sectores                                   # tras editar el catálogo, actualiza la lista de la web
python -m motor.procesar --prueba                          # procesa una cola CSV sin enviar emails
python probar_api.py "Basic-Fit" "McFit"                   # prueba la API real (pide el token sin mostrarlo)
python -m unittest discover -s tests                       # pruebas, sin red ni credenciales
```

## Limitaciones

- Solo analiza España. La API de Meta ofrece todos los anuncios en la UE y Reino Unido; centrarse en un país permite afinar los sectores.
- La API no sabe de sectores. En los principales se usan anunciantes conocidos; en el resto se buscan palabras y se filtra el ruido (apps de series, tiendas dudosas), pero puede colarse alguna marca ajena. Indicar las marcas es lo más preciso.
- Sin token de Meta, el sistema funciona con datos de ejemplo, y así se indica en cada informe.

---

Proyecto de marketing digital: captación, CRM, automatización y análisis de paid media.
