# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2020  Kinsolve Solutions
# Copyright 2020 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp import SUPERUSER_ID
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import float_is_zero, float_compare,float_round, DEFAULT_SERVER_DATETIME_FORMAT
from urllib import urlencode
from urlparse import urljoin
from openerp.tools import amount_to_text
from dateutil.relativedelta import relativedelta
from datetime import *


class Compare(models.Model):
    _name = 'kin.compare'

    @api.multi
    def btn_compare(self):
        for debit_line in self.compare_lines_debit_ids :
            debit = debit_line.debit
            for credit_line in self.compare_lines_credit_ids :
                if debit == credit_line.credit:
                    debit_line.unlink()
                    credit_line.unlink()


    name = fields.Char('Name')
    compare_lines_debit_ids = fields.One2many('kin.compare.lines.debit','compare_id',string='Compare Debit Lines')
    compare_lines_credit_ids = fields.One2many('kin.compare.lines.credit', 'compare_id', string='Compare Credit Lines')

class CompareDebit(models.Model):
    _name = 'kin.compare.lines.debit'

    date = fields.Date(string='Date')
    name = fields.Char(string='Entry')
    journal = fields.Char(string='Journal')
    partner = fields. Char(string='Partner')
    ref = fields.Char(string='Ref - Label')
    debit = fields.Float(string='Debit')
    compare_id = fields.Many2one('kin.compare',string='Compare')


class CompareCredit(models.Model):
    _name = 'kin.compare.lines.credit'

    date = fields.Date(string='Date')
    name = fields.Char(string='Entry')
    journal = fields.Char(string='Journal')
    partner = fields.Char(string='Partner')
    ref = fields.Char(string='Ref - Label')
    credit = fields.Float(string='Credit')
    compare_id = fields.Many2one('kin.compare',string='Compare')