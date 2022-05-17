from odoo import fields, models,api
from datetime import date, timedelta
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

    parcialidades = fields.Integer(
        string='Parcialidades compute',
        compute='_last_payment_date',
        readonly= True,
        default = 0,
    )

    parcialidades_store = fields.Integer(
        string='Parcialidades',
        compute='_get_parcialidades',
        readonly= True,
        store = True,
    )

    totalpagado = fields.Float(
        string = 'Total pagado compute',
        compute = '_last_payment_date',
        readonly = True,
        default = 0,
    )

    totalpagado_store = fields.Float(
        string = 'Total pagado',
        compute = '_get_totalpagado',
        readonly = True,
        default = 0,
    )

    @api.depends('invoice_payments_widget')
    def _last_payment_date(self):
        for record in self:
            dict = json.loads(record.invoice_payments_widget)
            if dict and dict.get("content"):
                content = dict.get("content")
                record.fecha_ultimo_pago_factura = date.fromisoformat(max(payment.get("date") for payment in content))
                record.parcialidades =  len(content)
                for r in content:
                    #We get payment date and substract a day
                    fecha_aux = (date.fromisoformat(r.get("date"))) - timedelta(1)
                    #We get the amount and convert to currency of the date
                    monto = r.get("amount")
                    moneda = record.env['res.currency.rate'].search([('currency_id','=',record.currency_id.id),
                    ('name','<=',fecha_aux)],order='name desc', limit=1)
                    if moneda:
                        #If moneda exists, we need calculate totalpagado with the last currency at fecha_aux
                        record.totalpagado += monto * (1/moneda.rate)
                    else: 
                        record.totalpagado += monto * 0
            else:
                record.fecha_ultimo_pago_factura = None
                record.parcialidades = 0     
                record.totalpagado = 0

    @api.depends('fecha_ultimo_pago_factura')
    def _get_fecha_ultimo_pago_factura(self):
        for record in self:
            if record.fecha_ultimo_pago_factura:
                record.fecha_ultimo_pago_factura_store = record.fecha_ultimo_pago_factura
            else:
                record.fecha_ultimo_pago_factura_store = None

    @api.depends('parcialidades')
    def _get_parcialidades(self):
        for record in self:
            if record.parcialidades:
                record.parcialidades_store = record.parcialidades
            else:
                record.parcialidades_store = 0

    @api.depends('totalpagado')
    def _get_totalpagado(self):
        for record in self:
            if record.totalpagado:
                record.totalpagado_store = record.totalpagado
            else:
                record.totalpagado_store = 0

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