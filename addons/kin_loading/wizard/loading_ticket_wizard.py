# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api, _
from openerp.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import *

class TicketQtyRequested(models.TransientModel):
    _name = 'ticket.qty.requested'



    qty_requested = fields.Float(string="Requested Qty.")
    ticket_count = fields.Integer(string="Ticket Count")
    ticket_wizard_id = fields.Many2one('loading.ticket.wizard',string='Ticket Wizard')


class LoadingTicketWizard(models.TransientModel):
    _name = 'loading.ticket.wizard'

    @api.onchange('ticket_qty_requested_ids')
    def onchange_qty(self):
        ticket_qty_requested_ids =  self.ticket_qty_requested_ids
        total_qty_requested = total_ticket_count = total_qty = 0
        for rec in ticket_qty_requested_ids:
            total_qty_requested += rec.qty_requested
            total_ticket_count += rec.ticket_count
            total_qty += rec.qty_requested * rec.ticket_count
        self.total_qty_requested = total_qty_requested
        self.total_ticket_count = total_ticket_count
        self.total_qty = total_qty

    @api.multi
    def action_generate_ticket(self):
        order_id = self.env.context['the_order_id']
        sale_order = self.env['sale.order'].browse(order_id)
        #authorization_code = sale_order.authorization_code
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
                 'is_throughput_so' : sale_order.is_throughput_order,
               'is_internal_use_so': sale_order.is_internal_use_order,
                'sale_order' : sale_order
               # 'location_dest_id':self.recipient_id.property_stock_customer.id,
            }

        if is_generate_loading_date :
            loading_date_interval = company.loading_date_interval or False
            if loading_date_interval :
                today = date.today()
                ticket_date = today + relativedelta(days=+loading_date_interval)
                ctx.update({'loading_date':ticket_date})

        #check if the qty is more than the ticketed qty
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
            qty_requested = line.qty_requested
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


    def _populate_order_lines(self):
        order_id = self.env.context['active_id']
        order_lines = self.env['sale.order.line'].search([('order_id','=',order_id)])
        return order_lines[0]

    order_line_ids = fields.Many2many('sale.order.line', string='Order Lines',default=_populate_order_lines)
    # recipient_id = fields.Many2one('res.partner',string='Goods Recipient')
    ticket_qty_requested_ids = fields.One2many('ticket.qty.requested','ticket_wizard_id',string="Ticket Qty. Requested")
    total_qty = fields.Float(string='Total Qty.')
    total_qty_requested = fields.Float(string='Total Requested Qty.')
    total_ticket_count = fields.Float(string='Total Ticket Count')

