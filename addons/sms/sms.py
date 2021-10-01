# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models
import requests



class SMSCompose(models.Model):

    _name = "sms.compose"

    recipients = fields.Text(string='Recipients',help="Please enter recipients number. You can separate them by comma")
    message = fields.Text(string='Message', size=160, required=1)
    sender_id = fields.Char(string='Sender ID')
    state = fields.Selection([('draft', "Draft"), ('sent', "Sent")],string='Status',default='draft')
    sms_log_ids = fields.One2many('sms.log','compose_id',string="Log History", )

    @api.multi
    def submit_sent_btn(self):
        sender = recipients = message = False
        for record in self :
            sender = record.sender_id
            recipients = record.recipients
            message =  record.message
        result = self.send_sms(sender,message,recipients)
        if result :
            self.write({'state':'sent'})
        return

    @api.multi
    def submit_reset_btn(self):
        self.write({'state':'draft'})
        return

    @api.v8
    def send_sms(self,sender,message,recipients):
        args = {}
        base_url = self.env.user.company_id.base_url

        username_key = self.env.user.company_id.username_key or False
        username_value = self.env.user.company_id.username_value or False
        if username_key and username_value :
            args.update({username_key:username_value})

        password_key = self.env.user.company_id.password_key or False
        password_value = self.env.user.company_id.password_value or False
        if password_key and password_value :
            args.update({password_key:password_value})

        message_key = self.env.user.company_id.message_key or False
        message_value  = message or False
        if message_key and message_value :
            args.update({message_key:message_value})

        sender_value = False
        sender_key = self.env.user.company_id.sender_key or False
        if sender :
            sender_value =  sender
        else :
            sender_value = self.env.user.company_id.sender_value or False

        if sender_key and sender_value :
            args.update({sender_key:sender_value})

        password_key = self.env.user.company_id.password_key
        password_value = self.env.user.company_id.password_value
        if password_key and password_value :
            args.update({password_key:password_value})

        recipients_key = self.env.user.company_id.recipients_key
        recipients_value = recipients
        if recipients_key and recipients_value :
            args.update({recipients_key:recipients_value})

        other_parameters  = self.env.user.company_id.other_parameter_ids
        for param in other_parameters :
            args.update({param.key:param.value})


        response = requests.get(base_url, params=args) # see http://docs.python-requests.org/en/master/user/quickstart/#passing-parameters-in-urls

        sms_log = self.env['sms.log']
        cr_id = sms_log.create({
            'response_reason': response.reason,
            'response_status_code': response.status_code,
            'date_log': fields.Date.context_today(self),
            'response_text': response.text,
            'sender_id': sender,
            'recipients': recipients,
            'txt_msg':message ,
            'compose_id': self.id
        })



        if response.reason == 'OK' :
            return True
        else :
            return False



class SMSLog(models.Model):

    _name = "sms.log"

    date_log = fields.Datetime(string="Date Log")
    sender_id = fields.Char(string="Sender")
    recipients = fields.Char(string="Recipients")
    txt_msg = fields.Char(string="Text Message")
    response_text = fields.Char(string="Response Message")
    response_status_code = fields.Char(string="Status Code")
    response_reason = fields.Char(string="Outcome")
    compose_id = fields.Many2one("sms.compose", string="Compose SMS")



class SmsParams(models.Model):
    _name = "sms.params"

    key = fields.Char(string="Name")
    value = fields.Char(string="Value")
    company_id = fields.Many2one("res.company", string="Company")


class Company(models.Model):
    _inherit = "res.company"

    base_url = fields.Char(string="Base URL")
    username_key = fields.Char(string="Username Name")
    username_value = fields.Char(string="Username Value")
    password_key = fields.Char(string="Password Name")
    password_value = fields.Char(string="Password Value")
    username_value = fields.Char(string="Username Value")
    message_key = fields.Char(string="Message Name")
    sender_key = fields.Char(string="Sender Name")
    sender_value = fields.Char(string="Sender Value")
    recipients_key = fields.Char(string="Recipients Name/Key")
    other_parameter_ids = fields.One2many('sms.params','company_id',string="Other Parameters", help="Please enter the name=value pair on the url string, except the parameters listed above")




class POS(models.Model):
    _inherit = "pos.order"

    @api.multi
    def action_paid(self):
        res = super(POS,self).action_paid()

        return True

