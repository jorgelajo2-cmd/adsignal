# adsignal: hoja de ruta

Informe gratuito con los anuncios de Meta de las marcas de un sector. Primer sector: gimnasios y fitness en España.

**Regla de oro:** primero que funcione a mano, después automatizar. Nunca esperar a la API para avanzar.

---

## Fase 0: marca y web ✅
- [x] Nombre de trabajo e identidad (`web/brand.css`, `web/logo.svg`)
- [x] Landing con formulario, consentimiento, UTMs y evento `generate_lead` (`web/index.html`)
- [x] Informe de ejemplo con la misma estética (`web/informe-ejemplo.html`)
- [x] Borrador de política de privacidad (`web/privacidad.html`)

## Fase 1: hacerlo real (esta semana, 0 €)
1. **Pedir acceso a la API de Meta** el primer día, porque la verificación de identidad tarda. Ver paso 1 de `PLAN_AUTOMATIZACION.md`.
2. **Elegir 5 gimnasios reales** con anuncios activos en España (en https://www.facebook.com/ads/library, país: España, categoría: todos los anuncios).
3. **Hacer el primer informe real a mano**, revisando sus anuncios en la web de la Biblioteca. Unas 2–3 horas.
4. **Sustituir los datos de ejemplo** de la landing y del informe por los reales, y quitar los avisos de "datos de ejemplo".
5. **Conectar el formulario a Brevo** (plan gratuito):
   - Lista "Informe gimnasios" con los atributos `SECTOR`, `UTM_SOURCE`, `UTM_CAMPAIGN`
   - Doble confirmación (double opt-in) activada
   - Automatización: email de bienvenida inmediato con el último informe
6. **Publicar la web gratis** en Netlify o Cloudflare Pages (arrastrar la carpeta `web`). El dominio es opcional (~10 €/año).
7. **Medición:** GA4 + Google Tag Manager (el evento `generate_lead` ya se envía) + Meta Pixel. En la UE, si pones GA4 o el Pixel, necesitas un **banner de cookies** que pida consentimiento.
8. **Completar la política de privacidad** con tus datos.

## Fase 2: conseguir los primeros suscriptores (semanas 2–4, ~50 €)
- Publicar cada informe resumido en LinkedIn, con enlace a la landing (`?utm_source=linkedin&utm_medium=organic`)
- Campaña en Meta Ads hacia la landing: 3–5 €/día, 2 o 3 creatividades en test A/B, objetivo: clientes potenciales
- Público: dueños y responsables de marketing de gimnasios y estudios, entrenadores personales y agencias de fitness
- Métricas: CTR, coste por suscriptor, conversión de la landing, apertura y clics de los emails

## Fase 3: automatizar (cuando llegue el acceso a la API)
Ver `PLAN_AUTOMATIZACION.md`: script de prueba → Google Sheets → escenario en Make → análisis con IA → borrador del informe.
El informe sigue revisándose a mano antes de enviarlo: la IA redacta y tú editas.

## Fase 4: caso de estudio (semanas 6–8)
- Dashboard en Looker Studio: inversión → visitas → suscriptores → aperturas
- Página del caso de estudio con la misma estética: objetivo, arquitectura, campañas, tests, resultados y qué no funcionó
- Actualizar el CV y LinkedIn con las cifras reales
