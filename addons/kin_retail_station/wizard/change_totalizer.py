# -*- coding: utf-8 -*-

from openerp import api, fields, models
from openerp.exceptions import UserError

class ChangeTotalizerWizard(models.TransientModel):
    _name = 'change.totalizer.wizard'
    _description = 'Change Totalizer Wizard'

    @api.multi
    def action_change_totalizer(self):
        recs = self.env.context['active_ids']
        pumps = self.env['kin.fuel.pump'].browse(recs)
        pumps.change_totalizer_value(self.new_totalizer)
        return

    new_totalizer = fields.Float(string='New Totalizer Value',required=True)
