import json
import re
from datetime import date, datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class Ultimopagofactura(models.Model):
    _inherit = "account.move"

    fecha_ultimo_pago_factura = fields.Date(
        string="Fecha último pago compute",
        compute="_last_payment_date",
        readonly=True,
        default=None,
    )

    fecha_ultimo_pago_factura_store = fields.Date(
        string="Fecha último pago",
        compute="_get_fecha_ultimo_pago_factura",
        readonly=True,
        store=True,
    )

    dias_pagar = fields.Integer(
        string="Días que tardaron en pagar compute",
        compute="get_dias_pagar",
        default=0,
    )

    dias_pagar_store = fields.Integer(
        string="Días que tardaron en pagar",
        compute="set_dias_pagar",
        default=0,
        store=True,
    )

    parcialidades = fields.Integer(
        string="Parcialidades compute",
        compute="_last_payment_date",
        readonly=True,
        default=0,
    )

    parcialidades_store = fields.Integer(
        string="Parcialidades",
        compute="_get_parcialidades",
        readonly=True,
        store=True,
    )

    monto_ultimo_pago = fields.Float(
        string="Monto del último pago compute",
        compute="_last_payment_date",
        readonly=True,
        default=0,
    )

    monto_ultimo_pago_store = fields.Float(
        string="Monto del último pago",
        compute="_get_monto_ultimo_pago",
        readonly=True,
        default=0,
    )

    @api.depends("invoice_payments_widget")
    def _last_payment_date(self):
        for record in self:
            if not record.invoice_payments_widget:
                record.fecha_ultimo_pago_factura = None
                record.parcialidades = 0
                continue
            dict = record.invoice_payments_widget
            if dict and dict.get("content"):
                content = dict.get("content")
                record.fecha_ultimo_pago_factura = date.fromisoformat(
                    max(payment.get("date") for payment in content)
                )
                record.parcialidades = len(content)
                fecha_anterior = 0
                sorted_content = sorted(
                    content, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"), reverse=True
                )
                for r in sorted_content:
                    if r.get("journal_name") != "Exchange Difference":
                        if r.get("name") != "":
                            # Si los pagos se relizaron en la misma fecha, estos se deben sumar
                            if r.get("date") == fecha_anterior or fecha_anterior == 0:
                                if r.get("name") == False:
                                    record.monto_ultimo_pago += 0
                                    continue
                                # TODO: Validar que el monto no este vacio
                                if r.get("amount"):
                                    if "USD" in r.get("currency"):
                                        moneda = record.env["res.currency.rate"].search(
                                            [
                                                ("currency_id", "=", 2),
                                                ("name", "<=", date.fromisoformat(r.get("date"))),
                                            ],
                                            order="name desc",
                                            limit=1,
                                        )
                                        tipo_cambio = 1 / moneda.rate
                                        record.monto_ultimo_pago += r.get("amount") * tipo_cambio
                                        fecha_anterior = r.get("date")
                                    else:
                                        record.monto_ultimo_pago += r.get("amount")
                                        fecha_anterior = r.get("date")
                                else:
                                    record.monto_ultimo_pago += 0
                        else:
                            record.monto_ultimo_pago += 0
            else:
                record.fecha_ultimo_pago_factura = None
                record.parcialidades = 0
                record.monto_ultimo_pago = 0

    @api.depends("fecha_ultimo_pago_factura")
    def _get_fecha_ultimo_pago_factura(self):
        for record in self:
            if record.fecha_ultimo_pago_factura:
                record.fecha_ultimo_pago_factura_store = record.fecha_ultimo_pago_factura
            else:
                record.fecha_ultimo_pago_factura_store = None

    @api.depends("parcialidades")
    def _get_parcialidades(self):
        for record in self:
            if record.parcialidades:
                record.parcialidades_store = record.parcialidades
            else:
                record.parcialidades_store = 0

    @api.depends("monto_ultimo_pago")
    def _get_monto_ultimo_pago(self):
        for record in self:
            if record.monto_ultimo_pago:
                record.monto_ultimo_pago_store = record.monto_ultimo_pago
            else:
                record.monto_ultimo_pago_store = 0

    @api.depends("fecha_ultimo_pago_factura_store", "invoice_date")
    @api.onchange("fecha_ultimo_pago_factura_store", "invoice_date")
    def get_dias_pagar(self):
        for record in self:
            if record.fecha_ultimo_pago_factura_store and record.invoice_date:
                record.dias_pagar = (
                    record.fecha_ultimo_pago_factura_store - record.invoice_date
                ).days
            else:
                record.dias_pagar = 0

    @api.depends("dias_pagar")
    @api.onchange("dias_pagar")
    def set_dias_pagar(self):
        for record in self:
            if record.dias_pagar == 0:
                record.dias_pagar_store = 0
            else:
                record.dias_pagar_store = record.dias_pagar
