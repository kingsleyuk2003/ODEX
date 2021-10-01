# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class LegalResponseWizard(models.TransientModel):
    _name = 'legal.response.wizard'
    _description = 'Legal Response Wizard'

    @api.multi
    def action_legal_response(self):
        rec_ids = self.env.context['active_ids']
        msg = self.legal_response
        records = self.env['legal.advice'].browse(rec_ids)
        for rec in records:
            rec.action_legal_response(msg)
        return

    legal_response = fields.Text(string='Legal Response',required=True)
