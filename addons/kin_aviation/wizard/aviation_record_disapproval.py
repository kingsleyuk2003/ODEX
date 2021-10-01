# -*- coding: utf-8 -*-

from openerp import api, fields, models

class AviationRecordDisApprovalWizard(models.TransientModel):
    _name = 'aviation.record.disapproval.wizard'
    _description = 'Aviation Record Disapproval Wizard'


    @api.multi
    def action_disapprove(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        records = self.env['kin.aviation.record'].browse(rec_ids)
        for rec in records:
            rec.action_disapprove(msg)
        return


    msg = fields.Text(string='Message', required=True)


