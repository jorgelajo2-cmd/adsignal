# Lección 3: el envío automático

**Objetivo:** que nadie tenga que tocar nada. Alguien pide un informe en la web y, en menos de media hora, le llega por email.

```
Landing ─► Make ─► Hoja "Solicitudes" (pendiente)
                          │
         GitHub Actions, cada 15 min:  python -m motor.procesar
                          │   1. lee las filas pendientes
                          │   2. genera cada informe
                          │   3. guarda el contacto en Brevo (CRM)
                          │   4. envía el email con el enlace (Brevo)
                          │   5. marca la fila: enviado / error
                          ▼
         GitHub Pages publica la web y los informes
```

**El código ya está hecho y probado en local** (`motor/procesar.py`, `motor/hoja.py`, `motor/correo.py`, `.github/workflows/adsignal.yml`). Lo que falta son las cuentas y las claves, que son tuyas.

> **Las claves no se pegan nunca en el chat ni en el código.** Van en los "secretos" de GitHub (paso 4), que están cifrados.

### Tus datos de configuración (no son secretos)

| Dato | Valor |
|---|---|
| Remitente (Brevo) | `adsignal1@gmail.com` |
| ID de la lista de Brevo | `3` |
| Email de la cuenta de servicio | `adsignal-motor@adsignal-515919.iam.gserviceaccount.com` |
| ID de la hoja | `1D2YQ9zAe8vTlqioqYBkBIr1XUx8fu9c5YpR3lsDeXuU` |

Secretos que guardas tú (fuera del proyecto): la **clave de API de Brevo** y el **archivo JSON** de la cuenta de servicio.

---

## Paso 1: Brevo (15 min)

1. **Remitente:** en Brevo, menú de tu cuenta → **Senders, domains & dedicated IPs** → **Senders** → **Add a sender**. Usa el email desde el que quieres enviar y confírmalo desde el correo que te llega.
2. **Atributos del CRM** ✅ hecho: con Brevo en español, **CRM → Contactos → Configuración** (abajo a la izquierda) → **Atributos de contacto** → **Crear atributo**. Creados de tipo *Texto*: `SECTOR`, `PAIS`, `UTM_SOURCE`, `UTM_CAMPAIGN`.
3. **Lista** ✅ hecho: **CRM → Listas → Crear una lista** → `Informes adsignal`, **ID 3**.
4. **Clave de API:** menú de tu cuenta → **SMTP & API** → **API Keys** → **Generate a new API key** → nombre `adsignal`. **Cópiala y guárdala**, porque solo se muestra una vez.

**Qué aprendes:** un CRM guarda **contactos con atributos** (sector, origen…) y **listas**. Con eso, más adelante, podrás segmentar: "todos los que pidieron un informe de cosmética y vinieron de LinkedIn".

## Paso 2: cuenta de servicio de Google (15 min)

Es un "usuario robot" que puede leer y escribir en tu hoja sin usar tu contraseña.

1. Entra en https://console.cloud.google.com → crea un proyecto llamado `adsignal`.
2. **APIs y servicios** → **Biblioteca** → busca **Google Sheets API** → **Habilitar**.
3. **APIs y servicios** → **Credenciales** → **Crear credenciales** → **Cuenta de servicio** → nombre `adsignal-motor` → **Listo**.
4. Entra en la cuenta de servicio → pestaña **Claves** → **Agregar clave** → **Crear clave nueva** → **JSON**. Se descarga un archivo: **guárdalo bien y no lo compartas**.
5. Copia el email de la cuenta de servicio (termina en `iam.gserviceaccount.com`).
6. Abre tu hoja **adsignal_leads** → **Compartir** → pega ese email → rol **Editor** → desmarca "Notificar" → **Compartir**.
7. Apunta el **ID de la hoja**: es la parte de la URL entre `/d/` y `/edit`.

## Paso 3: GitHub (20 min)

1. Crea una cuenta en https://github.com si no tienes.
2. **New repository** → nombre `adsignal` → **Public** → sin README → **Create**.
   - Tiene que ser público para que GitHub Pages sea gratis. El código y los informes (sin emails) serán visibles, lo que te sirve como portfolio. Los emails solo están en tu hoja.
3. Sube el proyecto. Te lo preparo yo en un repositorio local cuando llegues aquí; tú solo tendrás que ejecutar un comando y autorizar en el navegador.
4. En el repositorio: **Settings** → **Pages** → **Source: GitHub Actions**.

## Paso 4: los secretos (10 min)

**Settings** → **Secrets and variables** → **Actions** → **New repository secret**. Crea uno por fila:

| Nombre | Valor |
|---|---|
| `GOOGLE_SA_JSON` | Abre el archivo JSON del paso 2 con el Bloc de notas y pega **todo** su contenido |
| `SHEET_ID` | El ID de la hoja (paso 2.7) |
| `BREVO_API_KEY` | La clave del paso 1.4 |
| `REMITENTE_EMAIL` | El email verificado del paso 1.1 |
| `BREVO_LISTA_ID` | El número de la lista del paso 1.3 |
| `BASE_URL` | `https://TU-USUARIO.github.io/adsignal` |

Más adelante añadirás `META_TOKEN` (datos reales) y `ANTHROPIC_API_KEY` (análisis con IA). Mientras no estén, los informes salen con **datos de ejemplo**, marcados como tales en el informe y en el email.

## Paso 5: la prueba de fuego

1. Pestaña **Actions** → **adsignal** → **Run workflow**. Así se publica la web por primera vez.
2. Abre `https://TU-USUARIO.github.io/adsignal`: es tu landing, ya pública.
3. Pide un informe con tu email.
4. Vuelve a **Actions** → **Run workflow** (o espera hasta 15 minutos).
5. Comprueba:
   - La fila en la hoja pasa a `enviado`, con el enlace del informe.
   - Te llega el email.
   - El contacto aparece en Brevo con su sector y su país.

Si una fila queda en `error`, la columna **error** dice por qué. En **Actions** puedes abrir cada ejecución y leer el registro paso a paso.

---

## Cómo probarlo en local sin credenciales

```powershell
python -m motor.procesar --prueba
```

Lee `solicitudes_prueba.csv` en lugar de la hoja y guarda los emails como archivos en `salida_emails/` en lugar de enviarlos.

## Comprueba que lo has entendido

1. ¿Por qué el procesador marca la fila como `procesando` antes de generar el informe?
2. Si Brevo falla al guardar el contacto, ¿llega el email igualmente?
3. ¿Dónde mirarías si alguien dice que no le ha llegado su informe?

<details><summary>Respuestas</summary>

1. Para que, si dos ejecuciones coinciden, la segunda no procese la misma solicitud y no se envíen dos emails.
2. Sí: el contacto se guarda en un bloque aparte que, si falla, solo deja un aviso en el registro. El informe es lo importante.
3. En la hoja: su fila dice `enviado` (con fecha y enlace) o `error` (con el motivo). Si dice `enviado`, mira en Brevo → **Transactional** → **Logs** si el email rebotó o acabó en spam.
</details>
