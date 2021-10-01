# -*- coding: utf-8 -*-

from odoo import api, fields, models

class NetDifferenceConfirmationWizard(models.TransientModel):
    _name = 'net.difference.confirmation.wizard'
    _description = 'Net Difference Confirmation Wizard'

    @api.multi
    def action_confirm_wizard(self):
        rec_ids = self.env.context['active_ids']
        records = self.env['kin.stock.control'].browse(rec_ids)
        for rec in records :
            rec.action_submit()
        return

    net_difference = fields.Float(string='Net Difference')


