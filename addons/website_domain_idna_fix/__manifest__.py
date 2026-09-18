# Copyright 2026 Vykia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Website Domain IDNA Fix",
    "summary": "Corrige el UnicodeError de website al resolver el dominio desde hosts sin puntos (localhost)",
    "version": "19.0.1.0.0",
    "category": "Website",
    "license": "AGPL-3",
    "author": "Vykia",
    "website": "https://github.com/Vykia-git/odoo",
    "depends": [
        # core: se parchea website._get_current_website_id
        "website",
    ],
    # Sin `data`: es un parche de comportamiento, no aporta modelos ni vistas.
    # Parche de entorno de desarrollo: el bug solo se dispara en hosts sin
    # puntos (localhost). Sin autoinstalacion a proposito, para que en un
    # despliegue con dominio real quede en addons/ pero inerte.
    "auto_install": False,
    "installable": True,
}
