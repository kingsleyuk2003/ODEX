# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2025  Kinsolve Solutions
# Copyright 2025 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
# © 2016 ADHOC SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime,date, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError,ValidationError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from urllib import urlencode
from urlparse import urljoin
import  time
from openerp.tools import amount_to_text


class AccountPaymentGroupExtend(models.Model):
    _inherit = 'account.payment.group'

    # ref: 2016 ADHOC SA
    @api.multi
    @api.depends('payment_ids.amount')
    def _compute_payments_amount_currency(self):
        for rec in self:
            rec.payments_amount_currency = sum(rec.payment_ids.mapped(
                'amount'))

    #ref: 2016 ADHOC SA
    payments_amount_currency = fields.Float(
        compute='_compute_payments_amount_currency',
        string='Amount',
        track_visibility='always', store=True
    )


    @api.multi
    def amount_to_text_usd(self, amt, currency=False):
        dd = self.mapped('matched_move_line_ids')
        ddd = list(set(dd))

        big = 'Dollar'
        small = 'Cent'

        amount_text = amount_to_text(amt, currency).replace('euro', big).replace('Cent', small)
        return str.upper('**** ' + amount_text + '**** ONLY')