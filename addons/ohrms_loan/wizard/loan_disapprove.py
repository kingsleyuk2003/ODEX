# -*- coding: utf-8 -*-

from openerp import api, fields, models

class loan_disaaprove_wizard(models.TransientModel):
    _name = 'loan.disapprove.wizard'
    _description = 'loan Disapprove Wizard'

    @api.multi
    def disapprove_loan(self):
        loan_ids = self.env.context['active_ids']
        msg = self.msg
        loans = self.env['hr.loan'].browse(loan_ids)
        for loan in loans :
            loan.action_refuse(msg)
        return

    msg = fields.Text(string='Reason for Dis-approval', required=True)
