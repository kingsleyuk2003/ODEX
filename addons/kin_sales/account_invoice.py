# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError
from datetime import datetime,date, timedelta


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        # Check if partner credit limit has been approved
        # partner_id = self.partner_id
        # if partner_id:
        #     if partner_id.is_credit_limit_changed and not partner_id.is_credit_limit_approved:
        #         raise UserError(
        #             _('Please Contact the Responsible User to Approve the New Credit Limit (%s), for the Partner (%s)') % (
        #             partner_id.credit_limit, partner_id.name))

        res = super(AccountInvoice,self).invoice_validate()
        return res