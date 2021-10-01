# -*- coding: utf-8 -*-

from openerp import api, fields, models

class TruckCheckListApprovalWizard(models.TransientModel):
    _name = 'truck.checklist.approval.wizard'
    _description = 'Truck Check List Approval Wizard'

    @api.multi
    def action_confirm(self):
        rec_ids = self.env.context['active_ids']
        records = self.env['truck.check.list'].browse(rec_ids)
        for rec in records :
            rec.action_confirm()
        return

    @api.multi
    def action_approve(self):
        rec_ids = self.env.context['active_ids']
        records = self.env['truck.check.list'].browse(rec_ids)
        for rec in records:
            rec.action_approve()
        return

    @api.multi
    def action_pass_all_checks(self):
        rec_ids = self.env.context['active_ids']
        records = self.env['truck.check.list'].browse(rec_ids)
        for rec in records:
            rec.action_mark_all()
        return


