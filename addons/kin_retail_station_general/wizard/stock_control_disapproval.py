# -*- coding: utf-8 -*-

from openerp import api, fields, models

class StockControlDisApprovalWizard(models.TransientModel):
    _name = 'stock.control.disapproval.wizard'
    _description = 'Stock Control Disapproval Wizard'


    @api.multi
    def action_disapprove(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        records = self.env['kin.stock.control'].browse(rec_ids)
        for rec in records:
            rec.action_disapprove(msg)
        return



    msg = fields.Text(string='Message', required=True)


