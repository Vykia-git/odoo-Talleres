# Copyright 2026 Vykia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMove(models.Model):
    """Enlace de trazabilidad factura <-> orden de taller.

    Herencia clasica (_inherit sin _name): añade un campo al modelo core sin
    tocar su codigo ni crear un modelo nuevo.
    """

    _inherit = "account.move"

    workshop_order_id = fields.Many2one(
        comodel_name="workshop.order",
        string="Orden de taller",
        copy=False,
        index="btree_not_null",
        ondelete="set null",
    )
    workshop_license_plate = fields.Char(
        related="workshop_order_id.license_plate",
        string="Matrícula",
        store=True,
    )
