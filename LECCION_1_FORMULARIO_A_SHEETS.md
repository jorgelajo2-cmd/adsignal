# Lección 1: tu primera automatización

**Objetivo:** cuando alguien rellena el formulario de la landing, sus datos aparecen solos en una hoja de Google.

**Necesitas:** cuenta de Make y cuenta de Google. Tiempo: unos 45 minutos.

```
Landing (formulario)  ──►  Make: Webhook  ──►  Make: Google Sheets "Add a row"  ──►  Hoja "Leads"
       disparo                 recibe                     acción                        resultado
```

---

## Los 5 conceptos de cualquier automatización

Da igual la herramienta (Make, Zapier, n8n, HubSpot): todas funcionan igual.

1. **Disparador (trigger):** lo que pone en marcha la automatización. Puede ser un evento ("alguien envía el formulario") o un horario ("cada lunes a las 8").
2. **Módulos (acciones):** cada paso que se ejecuta después: crear una fila, enviar un email, llamar a una API…
3. **Datos y mapeo:** cada módulo produce datos (en Make se llaman *bundles*) que los siguientes pueden usar. "Mapear" es decirle al módulo de Google Sheets: "en la columna *email*, pon el email que llegó del formulario".
4. **Lógica:** *filtros* (solo seguir si se cumple algo), *routers* (caminos distintos según una condición), *iteradores* (repetir para cada elemento de una lista) y *agregadores* (juntar muchos elementos en uno).
5. **Errores:** qué pasa si algo falla. Una automatización buena avisa y no pierde datos.

Hoy usarás 1, 2 y 3. Los demás van en las lecciones siguientes.

---

## Paso 1: prepara la hoja de Google (5 min)

1. Crea una hoja de cálculo nueva en Google Sheets llamada **adsignal_leads**.
2. Renombra la primera pestaña a **Leads**.
3. Escribe estos encabezados en la fila 1, uno por columna (A–I):

   `fecha` · `email` · `sector` · `consentimiento` · `utm_source` · `utm_medium` · `utm_campaign` · `utm_content` · `pagina`

> **Por qué:** Make escribe en columnas que ya existen. Los encabezados son el "contrato" entre la automatización y la hoja.

## Paso 2: crea el escenario y el disparador (10 min)

1. En Make: **Scenarios → Create a new scenario**.
2. Pulsa el **+** grande y busca **Webhooks** → elige **Custom webhook**.
3. Pulsa **Add**, llámalo `adsignal - formulario landing` y guarda.
4. Make te da una **URL** (algo como `https://hook.eu2.make.com/abc123…`). **Cópiala.**

> **Qué es un webhook:** una dirección web que espera a que le envíen datos. Cuando la landing manda el formulario a esa URL, el escenario se dispara.

## Paso 3: conecta la landing (5 min)

1. Abre `web/index.html` y busca esta línea:
   ```js
   const FORM_ENDPOINT = "";
   ```
2. Pega tu URL entre las comillas:
   ```js
   const FORM_ENDPOINT = "https://hook.eu2.make.com/abc123...";
   ```
3. Guarda el archivo.

> Esta URL no es secreta del todo (cualquiera que vea el código de la web la puede ver), pero no la publiques fuera de la web.

## Paso 4: enséñale a Make qué datos llegan (5 min)

Make todavía no sabe qué campos trae el formulario. Hay que mandarle un envío de prueba:

1. En Make, con el webhook seleccionado, pulsa **Run once** (abajo a la izquierda). Se queda "escuchando".
2. Abre la landing en local (`http://localhost:8123`), rellena el formulario con tu email, marca la casilla y envía.
3. Vuelve a Make: debería aparecer **"Successfully determined"** y, si pulsas en la burbuja del módulo, verás los datos: `email`, `sector`, `consent`, `utm_source`…

> **Esto es el bundle:** el paquete de datos que acaba de entrar. A partir de ahora puedes usar cada campo en los siguientes módulos.

## Paso 5: la acción, escribir en Google Sheets (10 min)

1. Pasa el ratón por el lado derecho del webhook y pulsa el **+** para añadir otro módulo.
2. Busca **Google Sheets** → **Add a Row**.
3. **Connection:** pulsa *Add* y conecta tu cuenta de Google. Make pide permiso; acéptalo solo para tu cuenta.
4. Elige la hoja **adsignal_leads**, pestaña **Leads**, y deja marcado que la tabla tiene encabezados.
5. Ahora **mapea** cada columna. Pulsa en cada campo y elige el dato del webhook en el panel que aparece:

   | Columna | Qué pones |
   |---|---|
   | fecha | `now` (en la pestaña de fecha y hora del panel) |
   | email | `email` |
   | sector | `sector` |
   | consentimiento | `consent` |
   | utm_source… utm_content | sus campos correspondientes |
   | pagina | `pagina` |

6. Pulsa **OK**.

> **Esto es el mapeo:** conectar la salida de un módulo con la entrada del siguiente. Es el 80 % del trabajo en cualquier automatización.

## Paso 6: prueba y actívalo (10 min)

1. Pulsa **Run once** otra vez.
2. Envía el formulario de nuevo, pero esta vez desde esta URL:
   `http://localhost:8123/?utm_source=prueba&utm_medium=leccion&utm_campaign=leccion1`
3. Mira la hoja: debe aparecer una fila nueva con tu email, el sector y **las UTM rellenas**.
4. Si todo está bien: guarda el escenario (icono de disquete) y activa el interruptor **ON**. Desde ahora se ejecuta solo cada vez que llegue un formulario.

---

## Comprueba que lo has entendido

Intenta responder sin mirar:
1. ¿Cuál es el disparador de este escenario y cuál la acción?
2. ¿Por qué hubo que enviar un formulario de prueba antes de configurar Google Sheets?
3. Si añades un campo nuevo al formulario (por ejemplo "nombre"), ¿qué tres cosas tienes que cambiar?

<details>
<summary>Respuestas</summary>

1. Disparador: el webhook recibe el formulario. Acción: añadir una fila en Google Sheets.
2. Para que Make aprendiera la estructura de los datos (qué campos trae el bundle) y así poder mapearlos.
3. El formulario de la web, una columna nueva en la hoja y el mapeo en el módulo de Google Sheets. Además, en Make hay que volver a "enseñarle" la estructura al webhook con *Redetermine data structure*.
</details>

---

## Siguiente lección

**Lección 2: lógica y CRM.** Añadiremos un **router**: si el sector es gimnasios, el contacto entra en Brevo y recibe el informe; si es otro sector, entra en la lista de espera. Aprenderás filtros, routers y a conectar con un CRM.
