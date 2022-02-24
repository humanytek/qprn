from odoo import fields, models, api


class Productostransito(models.Model):
    _inherit = 'purchase.order.line'

    entransito = fields.Float(
        string = 'En tránsito compute',
        compute = '_en_transito',
        default=0,
    )

    entransito_store = fields.Float(
        string = 'En tránsito',
        compute = '_en_transito_store',
        store= True,
    )

    costotransito = fields.Monetary(
        string = 'Costo en tránsito compute',
        currency_field = 'currency_id',
        compute = '_en_transito',
        default=0,
    )

    costotransito_store = fields.Monetary(
        string = 'Costo en tránsito',
        currency_field = 'currency_id',
        compute = '_costo_transito_store',
        store=True,
    )

    almacen = fields.Many2one(
        string = 'Almacén',
        related = 'order_id.picking_type_id'
    )

    proveedor = fields.Many2one(
        string = 'Proveedor',
        related = 'order_id.partner_id',
        store = True,
    )

    @api.depends('move_ids')
    def _en_transito(self):
        for r in self:
            if r.state == 'purchase':
                if r.move_ids:
                    for m in r.move_ids:
                        tm = m.filtered(lambda x: x.state == 'assigned')
                        r.entransito = sum(tm.mapped('product_uom_qty'))
                        r.costotransito = r.price_unit * r.entransito
                else:
                    r.entransito = 0
                    r.costotransito = 0
            else:
                r.entransito = 0
                r.costotransito = 0

    @api.depends('entransito')
    def _en_transito_store(self):
        for record in self:
            if record.entransito:
                record.entransito_store = record.entransito
            else:
                record.entransito_store = 0

    @api.depends('costotransito')
    def _costo_transito_store(self):
        for record in self:
            if record.costotransito:
                record.costotransito_store = record.costotransito
            else:
                record.costotransito_store = 0
