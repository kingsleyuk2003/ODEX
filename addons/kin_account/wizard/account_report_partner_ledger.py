# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _
from openerp.exceptions import UserError
#
# class AccountPartnerLedgerExtend(models.TransientModel):
#     _inherit = "account.report.partner.ledger"
#
#
#     partner_ids = fields.Many2many('res.partner',string = "Partners", help="Filter by Partner")
#
#
#     def _print_report(self, data):
#         data = self.pre_print_report(data)
#         partner_ids =  [partner.id for partner in self.partner_ids]
#         data['form'].update({'partner_ids': partner_ids,'reconciled': self.reconciled, 'amount_currency': self.amount_currency})
#         action = self.env['report'].get_action(self, 'account_extra_reports.report_partnerledger', data=data)
#         return action
#
#     @api.onchange('result_selection')
#     def onchange_result_selection(self):
#         res = {}
#         #res =  {'domain': {'partner_ids': [('id', 'in',(1,2,3,4,5,6))]}}
#         if self.result_selection == 'supplier':
#             res =  {'domain': {'partner_ids': [('supplier', '=',True)]}}
#         elif self.result_selection == 'customer':
#             res =  {'domain': {'partner_ids': [('customer', '=',True)]}}
#         elif self.result_selection == 'customer_supplier':
#             res =  {'domain': {'partner_ids': ['|',('customer', '=',True),('supplier', '=',True)]}}
#         return res
#
