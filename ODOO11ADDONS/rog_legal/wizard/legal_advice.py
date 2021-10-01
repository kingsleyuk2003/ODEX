# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class LegalResponseWizard(models.TransientModel):
    _name = 'legal.advice.wizard'
    _description = 'Legal Advice Wizard'

    @api.multi
    def action_legal_advice(self):
        rec_ids = self.env.context['active_ids']
        msg = self.legal_advice
        records = self.env['legal.advice'].browse(rec_ids)
        for rec in records:
            rec.action_legal_request(msg)
        return

    legal_advice = fields.Text(string='Legal Request',required=True)
