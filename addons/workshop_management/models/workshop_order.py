# Copyright 2026 Vykia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import plaintext2html

NEW_PLACEHOLDER = "/"


class WorkshopOrder(models.Model):
    """Orden de trabajo del taller.

    No se hereda ``repair.order`` (core): desde Odoo 17 exige un product_id
    almacenable propio y genera stock.move, lo que no aplica a un vehiculo
    propiedad del cliente.
    """

    _name = "workshop.order"
    _description = "Workshop Work Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_in desc, id desc"

    name = fields.Char(
        string="Nº de orden",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=NEW_PLACEHOLDER,
    )
    state = fields.Selection(
        selection=[
            ("open", "En el taller"),
            ("done", "Salido"),
            ("cancel", "Anulada"),
        ],
        string="Estado",
        default="open",
        required=True,
        tracking=True,
        copy=False,
    )

    # --- Vehiculo -------------------------------------------------------
    license_plate = fields.Char(
        string="Matrícula", required=True, tracking=True, index=True
    )
    vehicle_id = fields.Many2one(
        comodel_name="workshop.vehicle",
        string="Vehículo",
        readonly=True,
        copy=False,
        help="Se enlaza o se crea automáticamente a partir de la matrícula.",
    )
    vehicle_brand = fields.Char(
        related="vehicle_id.brand", string="Marca", readonly=False
    )
    vehicle_model = fields.Char(
        related="vehicle_id.model", string="Modelo", readonly=False
    )
    vehicle_model_year = fields.Char(
        related="vehicle_id.model_year", string="Año", readonly=False
    )
    vehicle_engine = fields.Char(
        related="vehicle_id.engine", string="Motor", readonly=False
    )
    vehicle_order_count = fields.Integer(
        related="vehicle_id.order_count", string="Visitas anteriores"
    )
    km = fields.Integer(string="Kilómetros")

    # --- Cliente --------------------------------------------------------
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Dueño / quien trae el coche",
        required=True,
        tracking=True,
        index=True,
    )
    phone = fields.Char(
        related="partner_id.phone", string="Teléfono", store=True, readonly=False
    )
    dni = fields.Char(
        related="partner_id.vat",
        string="DNI / NIF",
        store=True,
        readonly=False,
        help="Se guarda en la ficha del cliente y se imprime en la factura.",
    )

    # --- Trabajo --------------------------------------------------------
    work_description = fields.Text(string="Trabajos a realizar", tracking=True)
    date_in = fields.Datetime(
        string="Fecha de entrada",
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    date_out = fields.Datetime(
        string="Fecha de salida", readonly=True, copy=False, tracking=True
    )
    line_ids = fields.One2many(
        comodel_name="workshop.order.line",
        inverse_name="order_id",
        string="Conceptos a facturar",
        copy=True,
    )

    # --- Facturacion ----------------------------------------------------
    invoice_ids = fields.One2many(
        comodel_name="account.move",
        inverse_name="workshop_order_id",
        string="Facturas",
        readonly=True,
        copy=False,
    )
    invoice_count = fields.Integer(
        string="Nº facturas", compute="_compute_invoice_count"
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related="company_id.currency_id", string="Moneda")
    amount_untaxed = fields.Monetary(
        string="Base imponible", compute="_compute_amounts", store=True
    )
    amount_tax = fields.Monetary(
        string="Impuestos", compute="_compute_amounts", store=True
    )
    amount_total = fields.Monetary(
        string="Total", compute="_compute_amounts", store=True
    )

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends("line_ids.price_subtotal", "line_ids.price_tax")
    def _compute_amounts(self):
        for order in self:
            order.amount_untaxed = sum(order.line_ids.mapped("price_subtotal"))
            order.amount_tax = sum(order.line_ids.mapped("price_tax"))
            order.amount_total = order.amount_untaxed + order.amount_tax

    @api.depends("invoice_ids")
    def _compute_invoice_count(self):
        for order in self:
            order.invoice_count = len(order.invoice_ids)

    @api.depends("name", "license_plate")
    def _compute_display_name(self):
        for order in self:
            order.display_name = f"{order.name} - {order.license_plate or ''}".strip(
                " -"
            )

    # ------------------------------------------------------------------
    # ORM
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", NEW_PLACEHOLDER) == NEW_PLACEHOLDER:
                company_id = vals.get("company_id") or self.env.company.id
                vals["name"] = (
                    self.env["ir.sequence"]
                    .with_company(company_id)
                    .next_by_code("workshop.order")
                    or NEW_PLACEHOLDER
                )
        orders = super().create(vals_list)
        orders._sync_vehicle()
        return orders

    def write(self, vals):
        res = super().write(vals)
        if vals.get("license_plate"):
            self._sync_vehicle()
        return res

    def _sync_vehicle(self):
        """Enlaza (o crea) el vehiculo a partir de la matricula tecleada."""
        vehicle_model = self.env["workshop.vehicle"]
        for order in self:
            vehicle = vehicle_model.with_company(order.company_id)._search_or_create(
                order.license_plate, order.partner_id
            )
            if not vehicle:
                continue
            if order.vehicle_id != vehicle:
                order.vehicle_id = vehicle
            # Normaliza la matricula mostrada en la orden (sin guiones/espacios)
            if order.license_plate != vehicle.license_plate:
                order.license_plate = vehicle.license_plate

    # ------------------------------------------------------------------
    # Acciones de estado
    # ------------------------------------------------------------------
    def action_close(self):
        """Marca el coche como salido del taller."""
        for order in self:
            if order.state != "open":
                raise UserError(f"La orden {order.name} no está abierta.")
        return self.write({"state": "done", "date_out": fields.Datetime.now()})

    def action_reopen(self):
        return self.write({"state": "open", "date_out": False})

    def action_cancel(self):
        for order in self:
            if order.invoice_ids.filtered(lambda m: m.state != "cancel"):
                raise UserError(
                    f"No se puede anular la orden {order.name}: "
                    "tiene facturas asociadas."
                )
        return self.write({"state": "cancel"})

    # ------------------------------------------------------------------
    # Facturacion
    # ------------------------------------------------------------------
    def _prepare_invoice_line_vals(self, line):
        return {
            "product_id": line.product_id.id or False,
            "name": line.name,
            "quantity": line.quantity,
            "price_unit": line.price_unit,
            "tax_ids": [fields.Command.set(line.tax_ids.ids)],
        }

    def _prepare_invoice_vals(self):
        self.ensure_one()
        return {
            "move_type": "out_invoice",
            "partner_id": self.partner_id.id,
            "invoice_origin": self.name,
            "workshop_order_id": self.id,
            "company_id": self.company_id.id,
            # account.move.narration es un campo Html: hay que convertir el
            # texto plano o se perderian los saltos de linea.
            "narration": (
                plaintext2html(self.work_description)
                if self.work_description
                else False
            ),
            "invoice_line_ids": [
                fields.Command.create(self._prepare_invoice_line_vals(line))
                for line in self.line_ids
            ],
        }

    def action_create_invoice(self):
        """Genera la factura de cliente y la abre para revisar/enviar.

        El contexto ``default_move_type`` es imprescindible: es lo que hace
        que ``account`` resuelva el diario de ventas y la secuencia fiscal
        correctos durante el ``create()``, sin depender de onchanges.
        """
        self.ensure_one()
        if not self.line_ids:
            raise UserError(
                "Añade al menos un concepto en la pestaña «Conceptos a "
                "facturar» antes de generar la factura."
            )
        if self.invoice_ids.filtered(lambda m: m.state != "cancel"):
            raise UserError(f"La orden {self.name} ya tiene una factura.")
        invoice = (
            self.env["account.move"]
            .with_company(self.company_id)
            .with_context(default_move_type="out_invoice")
            .create(self._prepare_invoice_vals())
        )
        self.message_post(body=f"Factura generada: {invoice.name or 'borrador'}")
        return self.action_view_invoices()

    def action_view_invoices(self):
        self.ensure_one()
        action = {
            "type": "ir.actions.act_window",
            "name": "Facturas",
            "res_model": "account.move",
            "context": {
                "default_move_type": "out_invoice",
                "default_workshop_order_id": self.id,
            },
        }
        if len(self.invoice_ids) == 1:
            action.update({"view_mode": "form", "res_id": self.invoice_ids.id})
        else:
            action.update(
                {
                    "view_mode": "list,form",
                    "domain": [("workshop_order_id", "=", self.id)],
                }
            )
        return action

    def action_print(self):
        self.ensure_one()
        return self.env.ref(
            "workshop_management.action_report_workshop_order"
        ).report_action(self)
