# -*- coding: utf-8 -*-

from openerp import api, fields, models

class TarmacTruckCheckListApprovalWizard(models.TransientModel):
    _name = 'tarmac.truck.checklist.approval.wizard'
    _description = 'Tarmac Truck Check List Approval Wizard'


    @api.multi
    def action_fail_checklist(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        records = self.env['tarmac.truck.checklist'].browse(rec_ids)
        for rec in records:
            rec.action_fail_check(msg)
        return


    @api.multi
    def action_pass_checklist_close(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        records = self.env['tarmac.truck.checklist'].browse(rec_ids)
        for rec in records:
            rec.action_pass_check_close(msg)
        return

    msg = fields.Text(string='Message', required=True)


