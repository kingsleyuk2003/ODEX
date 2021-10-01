# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp.exceptions import UserError
from openerp import api, fields, models, _
from datetime import datetime
import requests



class KinSMS(models.Model):
    _name = "kin.sms"

    recipient_ids = fields.Many2many('res.partner', 'kin_sms_partner_rel', 'kin_sms_id', 'partner_id',
                                     string="Recipients",required=True)
    message = fields.Text(string='Message', size=160, required=True)
    sms_date = fields.Datetime('SMS Date',default=lambda self: datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
    # sender_id = fields.Char(string='Sender ID')
    state = fields.Selection([('draft', "Draft"), ('sent', "Sent")],string='Status',default='draft')
    sms_log_ids = fields.One2many('kin.sms.log','sms_id',string="Log History", )
    log_count = fields.Integer(string='# of Orders', compute='_get_logs', readonly=True)

    def _get_logs(self):
        sms_log_ids = self.env['kin.sms.log'].search([('sms_id', '=', self.id)])

        self.update({
                'log_count': len(set(sms_log_ids.ids)),
                'sms_log_ids': sms_log_ids.ids ,
            })

    @api.multi
    def action_view_log(self):
        sms_log_ids = self.mapped('sms_log_ids')
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('kin_sms.sms_log_action')
        list_view_id = imd.xmlid_to_res_id('kin_sms.sms_log_tree')
        form_view_id = imd.xmlid_to_res_id('kin_sms.sms_log')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(sms_log_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % sms_log_ids.ids
        elif len(sms_log_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = sms_log_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.multi
    def submit_sent_btn(self):
        sender = recipients = message = False
        for record in self :
            list_contact = []
            no_contact = []
            sender = False # Use the one set in the SMS configuration
            recipients = record.recipient_ids
            message = record.message
            if not recipients:
                raise UserError(_("No Receipents"))

            for recipient in recipients:
                mobile = recipient.mobile and recipient.mobile.strip()
                phone = recipient.phone and recipient.phone.strip()
                if mobile or phone :
                    list_contact.append(mobile or phone)
                else :
                    no_contact.append(recipient.name)

            if len(no_contact) > 0 :
                raise UserError(_("The following contact(s) don't have a mobile or phone number: \n  %s") % (', '.join(con for con in no_contact)))

            result = record.send_sms(sender,message,str(','.join(listc for listc in list_contact)))
            if result :
                record.write({'state':'sent'})
        return

    @api.multi
    def submit_reset_btn(self):
        self.write({'state':'draft'})
        return


    def send_sms(self,sender,message,recipients):
        args = {}
        base_url = self.env.user.company_id.base_url

        username_key = self.env.user.company_id.kin_username_key or False
        username_value = self.env.user.company_id.kin_username_value or False
        if username_key and username_value :
            args.update({username_key:username_value})

        password_key = self.env.user.company_id.kin_password_key or False
        password_value = self.env.user.company_id.kin_password_value or False
        if password_key and password_value :
            args.update({password_key:password_value})

        message_key = self.env.user.company_id.kin_message_key or False
        message_value  = message or False
        if message_key and message_value :
            args.update({message_key:message_value})

        sender_value = False
        sender_key = self.env.user.company_id.kin_sender_key or False
        if sender :
            sender_value =  sender
        else :
            sender_value = self.env.user.company_id.kin_sender_value or False

        if sender_key and sender_value :
            args.update({sender_key:sender_value})

        password_key = self.env.user.company_id.kin_password_key
        password_value = self.env.user.company_id.kin_password_value
        if password_key and password_value :
            args.update({password_key:password_value})

        recipients_key = self.env.user.company_id.kin_recipients_key
        recipients_value = recipients
        if recipients_key and recipients_value :
            args.update({recipients_key:recipients_value})

        other_parameters  = self.env.user.company_id.kin_other_parameter_ids
        for param in other_parameters :
            args.update({param.key:param.value})


        response = requests.get(base_url, params=args) # see http://docs.python-requests.org/en/master/user/quickstart/#passing-parameters-in-urls

        sms_log = self.env['kin.sms.log']
        cr_id = sms_log.create({
            'response_reason': response.reason,
            'response_status_code': response.status_code,
            'date_log': fields.Date.context_today(self),
            'response_text': response.text,
            'sender_id': sender,
            'recipient_ids': recipients,
            'txt_msg':message ,
            'sms_id': self.id
        })

        if response.reason == 'OK' :
            return True
        else :
            return False



class SMSLog(models.Model):

    _name = "kin.sms.log"

    date_log = fields.Datetime(string="Date Log")
    #sender_id = fields.Char(string="Sender")
    recipient_ids = fields.Char(string="Recipients")
    txt_msg = fields.Char(string="Text Message")
    response_text = fields.Char(string="Response Message")
    response_status_code = fields.Char(string="Status Code")
    response_reason = fields.Char(string="Outcome")
    sms_id = fields.Many2one("kin.sms", string="SMS")



class SmsParams(models.Model):
    _name = "kin.sms.params"

    key = fields.Char(string="Name")
    value = fields.Char(string="Value")
    company_id = fields.Many2one("res.company", string="Company")


class Company(models.Model):
    _inherit = "res.company"

    kin_base_url = fields.Char(string="Base URL")
    kin_username_key = fields.Char(string="Username Name")
    kin_username_value = fields.Char(string="Username Value")
    kin_password_key = fields.Char(string="Password Name")
    kin_password_value = fields.Char(string="Password Value")
    kin_username_value = fields.Char(string="Username Value")
    kin_message_key = fields.Char(string="Message Name")
    kin_sender_key = fields.Char(string="Sender Name")
    kin_sender_value = fields.Char(string="Sender Value")
    kin_recipients_key = fields.Char(string="Recipients Name/Key")
    kin_other_parameter_ids = fields.One2many('kin.sms.params','company_id',string="Other Parameters", help="Please enter the name=value pair on the url string, except the parameters listed above")




