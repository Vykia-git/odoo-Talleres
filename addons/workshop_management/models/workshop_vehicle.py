# Copyright 2026 Vykia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class WorkshopVehicle(models.Model):
    """Registro ligero de vehículos de cliente.

    Deliberadamente NO se reutiliza ``fleet.vehicle`` (modela la flota propia
    de la empresa: contratos, seguros, costes recurrentes). Aquí solo se
    necesita historial por matrícula, creado de forma transparente al
    registrar un ingreso.
    """

    _name = "workshop.vehicle"
    _description = "Workshop Vehicle"
    _order = "license_plate"

    license_plate = fields.Char(
        string="Matrícula", required=True, index=True
    )
    brand = fields.Char(string="Marca")
    model = fields.Char(string="Modelo")
    model_year = fields.Char(
        string="Año de fabricación",
        size=4,
        help="Junto con el motor, es lo que identifica el despiece "
        "correcto al buscar información técnica o repuestos.",
    )
    engine = fields.Char(
        string="Tipo de motor",
        help="Código o denominación del motor: 1.9 TDI AXR, 1.6 HDi 9HZ, "
        "1.4 TSI CAXA... Texto libre a propósito: el código exacto es lo "
        "que sirve para buscar.",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Último cliente",
        help="Último cliente que trajo el vehículo. Informativo.",
    )
    note = fields.Text(string="Observaciones del vehículo")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )
    order_ids = fields.One2many(
        comodel_name="workshop.order",
        inverse_name="vehicle_id",
        string="Órdenes",
    )
    order_count = fields.Integer(
        string="Nº de visitas", compute="_compute_order_count"
    )

    # API Odoo 19: models.Constraint sustituye a la lista _sql_constraints
    _license_plate_company_uniq = models.Constraint(
        "unique(license_plate, company_id)",
        "Ya existe un vehículo con esta matrícula.",
    )

    @api.constrains("model_year")
    def _check_model_year(self):
        """Un año mal tecleado hace perder el tiempo al mecánico."""
        limit = fields.Date.context_today(self).year + 1
        for vehicle in self:
            year = (vehicle.model_year or "").strip()
            if not year:
                continue
            if not year.isdigit() or not 1900 <= int(year) <= limit:
                raise ValidationError(
                    f"Año de fabricación no válido: {year}. "
                    f"Escribe el año con 4 cifras (entre 1900 y {limit})."
                )

    @api.depends("order_ids")
    def _compute_order_count(self):
        data = self.env["workshop.order"]._read_group(
            [("vehicle_id", "in", self.ids)], groupby=["vehicle_id"], aggregates=["__count"]
        )
        mapped = {vehicle.id: count for vehicle, count in data}
        for record in self:
            record.order_count = mapped.get(record.id, 0)

    @api.depends("license_plate", "brand", "model")
    def _compute_display_name(self):
        for record in self:
            parts = [record.license_plate or ""]
            descr = " ".join(filter(None, [record.brand, record.model]))
            if descr:
                parts.append(f"({descr})")
            record.display_name = " ".join(parts)

    @api.model
    def _normalize_plate(self, plate):
        """Normaliza la matrícula para poder buscarla de forma fiable."""
        return (plate or "").upper().replace(" ", "").replace("-", "").strip()

    @api.model
    def _search_or_create(self, plate, partner=None):
        """Devuelve el vehículo de esa matrícula, creándolo si no existe.

        Punto de integración clave: permite registrar un ingreso escribiendo
        solo la matrícula, sin obligar al usuario a buscar en un maestro.
        """
        normalized = self._normalize_plate(plate)
        if not normalized:
            return self.browse()
        vehicle = self.search(
            [
                ("license_plate", "=", normalized),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        if not vehicle:
            vehicle = self.create(
                {"license_plate": normalized, "partner_id": partner.id if partner else False}
            )
        elif partner and vehicle.partner_id != partner:
            vehicle.partner_id = partner
        return vehicle

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("license_plate"):
                vals["license_plate"] = self._normalize_plate(vals["license_plate"])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("license_plate"):
            vals["license_plate"] = self._normalize_plate(vals["license_plate"])
        return super().write(vals)

    def action_view_orders(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Órdenes del vehículo",
            "res_model": "workshop.order",
            "view_mode": "list,form",
            "domain": [("vehicle_id", "=", self.id)],
            "context": {"default_vehicle_id": self.id, "default_license_plate": self.license_plate},
        }
