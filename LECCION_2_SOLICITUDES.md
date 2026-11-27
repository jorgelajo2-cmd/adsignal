# Lección 2: de "lead" a "solicitud de informe"

El formulario ya no pide solo un email: pide **sector, país y marcas**. Hay que adaptar la hoja y el escenario de Make para guardar esos datos, y añadir dos columnas que usará el motor: `id` y `estado`.

**Lo que aprendes:** cambiar la estructura de datos de una automatización sin romperla, y usar variables del sistema de Make.

---

## 1. Cómo encaja todo

```
Landing ──► Make: webhook ──► Sheets "Solicitudes" (estado = pendiente)
                                        │
                     motor de informes  ◄┘  lee las pendientes
                     (python -m motor)      genera el informe
                                        │
                                        └─► estado = enviado + email (próxima lección)
```

La hoja hace de **cola de trabajo**: Make escribe las solicitudes y el motor las va procesando. Es un patrón muy común. Separar "recibir" de "procesar" hace que, si el motor falla, no se pierda ninguna solicitud.

## 2. Actualiza la hoja (5 min)

1. En **adsignal_leads**, cambia el nombre de la pestaña **Leads** a **Solicitudes**.
2. Sustituye la fila 1 por estos encabezados (A–P):

`fecha` · `id` · `email` · `industria` · `pais` · `marcas` · `consentimiento` · `utm_source` · `utm_medium` · `utm_campaign` · `utm_content` · `pagina` · `estado` · `informe` · `enviado_en` · `error`

3. Borra las filas de prueba antiguas (2, 3…), porque tienen las columnas en otro orden.

## 3. Actualiza el webhook (5 min)

El formulario envía campos nuevos (`industria`, `pais`, `marcas`), así que Make tiene que volver a aprenderlos:

1. Abre el escenario y haz clic en el webhook → **Redetermine data structure**.
2. Abre la landing en local (`http://localhost:8123/?utm_source=prueba`), rellena el formulario con un sector real y envía.
3. Debe salir **Successfully determined**, con `industria`, `pais` y `marcas` en la lista.

## 4. Actualiza el módulo de Google Sheets (10 min)

1. Abre el módulo **Add a Row** → en **Sheet Name** elige **Solicitudes**. Make leerá los encabezados nuevos.
2. Mapea:

| Columna | Qué pones |
|---|---|
| fecha | `now` |
| id | Pestaña **Make** (icono de engranaje) del panel → **Execution ID**. Es un identificador único de cada ejecución |
| email, industria, pais, marcas, utm_*, pagina | El campo del webhook con el mismo nombre |
| consentimiento | `consent` |
| estado | Escríbelo a mano: `pendiente` |
| informe, enviado_en, error | Vacíos (los rellenará el motor) |

3. **OK** y **guarda** (disquete).

## 5. Prueba

Con el escenario activo, envía el formulario. En la hoja tiene que aparecer una fila con el sector, el país, un id y `pendiente`.

---

## Mientras tanto: genera informes con el motor

Puedes generar un informe con datos de ejemplo desde la terminal:

```powershell
python -m motor --industria "gimnasios" --salida web/informes
```

```powershell
python -m motor --industria "seguros de coche" --marcas "Marca A, Marca B" --salida web/informes
```

El informe aparece en `web/informes/` (HTML para verlo y JSON con todos los datos).

| Opción | Qué hace |
|---|---|
| `--fuente ejemplo` | Datos inventados para probar (por defecto) |
| `--fuente meta` | Datos reales de la API de Meta. Necesita `META_TOKEN` |
| `--ia auto / si / no` | Análisis con Claude si hay `ANTHROPIC_API_KEY`; si no, con reglas |

## Siguiente lección

**Lección 3: cerrar el círculo.** El motor leerá las solicitudes pendientes de la hoja, generará cada informe, lo enviará por Brevo y marcará la fila como `enviado`. Para eso necesitaremos tu cuenta de Brevo y una "cuenta de servicio" de Google, que es la forma segura de que un programa lea y escriba en tu hoja.
