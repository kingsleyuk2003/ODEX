# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api, _
from openerp.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import *

class LoadingTicketWizardROG(models.TransientModel):
    _inherit = 'loading.ticket.wizard'


    @api.multi
    def action_generate_ticket(self):
        order_id = self.env.context['the_order_id']
        sale_order = self.env['sale.order'].browse(order_id)
        # authorization_code = sale_order.authorization_code
        authorization_code = sale_order.advance_invoice_id.display_name
        is_has_advance_invoice = sale_order.is_has_advance_invoice

        if len(self.order_line_ids) > 1 :
            raise UserError(_('Please remove one of the order line. You can only generate ticket per order line'))

        company = self.env.user.company_id
        is_generate_loading_date = company.is_generate_loading_date

        ctx = {
                'authorization_code': authorization_code,
                'is_load_ticket_btn': self.env.context['is_load_ticket_btn'],
                'is_has_advance_invoice':is_has_advance_invoice,
                # 'recipient_id' :self.recipient_id,
                'is_throughput_so': sale_order.is_throughput_order,
               'is_internal_use_so': sale_order.is_internal_use_order,
                'sale_order' : sale_order,
                'location_dest_id':sale_order.partner_id.property_stock_customer.id,
                'is_ssd_sbu' : sale_order.is_ssd_sbu,
                'hr_department_id' : sale_order.hr_department_id.id,
                'sbu_id' : sale_order.sbu_id.id,
                'is_ssa_allow_split': True,
            }

        if is_generate_loading_date :
            loading_date_interval = company.loading_date_interval or False
            if loading_date_interval :
                today = date.today()
                ticket_date = today + relativedelta(days=+loading_date_interval)
                ctx.update({'loading_date':ticket_date})


        # check if the qty is more than the ticketed qty
        qty_ticket = 0
        for line in self.ticket_qty_requested_ids:
            qty_requested = line.qty_requested
            ticket_count = line.ticket_count
            qty_ticket += qty_requested * ticket_count

        ticket_remaining_qty = self.order_line_ids[0].ticket_remaining_qty
        if qty_ticket > ticket_remaining_qty:
            raise UserError(_('The Requested Ticket Qty (%s). is more than the Un-Ticketed Qty. (%s)' % (qty_ticket,self.order_line_ids[0].ticket_remaining_qty)))

        res = False
        for line in self.ticket_qty_requested_ids:
            qty_requested =  line.qty_requested
            ticket_count = line.ticket_count

            for x in range(ticket_count):
                self.order_line_ids[0].product_ticket_qty = qty_requested
                res = sale_order.with_context(ctx).action_create_loading_ticket()
        if res:
            self.env.user.notify_info('LOADING TICKET(S) SUCESSFULLY CREATED')
            return sale_order.action_view_delivery()
        else:
            raise UserError(_(
                "Sorry, No Requested Ticket Qty. was set for any of the product to be delivered"))




