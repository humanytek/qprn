from email.policy import default
from odoo import fields, models,api

class Margenfactura(models.Model):
    _inherit = 'account.move'

    sale_lines = fields.Many2many(
        string = 'Lineas de venta',
        related = 'line_ids.sale_line_ids',
    )

    margin_float = fields.Float(
        string = 'Float margin',
        default = 0,
        compute = '_get_margin',
    )

    currency_margin = fields.Many2one(
        string = 'Currency margin',
        related = 'sale_lines.currency_id',
    )

    margen_factura = fields.Float(
        string = 'Margen de venta',
        compute = '_set_margin',
        default = 0,
    )
    
    margen_factura_nacional = fields.Float(
        string = 'Margen de venta nacional',
        compute = '_get_margen_factura_nacional',
        store = True,
        default = 0,
    )

    tipocambio = fields.Float(
        string = 'Cambio del día compute',
        default = 0,
        compute = '_obtener_tasa',
        digits=(12,4),
    )

    tipocambio_store = fields.Float(
        string = 'Cambio del día',
        default = 0,
        compute = '_get_tipocambio_store',
        store = True,
        digits=(12,4),
    )

    @api.depends('invoice_date')
    @api.onchange('invoice_date')
    def _obtener_tasa(self):
        for record in self:
            moneda = record.env['res.currency.rate'].search([('currency_id','=',record.currency_id.id),
                    ('name','<=',record.invoice_date)],order='name desc', limit=1)
            if moneda:
                record.tipocambio = 1/moneda.rate
            else: 
                record.tipocambio = 0

    @api.depends('tipocambio')
    @api.onchange('tipocambio')
    def _get_tipocambio_store(self):
        for record in self:
            if record.tipocambio:
                record.tipocambio_store = record.tipocambio
            else: 
                record.tipocambio_store = 0
                
    @api.depends('invoice_line_ids')
    def _get_margin(self):
        for record in self:
            if record.invoice_line_ids:
                for accountline in record.invoice_line_ids:
                    if accountline.sale_line_ids:
                        for saleline in accountline.sale_line_ids:
                            record.margin_float += saleline.margin
                    else: 
                        record.margin_float += 0
            else:
                record.margin_float = 0

    @api.depends('margin_float', 'currency_margin', 'tipocambio_store')
    def _set_margin(self):
        for record in self:
            if record.margin_float and record.currency_margin:
                if record.currency_margin.name == 'USD':
                        record.margen_factura = record.margin_float * record.tipocambio_store
                else:
                    record.margen_factura = record.margin_float
            else:
                record.margen_factura = 0

    @api.depends('margen_factura')
    @api.onchange('margen_factura')
    def _get_margen_factura_nacional(self):
        for record in self:
            if record.margen_factura == 0:
                record.margen_factura_nacional = 0
            else: 
                record.margen_factura_nacional = record.margen_factura

