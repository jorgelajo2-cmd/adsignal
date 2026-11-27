"""
PDF del informe: abre el HTML en un navegador real y lo "imprime" a PDF.

Así el PDF es idéntico a la web (mismas fuentes, colores y gráficos), pero en
modo impresión: sin animaciones, todo en su estado final y paginado en A4.

Usa el navegador que haya: Chrome (en GitHub Actions viene instalado), Edge
(en Windows) o, si no hay ninguno, descarga el Chromium de Playwright una vez.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _abrir_navegador(p):
    errores = []
    for canal in ("chrome", "msedge", None):
        try:
            return p.chromium.launch(channel=canal) if canal else p.chromium.launch()
        except Exception as e:  # ese navegador no está instalado
            errores.append(f"{canal or 'chromium'}: {type(e).__name__}")
    # Último recurso: instalar el Chromium de Playwright y reintentar
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        return p.chromium.launch()
    except Exception as e:
        raise RuntimeError(f"No hay navegador para generar el PDF ({'; '.join(errores)}; {type(e).__name__})") from None


def generar_pdf(html: Path, destino: Path | None = None) -> Path:
    from playwright.sync_api import sync_playwright

    html = Path(html).resolve()
    destino = Path(destino) if destino else html.with_suffix(".pdf")
    with sync_playwright() as p:
        nav = _abrir_navegador(p)
        try:
            pag = nav.new_page()
            pag.emulate_media(media="print", reduced_motion="reduce")
            pag.goto(html.as_uri(), wait_until="networkidle", timeout=60_000)
            pag.evaluate("document.fonts.ready")
            pag.pdf(path=str(destino), print_background=True, prefer_css_page_size=True)
        finally:
            nav.close()
    return destino
