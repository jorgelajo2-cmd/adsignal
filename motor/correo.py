"""
EMAIL y CRM con Brevo.

- enviar():   manda el email con el enlace al informe (API transaccional de Brevo).
- contacto(): crea o actualiza el contacto en Brevo con su sector, país y campaña de origen.

Variables:
  BREVO_API_KEY     clave de API de Brevo (SMTP & API → API keys)
  REMITENTE_EMAIL   email verificado en Brevo desde el que se envía
  REMITENTE_NOMBRE  opcional, por defecto "adsignal"
  BREVO_LISTA_ID    opcional, número de la lista donde guardar los contactos

CorreoPrueba hace lo mismo pero guarda cada email como .html en una carpeta (no envía nada).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_env = Environment(loader=FileSystemLoader(Path(__file__).parent / "plantillas"), autoescape=select_autoescape(["html"]))
API = "https://api.brevo.com/v3"


def componer(sol, met: dict, an: dict, url: str, ejemplo: bool) -> tuple[str, str]:
    asunto = f"Tu informe de anuncios: {sol.industria} en {sol.nombre_pais}"
    html = _env.get_template("email.html").render(sol=sol, met=met, an=an, url=url, ejemplo=ejemplo)
    return asunto, html


class CorreoBrevo:
    def __init__(self):
        self.clave = os.environ.get("BREVO_API_KEY")
        self.remitente = os.environ.get("REMITENTE_EMAIL")
        if not self.clave or not self.remitente:
            raise RuntimeError("Faltan BREVO_API_KEY o REMITENTE_EMAIL.")
        self.nombre = os.environ.get("REMITENTE_NOMBRE", "adsignal")
        self.lista = os.environ.get("BREVO_LISTA_ID")

    def _post(self, ruta: str, cuerpo: dict) -> dict:
        req = urllib.request.Request(
            API + ruta, data=json.dumps(cuerpo).encode(), method="POST",
            headers={"api-key": self.clave, "content-type": "application/json", "accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                texto = r.read().decode() or "{}"
                return json.loads(texto)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Brevo {e.code}: {e.read().decode('utf-8', 'replace')[:300]}") from None

    def enviar(self, para: str, asunto: str, html: str):
        self._post("/smtp/email", {
            "sender": {"name": self.nombre, "email": self.remitente},
            "to": [{"email": para}],
            "subject": asunto,
            "htmlContent": html,
            "tags": ["informe"],
        })

    def contacto(self, email: str, atributos: dict):
        cuerpo = {"email": email, "attributes": atributos, "updateEnabled": True}
        if self.lista:
            cuerpo["listIds"] = [int(self.lista)]
        self._post("/contacts", cuerpo)


class CorreoPrueba:
    def __init__(self, carpeta: str | Path = "salida_emails"):
        self.carpeta = Path(carpeta)
        self.carpeta.mkdir(parents=True, exist_ok=True)

    def enviar(self, para: str, asunto: str, html: str):
        nombre = para.replace("@", "_at_").replace(".", "_")
        (self.carpeta / f"{nombre}.html").write_text(f"<!-- Para: {para} | Asunto: {asunto} -->\n{html}", encoding="utf-8")

    def contacto(self, email: str, atributos: dict):
        (self.carpeta / "contactos.jsonl").open("a", encoding="utf-8").write(json.dumps({"email": email, **atributos}, ensure_ascii=False) + "\n")
