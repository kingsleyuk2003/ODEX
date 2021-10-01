# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from openerp import api, fields, models, _

class AccountInvoiceAgary(models.Model):
    _inherit = 'account.invoice'

    # delivery_note = fields.Char(string='Delivery Note')
    supplier_ref = fields.Char(string='Suppliers Reference')
    other_ref = fields.Char(string='Other Reference')
    buyer_order_no = fields.Char(string='Buyer Order Number')
    buyer_order_no_dated = fields.Date('Buyer Order Dated')
    dispatch_doc_no = fields.Char('Dispatch Document Number')
    dispatch_doc_no_dated = fields.Date('Dispatch Doc. No. Dated')
    dispatched_through = fields.Char(string='Dispatched Through')
    destination = fields.Char(string='Destination')
    terms_of_delivery = fields.Text(string='Terms of Delivery')

