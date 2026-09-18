# Copyright 2026 Vykia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Parche local de un bug de Odoo 19 core (`addons/website`).

`website.get_current_website()` (website/models/website.py:1402) resuelve el
dominio así:

    domain_name = (
        request and request.httprequest.host                    # "host:puerto"
        or hasattr(threading.current_thread(), 'url')
        and threading.current_thread().url                      # URL COMPLETA
        or '')

El segundo término no es un netloc: es la URL entera que `http.py` deja en el
hilo. Ese valor llega sin tocar a `_get_current_website_id()`, que hace
`domain_name.encode("idna")` (línea 1450). El códec `idna` exige etiquetas
-- los trozos entre puntos -- de 63 caracteres como máximo, así que una URL
cuyo host no tenga puntos forma una sola etiqueta larguísima y revienta:

    http://localhost:8069/web/dataset/call_kw/website/configurator_apply
    -> 68 caracteres, 1 etiqueta -> UnicodeError: label too long

Se dispara siempre que `get_current_website()` corre sin `request` enlazado;
en la práctica, durante la recarga de registry que provoca instalar o
actualizar un tema (`ir.module.module.button_choose_theme`). Resultado: el
configurador de sitio web es inusable en cualquier despliegue servido desde un
host sin puntos (`localhost`, `odoo`, `web`...).

Se parchea la clase en tiempo de importación en lugar de heredar con
`_inherit` a propósito: el fallo ocurre mientras se reconstruye el registry, y
ahí no hay garantía de que este módulo se procese antes que el tema (el grafo
ordena por profundidad y luego por nombre, y `theme_kea` < `website_...`). Un
monkey patch en el import sí está activo, porque los módulos Python ya se
importaron al arrancar el servidor y no se reimportan en cada recarga.

Retirar cuando Odoo lo corrija upstream.
"""

import logging
from urllib.parse import urlsplit

from odoo import api
from odoo.addons.website.models.website import Website

_logger = logging.getLogger(__name__)

# RFC 1035: longitud máxima de una etiqueta DNS, que es lo que valida el códec.
MAX_IDNA_LABEL_LENGTH = 63


def _sanitize_domain_name(domain_name):
    """Devuelve un `host[:puerto]` que `str.encode('idna')` pueda digerir."""
    if not domain_name:
        return ""
    if "://" in domain_name:
        domain_name = urlsplit(domain_name).netloc
    # Una URL sin esquema ("localhost:8069/web/...") no la parte urlsplit.
    domain_name = domain_name.split("/", 1)[0]
    if any(len(label) > MAX_IDNA_LABEL_LENGTH for label in domain_name.split(".")):
        _logger.warning(
            "Dominio no codificable en idna (%r); se resuelve el website por fallback.",
            domain_name,
        )
        return ""
    return domain_name


_origin = Website._get_current_website_id


@api.model
def _get_current_website_id(self, domain_name, fallback=True):
    # `_origin` conserva el @tools.ormcache del core, así que la caché sigue
    # viva y además pasa a estar indexada por el dominio ya saneado.
    return _origin(self, _sanitize_domain_name(domain_name), fallback=fallback)


_get_current_website_id._vykia_idna_patch = True

if not getattr(_origin, "_vykia_idna_patch", False):
    Website._get_current_website_id = _get_current_website_id
