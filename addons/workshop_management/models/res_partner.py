# Copyright 2026 Vykia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    workshop_order_ids = fields.One2many(
        comodel_name="workshop.order",
        inverse_name="partner_id",
        string="Órdenes de taller",
    )
    workshop_order_count = fields.Integer(
        string="Nº de órdenes", compute="_compute_workshop_order_count"
    )

    @api.depends("workshop_order_ids")
    def _compute_workshop_order_count(self):
        data = self.env["workshop.order"]._read_group(
            [("partner_id", "in", self.ids)],
            groupby=["partner_id"],
            aggregates=["__count"],
        )
        mapped = {partner.id: count for partner, count in data}
        for partner in self:
            partner.workshop_order_count = mapped.get(partner.id, 0)

    def action_view_workshop_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Órdenes de taller",
            "res_model": "workshop.order",
            "view_mode": "list,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {"default_partner_id": self.id},
        }
