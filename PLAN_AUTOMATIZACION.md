# Plan técnico: automatización del informe (fase 3 de la hoja de ruta)

**Objetivo:** cada semana, extraer automáticamente los anuncios activos de 5–8 marcas de un sector en España, analizarlos con IA y generar un informe. Coste: 0 €.

---

## 1. Arquitectura

```
[Programador semanal (lunes 8:00)]
        │
        ▼
[Lista de marcas]  ← Google Sheets, pestaña "Marcas" (nombre, page_id)
        │  (por cada marca)
        ▼
[API de la Biblioteca de anuncios de Meta]  → anuncios activos en ES
        │
        ├──► [Google Sheets, pestaña "Anuncios"]  (1 fila por anuncio, histórico)
        │
        ▼
[IA (Gemini u OpenAI)]  → análisis por marca: ángulos, ofertas, formatos, insight
        │
        ├──► [Google Sheets, pestaña "Análisis semanal"]
        ▼
[Email / Notion]  → informe semanal resumido
```

## 2. Stack

| Pieza | Herramienta | Por qué |
|---|---|---|
| Orquestación | **Make** (plan gratuito: 1.000 créditos/mes, 2 escenarios activos) | La herramienta de automatización que más piden las ofertas de marketing; no requiere instalar nada |
| Datos | API de la Biblioteca de anuncios de Meta (`ads_archive`) | Pública, gratuita, cubre todos los anuncios servidos en la UE (DSA) |
| Almacenamiento | Google Sheets | Gratis, y luego se conecta a Looker Studio |
| IA | Gemini API (tiene nivel gratuito; comprueba límites actuales) u OpenAI (~5 € de saldo duran meses) | Análisis cualitativo de los copies |
| Informe | Gmail (módulo de Make) o Notion | |
| Prototipo | Script de Python (`probar_api.py`) | Para ver los datos reales antes de montar Make |

**Presupuesto de créditos en Make:** si cada marca va en una sola llamada (hasta 50 anuncios) y una sola llamada a IA, salen unos 6 créditos por marca y semana → 6 marcas × 4 semanas ≈ 150 créditos/mes. Sobra margen.

---

## 3. Pasos

### Paso 1 — Acceso a la API de Meta *(lo haces tú; 1–3 días de espera)*
1. Entra en https://www.facebook.com/ads/library/api y pulsa *Comenzar*.
2. **Confirma tu identidad** (pide un documento de identidad; Meta tarda de horas a un par de días). Es obligatorio para usar la API.
3. Crea una cuenta de desarrollador en https://developers.facebook.com y una **app** (tipo "Otro" / "Empresa").
4. Ve al **Explorador de la API Graph** (https://developers.facebook.com/tools/explorer), elige tu app y genera un **token de acceso de usuario**.
5. Ese token dura ~1–2 horas. Para el prototipo vale; para Make, conviértelo en uno de larga duración (~60 días) con el *Depurador de tokens* → *Ampliar token de acceso*. Apunta en el calendario renovarlo.

> ⚠️ El token es una credencial: no lo pegues en documentos públicos ni lo subas a GitHub.

### Paso 2 — Elegir sector y marcas *(30 min)*
- Elige un sector con mucha actividad en Meta Ads en España y marcas comparables. Ideas: café de especialidad, gimnasios low cost, cosmética DTC, comida a domicilio, academias de idiomas, moda sostenible.
- Para cada marca, búscala en https://www.facebook.com/ads/library (país: España). En la URL de su página de anuncios aparece `view_all_page_id=XXXXXXXX`: ese número es su **page_id**.
- Apúntalas en la pestaña "Marcas" de la hoja.

### Paso 3 — Probar la API con el script *(30 min)*
```powershell
$env:META_TOKEN = "pega_aqui_tu_token"
python probar_api.py 123456789 987654321
```
Genera `anuncios.csv` con lo que devuelve la API. Así ves qué campos vienen rellenos y validas las marcas antes de tocar Make.

### Paso 4 — Montar la hoja de Google *(30 min)*

**Pestaña "Marcas"**
| marca | page_id | activa (sí/no) |

**Pestaña "Anuncios"** (histórico, 1 fila por anuncio)
| fecha_extraccion | marca | ad_id | fecha_inicio | fecha_fin | dias_activo | plataformas | texto | titulo | descripcion | alcance_ue | edades | genero | url_snapshot |

**Pestaña "Análisis semanal"**
| semana | marca | n_anuncios_activos | n_anuncios_nuevos | angulos | ofertas | formatos_y_cta | anuncio_mas_longevo | insight |

### Paso 5 — Escenario en Make *(2–4 h)*
1. **Disparador:** *Schedule* → semanal, lunes 8:00.
2. **Google Sheets → Search Rows** en "Marcas" (filtro `activa = sí`).
3. **HTTP → Make a request** (por cada marca):
   - `GET https://graph.facebook.com/<versión>/ads_archive`
   - Parámetros: ver la sección 4.
4. **Iterator** sobre `data[]` → **Google Sheets → Add a Row** en "Anuncios".
   *(Si quieres ahorrar créditos, usa un Array aggregator + "Bulk Add Rows".)*
5. **Text aggregator:** junta los textos de los anuncios de la marca en un único bloque.
6. **Módulo de IA** (Gemini / OpenAI) con el prompt de la sección 5 → devuelve JSON.
7. **JSON → Parse JSON** → **Google Sheets → Add a Row** en "Análisis semanal".
8. Fuera del bucle: **Gmail → Send an email** con el resumen de todas las marcas.

### Paso 6 — Validar y documentar *(continuo)*
- Lanzarlo 3–4 semanas seguidas para tener histórico (anuncios nuevos, anuncios que se apagan, cuánto duran).
- Hacer capturas del escenario, de la hoja y de los informes: serán el material del caso de estudio.
- Cada semana, un post en LinkedIn con lo más interesante del informe.

---

## 4. Llamada a la API

```
GET https://graph.facebook.com/<versión>/ads_archive
  ?access_token=<TOKEN>
  &search_page_ids=[<page_id>]
  &ad_reached_countries=["ES"]
  &ad_type=ALL
  &ad_active_status=ACTIVE
  &limit=50
  &fields=id,page_name,ad_creation_time,ad_delivery_start_time,ad_delivery_stop_time,
          ad_creative_bodies,ad_creative_link_titles,ad_creative_link_descriptions,
          ad_creative_link_captions,publisher_platforms,languages,
          eu_total_reach,target_ages,target_gender,target_locations,ad_snapshot_url
```
- `<versión>`: usa la versión actual de la API Graph que te indique el Explorador (por ejemplo `v23.0`).
- Si una marca tiene más de 50 anuncios, la respuesta trae `paging.next` para pedir la siguiente página.
- La API **no devuelve la imagen o el vídeo** directamente; `ad_snapshot_url` es el enlace para verlo.

## 5. Prompt de análisis (primera versión)

```
Eres analista de paid media. Te paso los anuncios activos esta semana en Meta
de la marca {{marca}} en España, con su fecha de inicio y plataformas.

Analízalos y responde SOLO con un JSON con esta estructura:
{
  "angulos": ["ángulo creativo principal 1", "..."],      // p. ej. precio, estatus, comunidad, urgencia
  "ofertas": ["oferta o promoción detectada", "..."],
  "formatos_y_cta": "resumen de llamadas a la acción y tono",
  "anuncio_mas_longevo": "id y por qué crees que sigue activo",
  "insight": "una frase con lo más relevante para un competidor"
}

Anuncios:
{{texto_agregado}}
```
Lo iremos afinando cuando veamos datos reales.

---

## 6. Entregables de la fase 1
- [ ] Acceso a la API conseguido
- [ ] Sector y 5–8 marcas con page_id
- [ ] Datos probados con el script
- [ ] Hoja de Google con las tres pestañas
- [ ] Escenario de Make funcionando semanalmente
- [ ] 3–4 informes semanales generados
- [ ] Capturas y notas para el caso de estudio
