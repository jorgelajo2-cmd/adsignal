# Guía: el primer informe real (a mano)

Tiempo: 3–4 horas la primera vez, luego unas 1,5 h. Coste: 0 €.
Herramientas: la Biblioteca de anuncios de Meta y `plantilla_anuncios.xlsx` (súbela a Google Sheets si prefieres).

---

## 1. Elegir 5 marcas (30 min)

En la pestaña **Marcas** hay 10 cadenas de gimnasios como punto de partida. Para cada una:

1. Abre https://www.facebook.com/ads/library
2. País: **España**. Categoría: **Todos los anuncios**.
3. Escribe el nombre de la marca y elige su **página** en el desplegable (no la búsqueda por palabra clave).
4. Filtra por **Activos**.
5. Copia la URL en la columna "Enlace" y apunta cuántos anuncios activos tiene.

Elige 5 que cumplan:
- Tienen **al menos 5 anuncios activos**; con menos no hay nada que contar.
- Son **comparables** entre sí: por ejemplo, 3 low cost y 2 premium, o las 5 low cost.

Marca "Sí" en "¿La sigo?".

## 2. Recoger los anuncios (2 h)

Una fila por anuncio en la pestaña **Anuncios**. Rellena solo las columnas amarillas.

| Columna | De dónde sale |
|---|---|
| Fecha revisión | La fecha de hoy (la misma en todas las filas) |
| ID en la Biblioteca | "Identificador de la biblioteca" en la tarjeta del anuncio |
| Fecha inicio | "Comenzó a circular el…" |
| Plataformas | Los iconos de la tarjeta (Facebook, Instagram, Messenger, Audience Network) |
| Formato | Imagen, vídeo o carrusel |
| Texto principal / Titular / CTA | Abre "Ver detalles del anuncio" y cópialos |
| Oferta | Si hay precio, descuento o algo gratis, resúmelo en pocas palabras |
| Ángulo | El argumento principal (definiciones en la pestaña "Cómo usar") |
| ¿Salen personas? | Sí, si el protagonista es gente y no instalaciones o texto |

Consejos:
- Si una marca tiene muchísimos anuncios casi iguales (mismo texto, distinta imagen), apúntalos todos: que una marca haga muchas variantes también es un dato.
- Si tiene más de 40 anuncios, recoge los 40 más recientes y anota en "Notas" que es una muestra.
- **Las grandes cadenas hacen una versión del anuncio por ciudad o club.** Por ejemplo, Basic-Fit tiene el mismo texto con "…en Barcelona", "…en Madrid", etc. Apunta una fila por creatividad distinta y en "Notas" indica en cuántas ciudades se repite. Que una marca localice sus anuncios ya es una conclusión.
- La etiqueta "Este anuncio tiene varias versiones" indica que la marca está haciendo tests A/B. Anótalo en "Notas".
- Busca siempre eligiendo la **página** de la marca en el desplegable. La búsqueda por palabra clave mezcla anuncios de otras páginas que solo mencionan el nombre.
- Guarda capturas de los 3–4 anuncios más interesantes: sirven para el informe y para LinkedIn.

## 3. Leer el resumen (15 min)

La pestaña **Resumen** te da por marca: activos, nuevos, el más longevo, el % de anuncios con personas y el ángulo principal. Busca:
- **Quién está acelerando:** muchos anuncios nuevos.
- **Qué funciona:** los anuncios con más días activos. Si una marca mantiene un anuncio más de 30 días, probablemente le da resultados.
- **Patrones del sector:** ¿todos usan precio? ¿alguien se diferencia?

## 4. Escribir el informe (45 min)

Copia `web/informe-ejemplo.html` como `web/informe-gimnasios-1.html` y sustituye:
- **Titular:** la conclusión más interesante en una frase ("Los gimnasios dejan de anunciar precio").
- **Subtítulo:** el dato que la respalda.
- **KPIs y tabla:** salen directamente de la pestaña Resumen.
- **"Qué ha cambiado":** 3 observaciones. En el primer informe no hay semana anterior con la que comparar, así que cuenta patrones ("4 de 5 marcas anuncian precio").
- **Marca a marca:** oferta, anuncio más longevo, dónde anuncia y una conclusión.
- Quita la etiqueta "Datos de ejemplo".

Regla: **cada frase tiene que poder comprobarse en la hoja.** Nada inventado ni exagerado: el informe es tu carta de presentación.

## 5. Actualizar la landing (15 min)

En `web/index.html`, cambia los nombres y números del dashboard y de las tarjetas por los reales, y el enlace "Ver ejemplo" por el nuevo informe.

---

Cuando tengas el informe, sigue con la fase 1 de `HOJA_DE_RUTA.md`: conectar el formulario a Brevo y publicar la web.
