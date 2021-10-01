# -*- coding: utf-8 -*-

from openerp import api, fields, models

class Adv_disaaprove_wizard(models.TransientModel):
    _name = 'adv.disapprove.wizard'
    _description = 'Advance Disapprove Wizard'

    @api.multi
    def disapprove_adv(self):
        adv_ids = self.env.context['active_ids']
        msg = self.msg
        advs = self.env['salary.advance'].browse(adv_ids)
        for adv in advs :
            adv.reject(msg)
        return

    msg = fields.Text(string='Reason for Dis-approval', required=True)
