# Copyright 2026 Vykia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Workshop Management",
    "summary": "Gestión de taller: ingresos de vehículos, órdenes de trabajo y facturación",
    "version": "19.0.1.0.0",
    "category": "Services/Workshop",
    "license": "AGPL-3",
    "author": "Vykia",
    "website": "https://github.com/Vykia-git/odoo",
    "depends": [
        # core: ORM, chatter, secuencias, informes QWeb
        "base",
        "mail",
        # core: account.move (factura), impuestos y envío por email de la factura
        "account",
    ],
    "data": [
        "security/workshop_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/product_data.xml",
        "report/workshop_order_report.xml",
        "report/report_workshop_order.xml",
        "views/workshop_vehicle_views.xml",
        "views/workshop_order_views.xml",
        "views/account_move_views.xml",
        "views/res_partner_views.xml",
        "views/workshop_menus.xml",
    ],
    "installable": True,
    "application": True,
}
