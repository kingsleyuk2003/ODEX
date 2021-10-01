# -*- coding: utf-8 -*-

from openerp import api, fields, models

class sales_order_disapprove_markup_wizard(models.TransientModel):
    _name = 'sale.order.disapprove.markup.wizard'
    _description = 'Sales Order Disapprove Markup Wizard'

    @api.multi
    def disapprove_sales_orders_markup(self):
        sale_ids = self.env.context['active_ids']
        msg = self.msg
        sale_orders = self.env['sale.order'].browse(sale_ids)
        for order in sale_orders :
            order.action_disapprove_markup(msg)
        return

    msg = fields.Text(string='Reason for Markup Disapproval', required=True)
