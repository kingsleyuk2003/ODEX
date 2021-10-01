# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _
from datetime import datetime



class Company(models.Model):
    _inherit = "res.company"

    is_enable_birthday_alert = fields.Boolean("Enable Birthday Alert",default=False)
    kin_sms_birthday_text = fields.Char('SMS Birthday Text Message',
                               default="Dear ${object.name} , We at ${ctx.get('company_name')} specially wish you a wonderful happy birthday.")


class ResPartner(models.Model):
    _inherit = "res.partner"

    sms_birthday = fields.Date("SMS Birthday")

    @api.model
    def run_sms_birthday(self):
        is_enable_birthday_alert = self.env.user.company_id.is_enable_birthday_alert
        kin_sms_birthday_text = self.env.user.company_id.kin_sms_birthday_text

        if is_enable_birthday_alert and kin_sms_birthday_text:
            partners = self.env['res.partner'].search([('sms_birthday', '!=', False)])
            for record in partners:
                sms_birthday = record.sms_birthday
                cust_phone = record.phone
                cust_mobile = record.mobile
                if sms_birthday and (cust_phone or cust_mobile):

                    today = datetime.today()
                    day = today.day
                    month = today.month

                    sms_birthday = datetime.strptime(sms_birthday,'%Y-%m-%d')
                    day_birth = sms_birthday.day
                    month_birth = sms_birthday.month

                    if day == day_birth and  month == month_birth  :
                        #send sms
                        sender = False  # let it use the sender set in the POS configuration form
                        kin_sms_birthday_text = self.env.user.company_id.kin_sms_birthday_text
                        if kin_sms_birthday_text :
                            ctx = {'company_name': self.env.user.company_id.name }
                            text_message = self.env['mail.template'].with_context(ctx).render_template(kin_sms_birthday_text, 'res.partner', record.id)
                            self.env['kin.sms'].send_sms(sender=sender, message=text_message, recipients=cust_mobile or cust_phone)

            return True









