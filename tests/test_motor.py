"""
Pruebas del motor con una API de Meta simulada. No usan red ni credenciales.

    python -m unittest discover -s tests
"""
import contextlib
import csv
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from motor import analisis, marcas, meta_api, metricas, procesar, relevancia, sectores
from motor.correo import CorreoPrueba
from motor.hoja import COLUMNAS, HojaCSV
from motor.meta_api import ErrorMeta, ErrorMetaGlobal, parecido
from motor.seguridad import FugaDeSecreto, comprobar_publicable, ocultar
from motor.solicitud import Solicitud

TOKEN = "EAAtokenDePrueba123456"
EMAIL = "persona@ejemplo.com"


def anuncio(pid, nombre, i, texto="Tu gimnasio desde 19 €"):
    return {
        "id": f"{pid}{i:04d}", "page_id": pid, "page_name": nombre,
        "ad_delivery_start_time": "2026-11-01", "ad_creative_bodies": [texto],
        "publisher_platforms": ["facebook"],
        # Así devuelve Meta el enlace: con el token dentro
        "ad_snapshot_url": f"https://www.facebook.com/ads/archive/render_ad/?id={pid}{i:04d}&access_token={TOKEN}",
    }


class MetaSimulada:
    """Sustituye a meta_api._pedir. Pagina de 2 en 2."""

    def __init__(self, paginas: dict):
        self.paginas = paginas  # page_id -> (nombre, número de anuncios)

    def __call__(self, url):
        from urllib.parse import parse_qs, urlparse
        q = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
        if "search_page_ids" in q:
            ids = json.loads(q["search_page_ids"])
        else:
            ids = list(self.paginas)
        todos = [anuncio(p, self.paginas[p][0], i) for p in ids if p in self.paginas for i in range(self.paginas[p][1])]
        desde = int(q.get("after", 0))
        datos = {"data": todos[desde:desde + 2]}
        if desde + 2 < len(todos):
            sin_after = url.split("&after=")[0]
            datos["paging"] = {"next": f"{sin_after}&after={desde + 2}"}
        return datos


class ConEntorno(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        entorno = mock.patch.dict(os.environ, {"META_TOKEN": TOKEN}, clear=False)
        entorno.start()
        self.addCleanup(entorno.stop)
        for nombre in ("ANTHROPIC_API_KEY", "GITHUB_OUTPUT"):
            os.environ.pop(nombre, None)
        sin_pdf = mock.patch("motor.pdf.generar_pdf", side_effect=RuntimeError("sin navegador en las pruebas"))
        sin_pdf.start()
        self.addCleanup(sin_pdf.stop)

    def meta(self, paginas):
        p = mock.patch.object(meta_api, "_pedir", MetaSimulada(paginas))
        p.start()
        self.addCleanup(p.stop)


class Seguridad(ConEntorno):
    def test_el_recolector_quita_el_token_de_los_enlaces(self):
        self.meta({"111111": ("Basic-Fit", 5)})
        anuncios, quedan = meta_api.anuncios_de_pagina("111111", "ES")
        self.assertEqual(len(anuncios), 5)
        self.assertFalse(quedan)
        self.assertNotIn(TOKEN, json.dumps(anuncios))
        self.assertEqual(anuncios[0]["ad_snapshot_url"], "https://www.facebook.com/ads/library/?id=1111110000")

    def test_no_se_publica_nada_con_el_token(self):
        for malo in ("https://x.com/?access_token=abc", f"texto {TOKEN}"):
            with self.assertRaises(FugaDeSecreto):
                comprobar_publicable(malo)
        comprobar_publicable("https://www.facebook.com/ads/library/?id=1")

    def test_ocultar_emails_y_claves(self):
        limpio = ocultar(f"Fallo con «{EMAIL}» en ?access_token=zzz&x=1 y {TOKEN}")
        for secreto in (EMAIL, "zzz", TOKEN):
            self.assertNotIn(secreto, limpio)


class Busqueda(ConEntorno):
    def test_parecido(self):
        self.assertEqual(parecido("Basic Fit", "Basic-Fit"), 2)
        self.assertEqual(parecido("basicfit", "Basic-Fit España"), 1)
        self.assertEqual(parecido("Línea Directa", "Linea Directa Aseguradora"), 1)
        self.assertEqual(parecido("Nike", "Nikesha Beauty"), 0)
        self.assertEqual(parecido("Zara", "Gimnasio Central"), 0)

    def test_no_adivina_una_marca_que_no_existe(self):
        self.meta({"222222": ("Gimnasio Central", 3)})
        self.assertIsNone(meta_api.resolver_marca("McFit", "ES"))

    def test_prefiere_el_nombre_exacto(self):
        self.meta({"1000001": ("Zara Home", 9), "1000002": ("ZARA", 2)})
        self.assertEqual(meta_api.resolver_marca("Zara", "ES"), ("1000002", "ZARA"))

    def test_acepta_numero_o_url_de_pagina(self):
        self.assertEqual(meta_api.id_de_pagina("123456789"), "123456789")
        self.assertEqual(meta_api.id_de_pagina("https://www.facebook.com/ads/library/?view_all_page_id=987654321"), "987654321")
        self.assertIsNone(meta_api.id_de_pagina("McFit"))

    def test_avisa_de_marcas_no_encontradas_y_de_recortes(self):
        self.meta({"111111": ("Basic-Fit", 7)})
        sol = Solicitud("gimnasios", "ES", ["Basic-Fit", "Inventada"])
        r = meta_api.recolectar(sol, max_por_marca=4, log=lambda m: None)
        self.assertEqual(len(r.anuncios), 4)
        self.assertTrue(any("Inventada" in a for a in r.avisos))
        self.assertTrue(any("más de 4" in a for a in r.avisos))

    def test_un_anuncio_hallado_por_dos_busquedas_cuenta_una_vez(self):
        self.meta({"111111": ("Basic-Fit", 3)})
        paginas, _, terminos, en_catalogo = meta_api.anunciantes_de_sector("gimnasio", "ES")
        self.assertEqual((len(terminos), en_catalogo), (2, True))
        self.assertEqual(paginas, [("111111", "Basic-Fit", 3)])

    def test_sector_fuera_del_catalogo_se_avisa(self):
        self.meta({"111111": ("Tienda", 2)})
        r = meta_api.recolectar(Solicitud("cometas artesanales"), log=lambda m: None)
        self.assertTrue(any("no está en nuestro catálogo" in a for a in r.avisos))

    def test_solo_espana(self):
        self.assertEqual(Solicitud("vino", "").nombre_pais, "España")
        with self.assertRaises(ValueError):
            Solicitud("vino", "FR")


class Catalogo(unittest.TestCase):
    def test_es_amplio_y_cada_sector_tiene_de_una_a_tres_busquedas(self):
        self.assertGreaterEqual(len(sectores.SECTORES), 150)
        self.assertEqual(len(sectores.SECTORES), sum(len(g) for g in sectores.CATALOGO.values()), "sector repetido")
        for nombre, terminos in sectores.SECTORES.items():
            self.assertTrue(1 <= len(terminos) <= 3, nombre)
            self.assertLessEqual(len(nombre), 60)

    def test_cada_nombre_lleva_a_su_propio_sector(self):
        for nombre in sectores.SECTORES:
            self.assertEqual(sectores.buscar_sector(nombre), nombre)

    def test_entiende_singular_plural_mayusculas_y_sinonimos(self):
        casos = {"gimnasio": "Gimnasios", "HOTEL": "Hoteles", "viaje": "Viajes", "dentista": "Clínicas dentales",
                 "seguro de coche": "Seguros de coche", "cosmetica": "Cosmética"}
        for escrito, sector in casos.items():
            self.assertEqual(sectores.buscar_sector(escrito), sector, escrito)
        self.assertEqual(sectores.terminos_de_busqueda("cometas artesanales"), (["cometas artesanales"], False))

    def test_la_lista_de_la_web_esta_al_dia(self):
        self.assertEqual(sectores.RUTA_WEB.read_text(encoding="utf-8").replace("\r\n", "\n"), sectores.contenido_web(),
                         "Ejecuta: python -m motor.sectores")


class Ruido(ConEntorno):
    """Casos tomados de búsquedas reales en España."""

    def ad(self, pagina, texto, i=0, **extra):
        return {"id": f"{pagina}{i}", "page_id": pagina, "page_name": pagina, "ad_creative_bodies": [texto]} | extra

    def elegidas(self, anuncios, sector):
        terminos, _ = sectores.terminos_de_busqueda(sector)
        return [n for _, n, _ in relevancia.ordenar_anunciantes(anuncios, sector, terminos)]

    def test_descarta_apps_de_series_y_tiendas_con_nombre_generado(self):
        historia = "El día de su boda, Adrian dejó a Elias. " * 8 + "Se conocieron en el gym."
        ads = [self.ad("Joyreels-playet-26", "Sabía que estaba mal. En el gimnasio..."),
               self.ad("Mitgcherm-store", "Recupera tu sonrisa sin pisar el gimnasio"),
               self.ad("Isaac Foster", historia),
               self.ad("Gymtone", "Un año en el gym y sigues igual")]
        self.assertEqual(self.elegidas(ads, "Gimnasios"), ["Gymtone"])

    def test_primero_quien_nombra_el_sector(self):
        ads = [self.ad("Ofertas Varias", "Jamón y vino tinto", i) for i in range(3)]
        ads.append(self.ad("Vinos de La Mancha", "El vino tinto tempranillo"))
        self.assertEqual(self.elegidas(ads, "Vino"), ["Vinos de La Mancha", "Ofertas Varias"])

    def test_una_pagina_que_solo_menciona_el_sector_de_pasada_no_entra(self):
        ads = [self.ad("Revista", "Noticias de hoy", i) for i in range(3)] + [self.ad("Revista", "Abre un gimnasio", 9)]
        self.assertEqual(self.elegidas(ads, "Gimnasios"), [])

    def test_pagina_oficial_de_una_marca_conocida(self):
        oficial = meta_api.es_pagina_oficial
        self.assertTrue(oficial("Altafit", "ALTAFIT GIMNASIOS", "Gimnasios"))
        self.assertTrue(oficial("Banco Santander", "Banco Santander España", "Bancos"))
        self.assertTrue(oficial("Línea Directa", "Línea Directa Aseguradora", "Seguros de coche"))
        self.assertFalse(oficial("Flex", "Flex Fitness Studio", "Colchones"))
        self.assertFalse(oficial("Mango", "Frutas Mango Tropical", "Moda"))
        # «Man» está dentro de «Mango», pero es otra página: si se quiere, va en la lista
        self.assertFalse(oficial("Mango", "MANGO Man", "Moda"))
        self.assertTrue(oficial("VivaGym", "vivagym.es", "Gimnasios"))

    def test_con_marcas_conocidas_no_se_busca_por_palabras(self):
        paginas = {f"10000{i}": (n, 2) for i, n in enumerate(("Basic-Fit", "Altafit", "VivaGym", "Joyreels-playet-1"))}
        self.meta(paginas)
        with mock.patch.object(meta_api, "anunciantes_de_sector") as buscar:
            r = meta_api.recolectar(Solicitud("gimnasios"), log=lambda m: None)
        buscar.assert_not_called()
        self.assertEqual({a["page_name"] for a in r.anuncios}, {"Basic-Fit", "Altafit", "VivaGym"})
        self.assertTrue(any("conocidos del sector" in a for a in r.avisos))

    def test_las_marcas_conocidas_son_de_sectores_que_existen(self):
        self.assertEqual(set(marcas.CONOCIDAS) - set(sectores.SECTORES), set())


class ErroresDeMeta(ConEntorno):
    def error(self, codigo, mensaje, estado=400):
        cuerpo = io.BytesIO(json.dumps({"error": {"code": codigo, "message": mensaje}}).encode())
        return urllib.error.HTTPError("https://graph.facebook.com", estado, "x", {}, cuerpo)

    def test_token_caducado_afecta_a_todas(self):
        with mock.patch("urllib.request.urlopen", side_effect=self.error(190, f"Token {TOKEN} expired")):
            with self.assertRaises(ErrorMetaGlobal) as c:
                meta_api._pedir("https://graph.facebook.com/x")
        self.assertNotIn(TOKEN, str(c.exception))

    def test_pide_menos_datos_si_meta_lo_exige(self):
        respuesta = io.BytesIO(b'{"data": []}')
        efectos = [self.error(1, "Please reduce the amount of data you're asking for", 500), contextlib.nullcontext(respuesta)]
        with mock.patch("urllib.request.urlopen", side_effect=efectos) as abrir:
            self.assertEqual(meta_api._pedir("https://graph.facebook.com/x?limit=100"), {"data": []})
        self.assertIn("limit=50", abrir.call_args_list[1].args[0])

    def test_un_error_inesperado_no_muestra_la_url(self):
        with mock.patch("urllib.request.urlopen", side_effect=ValueError(f"mala url ?access_token={TOKEN}")):
            with self.assertRaises(ErrorMeta) as c:
                meta_api._pedir("https://graph.facebook.com/x")
        self.assertNotIn(TOKEN, str(c.exception))


class Metricas(unittest.TestCase):
    def test_quita_huecos_de_catalogo(self):
        from datetime import date
        m = metricas.calcular([anuncio("1", "A", 1, "Compra {{product.name}} hoy")], date(2026, 11, 27))
        self.assertEqual(m["marcas"][0]["textos"][0]["texto"], "Compra hoy")


class Carrusel(unittest.TestCase):
    def test_el_texto_repetido_en_cada_tarjeta_cuenta_una_vez(self):
        from datetime import date
        ad = anuncio("1", "A", 1) | {"ad_creative_bodies": ["Nuevo gym en Utrera", "Nuevo gym en Utrera"]}
        m = metricas.calcular([ad], date(2026, 11, 27))
        self.assertEqual(m["marcas"][0]["textos"][0]["texto"], "Nuevo gym en Utrera")


class Precision(unittest.TestCase):
    def informe(self, ads):
        from datetime import date
        met = metricas.calcular(ads, date(2026, 11, 27))
        return analisis.analizar(Solicitud("Gimnasios", "ES"), met, usar_ia=False)

    def test_encuentra_ofertas_en_texto_y_titular_sin_duplicarlas(self):
        ad = anuncio("1", "A", 1, "Black Friday: empieza por solo 1 euro y llévate una mochila") | {
            "ad_creative_link_titles": ["Empieza por solo 1€*"]}
        ofertas = self.informe([ad])["marcas"]["1"]["ofertas"]
        self.assertEqual(sorted(ofertas), ["black friday", "llévate una mochila", "por solo 1 €"])

    def test_la_cuota_no_se_presenta_como_de_todo_el_sector(self):
        an = self.informe([anuncio("1", "A", 1), anuncio("1", "A", 2), anuncio("2", "B", 1)])
        self.assertIn("marcas analizadas", an["titular"])

    def test_no_dice_que_una_plataforma_manda_si_hay_empate(self):
        ad = anuncio("1", "A", 1) | {"publisher_platforms": ["facebook", "instagram"]}
        titulos = [t["titulo"] for t in self.informe([ad])["tendencias"]]
        self.assertIn("Empate: Facebook y Instagram", titulos)


class Flujo(ConEntorno):
    def cola(self, **campos):
        fila = dict.fromkeys(COLUMNAS, "") | {
            "id": "abc123def456", "email": EMAIL, "industria": "Gimnasios", "pais": "ES",
            "consentimiento": "si", "estado": "pendiente"} | campos
        ruta = self.tmp / "cola.csv"
        with ruta.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNAS)
            w.writeheader()
            w.writerow(fila)
        self.hoja = HojaCSV(ruta)
        self.correo = CorreoPrueba(self.tmp / "emails")
        self.carpeta = self.tmp / "informes"

    def fila(self):
        return self.hoja._leer()[0]

    def emails(self):
        return list((self.tmp / "emails").glob("*.html"))

    def generar(self):
        salida = io.StringIO()
        with contextlib.redirect_stdout(salida):
            problemas = procesar.generar(self.hoja, self.correo, "meta", self.carpeta, "https://web.test")
        return problemas, salida.getvalue()

    def enviar(self, publicado=True):
        with contextlib.redirect_stdout(io.StringIO()):
            return procesar.enviar(self.hoja, self.correo, self.carpeta, "https://web.test", lambda url: publicado)

    def test_primero_se_genera_y_solo_se_envia_cuando_esta_publicado(self):
        self.meta({"111111": ("Basic-Fit", 5), "222222": ("McFit", 3)})
        self.cola(marcas="Basic-Fit, McFit")
        problemas, registro = self.generar()
        self.assertEqual((problemas, self.fila()["estado"], self.emails()), (0, "generado", []))
        self.assertNotIn(EMAIL, registro)

        for archivo in self.carpeta.iterdir():
            contenido = archivo.read_text(encoding="utf-8")
            self.assertNotIn(TOKEN, contenido, archivo.name)
            self.assertNotIn(EMAIL, contenido, archivo.name)

        self.assertEqual(self.enviar(publicado=False), 1)
        self.assertEqual((self.fila()["estado"], self.emails()), ("generado", []))

        self.assertEqual(self.enviar(), 0)
        self.assertEqual(self.fila()["estado"], "enviado")
        self.assertIn(self.fila()["informe"], self.emails()[0].read_text(encoding="utf-8"))

    def test_si_falta_el_archivo_se_vuelve_a_generar(self):
        self.cola(estado="generado", informe="https://web.test/informes/no-existe.html")
        self.enviar()
        self.assertEqual(self.fila()["estado"], "pendiente")

    def test_token_caducado_deja_la_solicitud_pendiente(self):
        self.cola()
        with mock.patch.object(meta_api, "_pedir", side_effect=ErrorMetaGlobal("token caducado")):
            problemas, _ = self.generar()
        self.assertEqual((problemas, self.fila()["estado"], self.emails()), (1, "pendiente", []))

    def test_sin_anuncios_se_avisa_por_email(self):
        self.meta({})
        self.cola(marcas="Inventada")
        problemas, _ = self.generar()
        self.assertEqual((problemas, self.fila()["estado"]), (0, "sin_resultados"))
        self.assertIn("Inventada", self.emails()[0].read_text(encoding="utf-8"))

    def test_retoma_una_fila_a_medias(self):
        self.meta({"111111": ("Basic-Fit", 2)})
        self.cola(estado="procesando", marcas="Basic-Fit")
        self.generar()
        self.assertEqual(self.fila()["estado"], "generado")

    def test_email_no_valido_no_sale_en_el_registro(self):
        self.cola(email="mal@escrito")
        problemas, registro = self.generar()
        self.assertEqual((problemas, self.fila()["estado"]), (1, "error"))
        self.assertNotIn("mal@escrito", registro)


if __name__ == "__main__":
    unittest.main()
