from odoo import fields, models,api
from datetime import date
import json

class Ultimopagofactura(models.Model):
    _inherit = 'account.move'

    fecha_ultimo_pago_factura = fields.Date(
        string='Fecha último pago compute',
        compute='_last_payment_date',
        readonly= True,
        default = None,
    )
    
    fecha_ultimo_pago_factura_store = fields.Date(
        string='Fecha último pago',
        compute='_get_fecha_ultimo_pago_factura',
        readonly= True,
        store = True,
    )

    dias_pagar = fields.Integer(
        string = 'Días que tardaron en pagar compute',
        compute = 'get_dias_pagar',
        default = 0,
    )

    dias_pagar_store = fields.Integer(
        string = 'Días que tardaron en pagar',
        compute = 'set_dias_pagar',
        default = 0,
        store = True,
    )

    @api.depends('invoice_payments_widget')
    def _last_payment_date(self):
        for record in self:
            dict = json.loads(record.invoice_payments_widget)
            if dict and dict.get("content"):
                content = dict.get("content")
                record.fecha_ultimo_pago_factura =  date.fromisoformat(max(payment.get("date") for payment in content))
            else:
                record.fecha_ultimo_pago_factura = None      

    @api.depends('fecha_ultimo_pago_factura')
    def _get_fecha_ultimo_pago_factura(self):
        for record in self:
            if record.fecha_ultimo_pago_factura:
                record.fecha_ultimo_pago_factura_store = record.fecha_ultimo_pago_factura
            else:
                record.fecha_ultimo_pago_factura_store = None

    @api.depends('fecha_ultimo_pago_factura_store', 'invoice_date')
    @api.onchange('fecha_ultimo_pago_factura_store', 'invoice_date')
    def get_dias_pagar(self):
        for record in self:
            if record.fecha_ultimo_pago_factura_store and record.invoice_date:
                record.dias_pagar = (record.fecha_ultimo_pago_factura_store-record.invoice_date).days
            else:
                record.dias_pagar = 0

    @api.depends('dias_pagar')
    @api.onchange('dias_pagar')
    def set_dias_pagar(self):
        for record in self:
            if record.dias_pagar == 0:
                record.dias_pagar_store = 0
            else:
                record.dias_pagar_store = record.dias_pagar