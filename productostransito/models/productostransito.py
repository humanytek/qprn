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
        currency_field = 'moneda_default',
        compute = '_en_transito',
        default=0,
    )

    costotransito_store = fields.Monetary(
        string = 'Costo en tránsito',
        currency_field = 'moneda_default',
        compute = '_costo_transito_store',
        store=True,
    )

    moneda_default = fields.Many2one(
        string = 'Moneda default',
        related = 'company_id.currency_id',
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

    cancelados = fields.Float(
        string = 'Cancelados',
        compute = '_get_cancelados',
        default = 0,
    )

    @api.depends('move_ids')
    def _en_transito(self):
        for r in self:
            if r.state == 'purchase':
                if r.move_ids:
                    for m in r.move_ids:
                        tm = m.filtered(lambda x: x.state == 'assigned')
                        r.entransito = sum(tm.mapped('product_uom_qty'))
                        subtotal = r.price_unit * r.entransito
                        fecha = r.order_id.date_approve
                        r.costotransito = r.order_id.currency_id._convert(subtotal,
                                                                        r.order_id.company_id.currency_id,
                                                                        r.order_id.company_id,
                                                                        fecha)
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

    @api.depends('move_ids.state', 'move_ids.product_uom_qty', 'move_ids.product_uom')
    def _compute_qty_received(self):
        super(Productostransito, self)._compute_qty_received()
        for line in self:
            if line.qty_received_method == 'stock_moves':
                total = 0.0
                # In case of a BOM in kit, the products delivered do not correspond to the products in
                # the PO. Therefore, we can skip them since they will be handled later on.
                for move in line.move_ids.filtered(lambda m: m.product_id == line.product_id):
                    if move.state == 'done':
                        if move.location_dest_id.usage == "supplier":
                            if move.to_refund:
                                total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)  
                        elif move.origin_returned_move_id and move.origin_returned_move_id._is_dropshipped() and not move._is_dropshipped_returned():
                            # Edge case: the dropship is returned to the stock, no to the supplier.
                            # In this case, the received quantity on the PO is set although we didn't
                            # receive the product physically in our stock. To avoid counting the
                            # quantity twice, we do nothing.
                            pass
                        elif (
                            move.location_dest_id.usage == "internal"
                            and move.to_refund
                            and move.location_dest_id
                            not in self.env["stock.location"].search(
                                [("id", "child_of", move.warehouse_id.view_location_id.id)]
                            )
                        ):
                            total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                        else:
                            total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                        line.entransito_store = (line.product_qty - total) - line.cancelados
                        subtotal = line.price_unit * line.entransito_store
                        fecha = line.order_id.date_approve
                        line.costotransito = line.order_id.currency_id._convert(subtotal,
                                                                                line.order_id.company_id.currency_id,
                                                                                line.order_id.company_id,
                                                                                fecha)
                    if total == 0:
                        line.entransito_store = line.entransito_store - line.cancelados
                        subtotal = line.price_unit * line.entransito_store
                        fecha = line.order_id.date_approve
                        line.costotransito = line.order_id.currency_id._convert(subtotal,
                                                                                line.order_id.company_id.currency_id,
                                                                                line.order_id.company_id,
                                                                                fecha)

    @api.depends('move_ids')
    def _get_cancelados(self):
        for record in self:
            for m in record.move_ids:
                tm = m.filtered(lambda x: x.state == 'cancel')
                record.cancelados = sum(tm.mapped('product_uom_qty'))
