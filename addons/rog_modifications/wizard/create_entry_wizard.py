# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models
from openerp.tools.translate import _
from datetime import datetime, timedelta
from openerp.exceptions import UserError



class CreateEntryWizard(models.TransientModel):
    _inherit = 'create.entry.wizard'

    @api.multi
    def btn_create_entry(self):
        ctx = dict(self._context)
        ctx['is_ssd_sbu'] = self.is_ssd_sbu
        ctx['hr_department_id'] = self.hr_department_id
        ctx['sbu_id'] = self.sbu_id
        ctx['is_ssa_allow_split'] = True
        res = super(CreateEntryWizard,self.with_context(ctx)).btn_create_entry()
        return res

    hr_department_id = fields.Many2one('hr.department', string='Shared Service', track_visibility='onchange')
    sbu_id = fields.Many2one('sbu', string='SBU', track_visibility='onchange')
    is_ssd_sbu = fields.Selection([
        ('ssd', 'Shared Service'),
        ('sbu', 'SBU')
    ], string='Category', track_visibility='onchange')





