# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from openerp import api, fields, models, _
from datetime import datetime, timedelta

class HRContract(models.Model):
    _inherit = 'hr.contract'


    paye_agary = fields.Float(string='PAYE')
    pension_agary = fields.Float(string='PENSION')
    bank_agary = fields.Float(string='BANK')










