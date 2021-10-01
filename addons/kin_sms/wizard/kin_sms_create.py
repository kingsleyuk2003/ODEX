# -*- coding: utf-8 -*-

from openerp import api, fields, models


class KinSMSWizard(models.TransientModel):
    _name = 'kin.sms.wizard'
    _description = 'SMS Wizard'

    @api.multi
    def send_sms(self):
        partner_ids = self.env.context['active_ids']
        msg = self.msg
        res = self.create_sms(msg,partner_ids)
        return res

    def create_sms(self,msg,partner_ids):
        kin_sms_obj = self.env['kin.sms']
        sms_vals = {
            'message': msg,
            'recipient_ids': [(6, 0, [partner_ids])]
        }
        res = kin_sms_obj.create(sms_vals).submit_sent_btn()
        return res


    msg = fields.Text(string='SMS Message', required=True)

