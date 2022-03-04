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