from odoo import fields, models, api

class Vistapagos(models.Model):
    _inherit = 'account.payment'

    cliente_categorias_pagos = fields.Many2many(
        string = "Categorías",
        related="partner_id.category_id",
    )

    categoria_cliente = fields.Char(
        string = "Categoría del cliente",
        default = "Sin categoría",
        compute = "_get_categoria",
        store = True,
    )

    cliente_termino_pago = fields.Char(
        string = "Término de pago compute",
        compute = "_get_termino_pago",
        readonly= True,
        default = "Sin término de pago",
    )

    cliente_termino_pago_store = fields.Char(
        string = "Término de pago",
        compute = "_get_termino_pago_store",
        readonly= True,
        store = True,
    )

    tipocambio_pago = fields.Float(
        string = 'Cambio del día de pago compute',
        default = 0,
        compute = '_get_tipocambio_pago',
        digits=(12,4),
    )

    tipocambio_pago_store = fields.Float(
        string = 'Cambio del día de pago',
        default = 0,
        compute = '_get_tipocambio_pago_store',
        store = True,
        digits=(12,4),
    )

    @api.depends('date')
    @api.onchange('date')
    def _get_tipocambio_pago(self):
        for record in self:
            moneda = record.env['res.currency.rate'].search([('currency_id','=',record.currency_id.id),
                    ('name','<=',record.date)],order='name desc', limit=1)
            if moneda:
                record.tipocambio_pago = 1/moneda.rate
            else: 
                record.tipocambio_pago = 0

    @api.depends('tipocambio_pago')
    @api.onchange('tipocambio_pago')
    def _get_tipocambio_pago_store(self):
        for record in self:
            if record.tipocambio_pago:
                record.tipocambio_pago_store = record.tipocambio_pago
            else: 
                record.tipocambio_pago_store = 0

    @api.depends('cliente_categorias_pagos')
    def _get_categoria(self):
        for record in self:
            if record.cliente_categorias_pagos:
                for c in record.cliente_categorias_pagos:
                    record.categoria_cliente = c.name
                    break
            else:
                record.categoria_cliente = "Sin categoría"

    @api.depends('reconciled_invoice_ids')
    def _get_termino_pago(self):
        for record in self:
            if record.reconciled_invoice_ids:
                for inv in record.reconciled_invoice_ids:
                    record.cliente_termino_pago = inv.invoice_payment_term_id.name
                    break
            else:
                record.cliente_termino_pago = "Sin término de pago"

    @api.depends('cliente_termino_pago')
    def _get_termino_pago_store(self):
        for record in self:
            if record.cliente_termino_pago:
                record.cliente_termino_pago_store = record.cliente_termino_pago
            else:
                record.cliente_termino_pago_store = "Sin término de pago"