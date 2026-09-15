# Copyright 2026 Vykia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class WorkshopOrderLine(models.Model):
    """Concepto facturable de una orden de trabajo.

    El producto es OPCIONAL y solo sirve para autocompletar precio e
    impuestos: no se generan movimientos de stock (decision de alcance).
    """

    _name = "workshop.order.line"
    _description = "Workshop Work Order Line"
    _order = "order_id, sequence, id"

    order_id = fields.Many2one(
        comodel_name="workshop.order",
        string="Orden",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        related="order_id.company_id", string="Compañía", store=True
    )
    currency_id = fields.Many2one(related="order_id.currency_id", string="Moneda")

    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Artículo / servicio",
        # Deja fuera los productos tecnicos no vendibles (p. ej. los
        # "DUA Valoracion IVA" que instala l10n_es para importaciones).
        domain=[("sale_ok", "=", True)],
        help="Opcional. Solo autocompleta descripción, precio e impuestos.",
    )
    name = fields.Char(string="Descripción", required=True)
    quantity = fields.Float(
        string="Cantidad", default=1.0, digits="Product Unit"
    )
    price_unit = fields.Float(string="Precio unitario", digits="Product Price")
    tax_ids = fields.Many2many(
        comodel_name="account.tax",
        string="Impuestos",
        domain="[('type_tax_use', '=', 'sale'), ('company_id', '=', company_id)]",
    )
    price_subtotal = fields.Monetary(
        string="Subtotal", compute="_compute_amounts", store=True
    )
    price_tax = fields.Monetary(
        string="Importe impuestos", compute="_compute_amounts", store=True
    )
    price_total = fields.Monetary(
        string="Total", compute="_compute_amounts", store=True
    )

    @api.depends("quantity", "price_unit", "tax_ids", "product_id")
    def _compute_amounts(self):
        """Delega el calculo en account.tax.compute_all.

        Nunca se calcula el IVA a mano: compute_all resuelve impuestos
        incluidos, en cascada y redondeos segun la configuracion fiscal.
        """
        for line in self:
            taxes = line.tax_ids.compute_all(
                price_unit=line.price_unit,
                currency=line.currency_id,
                quantity=line.quantity,
                product=line.product_id,
                partner=line.order_id.partner_id,
            )
            line.price_subtotal = taxes["total_excluded"]
            line.price_total = taxes["total_included"]
            line.price_tax = taxes["total_included"] - taxes["total_excluded"]

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Autocompleta descripcion, precio e impuestos desde el producto."""
        for line in self:
            if not line.product_id:
                continue
            product = line.product_id.with_company(line.company_id)
            # No se usa get_product_multiline_description_sale(): lo define el
            # modulo `sale`, que no esta en las dependencias de este modulo.
            line.name = product.description_sale or product.display_name
            line.price_unit = product.lst_price
            line.tax_ids = product.taxes_id.filtered(
                lambda t: t.company_id == line.company_id
            )

    @api.model
    def _default_sale_taxes(self, company):
        """Impuesto de venta por defecto de la compañía (fallback)."""
        return company.account_sale_tax_id

    @api.model_create_multi
    def create(self, vals_list):
        """Aplica el IVA por defecto cuando la linea se teclea a mano.

        Sin esto, una linea creada sin producto saldria sin impuestos y la
        factura se emitiria con IVA 0.
        """
        lines = super().create(vals_list)
        for line, vals in zip(lines, vals_list, strict=True):
            if "tax_ids" in vals or line.tax_ids or line.product_id:
                continue
            line.tax_ids = self._default_sale_taxes(line.company_id)
        return lines
