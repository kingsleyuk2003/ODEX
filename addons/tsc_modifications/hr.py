# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from openerp import api, fields, models, _
from datetime import datetime, timedelta

class hrExtend(models.Model):
    _inherit = 'hr.employee'

    exp_rel_pos = fields.Char(string='Experience relevant to Position')

