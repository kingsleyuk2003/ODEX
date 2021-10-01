# -*- coding: utf-8 -*-

from openerp import api, fields, models

class sales_orders_confirm_wizard(models.TransientModel):
    _name = 'sale.order.confirmation.wizard'
    _description = 'Sales Order Confirmation Wizard'

    @api.multi
    def confirm_sales_orders(self):
        sale_ids = self.env.context['active_ids']
        sale_orders = self.env['sale.order'].browse(sale_ids)
        for order in sale_orders :
            order.action_confirm()
        return
