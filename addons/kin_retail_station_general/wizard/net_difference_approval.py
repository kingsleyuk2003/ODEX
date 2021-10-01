# -*- coding: utf-8 -*-

from openerp import api, fields, models

class NetDifferenceApprovalWizard(models.TransientModel):
    _name = 'net.difference.approval.wizard'
    _description = 'Net Difference Approval Wizard'

    @api.multi
    def action_approve_wizard(self):
        rec_ids = self.env.context['active_ids']
        records = self.env['kin.stock.control'].browse(rec_ids)
        for rec in records :
            rec.action_approved()
        return

    net_difference = fields.Float(string='Net Difference')


