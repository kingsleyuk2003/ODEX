# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2025  Kinsolve Solutions
# Copyright 2025 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


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


    @api.multi
    def amount_to_text(self, amt, currency=False):
        dd = self.mapped('matched_move_line_ids')
        ddd = list(set(dd))
        big = ''
        small = ''
        if currency.name == 'SLE':
            big = 'Leone'
            small = 'Cent'
        elif currency.name == 'USD':
            big = 'Dollar'
            small = 'Cent'
        else:
            big = 'Naira'
            small = 'kobo'

        amount_text = amount_to_text(amt, currency).replace('euro', big).replace('Cent', small)
        return str.upper('**** ' + amount_text + '**** ONLY')



class HRPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    fuel_pump_price = fields.Float('Fuel Pump Price')
    lrd_rate = fields.Float('Exchange Rate')


class HRContract(models.Model):
    _inherit = 'hr.contract'

    communication_allowance = fields.Float(string="Communication. Allowance (USD)")
    fuel_transport_allowance = fields.Float(string="Fuel/Transport Allowance (ltrs)")
    fuel_pump_price = fields.Float(string='Uniform Fuel Pump Price for all Salary Structure',related='struct_id.fuel_pump_price')


class HRExtend(models.Model):

    _inherit = 'hr.employee'

    bank_account_number_lrd = fields.Char(string='Bank Account Number (SLE)')
    bank_account_number_usd = fields.Char(string='Bank Account Number (USD)')