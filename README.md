# adsignal

**Informes automáticos de los anuncios de tu competencia.** Eliges sector y país (UE) en la web y recibes por email un informe con lo que anuncian las marcas de ese mercado en Meta: quién invierte más, qué lanza, qué ofertas usa y qué anuncios mantiene activos más tiempo.

🔗 **Web:** https://jorgelajo2-cmd.github.io/adsignal

---

## Cómo funciona

```
Landing ──► Make (webhook) ──► Google Sheets "Solicitudes"  ← cola de trabajo (estado: pendiente)
                                        │
            GitHub Actions, cada 15 min: python -m motor.procesar
                                        │  1. API de la Biblioteca de anuncios de Meta
                                        │  2. Métricas (código, siempre exactas)
                                        │  3. Análisis de los textos (Claude, con alternativa por reglas)
                                        │  4. Informe HTML
                                        │  5. Contacto en Brevo (CRM) + email con el informe
                                        ▼
            GitHub Pages publica la web y los informes
```

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
  solicitud.py       Validación de la petición (sector, país UE, marcas)
  meta_api.py        Recolector de la API de Meta
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
python -m motor --industria "gimnasios" --pais ES          # un informe con datos de ejemplo
python -m motor.procesar --prueba                          # procesa una cola CSV sin enviar emails
```

## Limitaciones

- La API de Meta solo ofrece **todos** los anuncios de países de la UE (Ley de Servicios Digitales). Fuera de la UE solo hay anuncios políticos.
- Sin token de Meta, el sistema funciona con datos de ejemplo, y así se indica en cada informe.

---

Proyecto de marketing digital: captación, CRM, automatización y análisis de paid media.
