# addons_third

Modulos de terceros que **no** son de la OCA, vendorizados igual que `addons_oca/`
(copia del codigo, no submodulo).

| Modulo | Origen | Licencia | Por que |
|---|---|---|---|
| `muk_web_colors` | [muk-it/odoo-modules](https://github.com/muk-it/odoo-modules/tree/19.0/muk_web_colors) rama `19.0` | LGPL-3 | Personalizar los colores del backend. OCA no tiene equivalente en 19.0: `web_company_color` no esta portado. |

Montado en el contenedor como `/mnt/third-addons`. Al anadir un modulo aqui hay que
tocar el `addons_path` en `config/odoo.conf` **y** en `config/odoo.conf.example`.
