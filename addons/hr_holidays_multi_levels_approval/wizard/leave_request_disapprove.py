# -*- coding: utf-8 -*-

from openerp import api, fields, models

class leave_request_disaaprove_wizard(models.TransientModel):
    _name = 'leave.request.disapprove.wizard'
    _description = 'Leave Request Dispprove Wizard'

    @api.multi
    def disapprove_leave_request(self):
        holiday_ids = self.env.context['active_ids']
        msg = self.msg
        hr_holidays = self.env['hr.holidays'].browse(holiday_ids)
        for holiday in hr_holidays :
            holiday.action_disapprove(msg)
        return

    msg = fields.Text(string='Reason for Disapproval', required=True)
