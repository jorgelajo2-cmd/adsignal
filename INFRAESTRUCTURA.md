# adsignal: infraestructura, paso a paso

El sistema tiene **dos líneas** que se juntan en el email:

- **Motor de datos:** API de Meta → Make → Google Sheets → IA → informe
- **Captación de leads:** anuncios → landing → Brevo (CRM) → email con el informe
- **Medición**, por encima de todo: GA4 + Tag Manager + Looker Studio

Cada paso de abajo se construye, se prueba y se entiende antes de pasar al siguiente.

---

## Las herramientas y por qué cada una

| Pieza | Herramienta | Coste | Por qué esta |
|---|---|---|---|
| Datos | API de la Biblioteca de anuncios de Meta | 0 € | Fuente oficial y pública; nada de copiar a mano ni "scraping" |
| Orquestación | **Make** | 0 € (1.000 créditos/mes) | Es la herramienta de automatización que más aparece en ofertas de marketing; todo es visual |
| Base de datos | **Google Sheets** | 0 € | Ves los datos tal cual; se conecta a Make y a Looker Studio |
| Análisis | IA (Gemini u OpenAI) desde Make | 0–5 € | Clasifica ángulo y oferta de cada anuncio |
| CRM y email | **Brevo** | 0 € (300 emails/día) | CRM + formularios + automatizaciones + doble confirmación, cumple con la normativa europea |
| Web | Netlify o Cloudflare Pages | 0 € | Publicar la carpeta `web` |
| Medición | GA4, Google Tag Manager, Looker Studio | 0 € | El estándar del sector |

**Python** solo lo usamos para probar cosas rápido (como `probar_api.py`). El sistema en producción vive en Make, para que puedas enseñarlo en una entrevista.

---

## La idea clave para que los datos sean precisos

La API te dice qué anuncios están activos **hoy**. No te dice qué ha cambiado. El cambio lo calculamos nosotros guardando una "foto" cada vez:

| Columna | Qué guarda |
|---|---|
| `ad_id` | Identificador único del anuncio. **Nunca se repite una fila con el mismo id.** |
| `primera_vez_visto` | Fecha de la primera extracción en la que apareció |
| `ultima_vez_visto` | Fecha de la última extracción en la que seguía activo |
| `estado` | `activo` si apareció en la última extracción; `apagado` si no |

Con eso salen las tres métricas del informe sin errores:
- **Nuevos:** fecha de inicio en los últimos 7 días
- **Apagados:** estaban activos la vez anterior y ya no
- **Longevidad:** días entre la fecha de inicio y la última vez visto

Esta lógica ("upsert": si el anuncio existe se actualiza, si no se crea) es lo que hace que el sistema sea preciso. Es también lo más interesante para explicar en una entrevista.

---

## Los pasos

### Paso 1: cuentas y accesos *(lo haces tú, ~1 h + espera de Meta)*
Lo hacemos primero porque la verificación de Meta tarda. Ver la sección "Paso 1 en detalle" abajo.

### Paso 2: base de datos en Google Sheets
- **Construimos:** una hoja con las pestañas `Marcas`, `Anuncios` (con la lógica de arriba), `Extracciones` (registro de cada ejecución) e `Informes`.
- **Aprendes:** modelo de datos, claves únicas, por qué separar datos en bruto de cálculos.
- **Prueba:** añadir filas a mano y ver que los cálculos responden.

### Paso 3: el recolector (API de Meta → Sheets)
- **Primero en Python** con `probar_api.py`, para ver qué devuelve la API y con qué calidad.
- **Después en Make:** escenario `1 · Recoger anuncios`: lee las marcas, llama a la API por cada una, pagina los resultados y hace upsert en `Anuncios`.
- **Aprendes:** qué es una API, tokens, parámetros, paginación, iteradores y agregadores en Make, control de errores.
- **Prueba:** ejecutarlo dos veces seguidas y comprobar que **no duplica** filas.

### Paso 4: el análisis con IA
- **Construimos:** escenario `2 · Clasificar anuncios`: coge los anuncios sin clasificar, pide a la IA ángulo, oferta y tono en formato JSON, y los guarda.
- **Aprendes:** prompts con salida estructurada, coste por llamada, cómo revisar la calidad (comparar 20 anuncios clasificados a mano con lo que dice la IA).
- **Prueba:** que el porcentaje de acierto sea aceptable (>80 %) antes de fiarse.

### Paso 5: el informe
- **Construimos:** la pestaña `Resumen` calcula los números y un escenario `3 · Generar informe` redacta el borrador con IA a partir de esos números.
- **Tú revisas y editas siempre** antes de publicarlo. La IA redacta, tú firmas.
- **Aprendes:** separar datos de narrativa, plantillas.

### Paso 6: captación y CRM en Brevo
- **Construimos:** lista y atributos (`SECTOR`, `UTM_SOURCE`, `UTM_CAMPAIGN`, `FECHA_ALTA`), formulario conectado a la landing, doble confirmación y la automatización:
  1. Alta confirmada → email con el informe de su sector
  2. Si su sector aún no existe → email de "te avisamos" y etiqueta `lista_espera`
  3. A los 7 días, si no abrió → recordatorio
- **Aprendes:** CRM, segmentación, consentimiento (RGPD), automatizaciones con disparadores y condiciones.
- **Prueba:** darte de alta con tu email desde la web y recorrer todo el flujo.

### Paso 7: medición
- **Construimos:** GA4 + Tag Manager (evento `generate_lead` ya preparado en la web), banner de cookies, UTMs en todos los enlaces, y un dashboard en Looker Studio: visitas → leads → confirmados → aperturas, por canal.
- **Aprendes:** atribución, embudo, eventos.

### Paso 8: publicar y conseguir tráfico
- Web en Netlify, primer post en LinkedIn y una campaña pequeña en Meta Ads hacia la landing.
- Con datos reales de captación → caso de estudio.

---

## Paso 1 en detalle

Haz estas cinco cosas. Todas son gratis.

**1. Meta para desarrolladores** *(la más importante: tarda en aprobarse)*
- Entra en https://www.facebook.com/ads/library/api y pulsa para empezar.
- Confirma tu identidad con tu documento. Meta tarda de horas a unos días.
- Crea una cuenta en https://developers.facebook.com y una app de tipo "Empresa" (u "Otro").
- Avísame cuando esté aprobado: generaremos el token juntos y probaremos `probar_api.py`.

**2. Google**
- Usa tu cuenta de Google (o crea una para el proyecto). Aquí vivirán Sheets, Looker Studio, GA4 y Tag Manager.

**3. Make**
- Crea una cuenta en https://www.make.com (plan gratuito).

**4. Brevo**
- Crea una cuenta en https://www.brevo.com (plan gratuito).
- Te pedirá datos de remitente. Si puedes, usa un email propio del proyecto, no uno personal.

**5. Netlify**
- Crea una cuenta en https://www.netlify.com (plan gratuito).

> Las contraseñas y los códigos de verificación son solo tuyos: no me los pases por aquí. Cuando haga falta conectar algo, te diré dónde pegar cada clave.

Mientras Meta verifica tu identidad, seguimos con el **paso 2** (base de datos), que no depende de nada más.
