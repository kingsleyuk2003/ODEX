# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from openerp import api, fields, models, _
from datetime import datetime, timedelta

class SchoolAttended(models.Model):
    _name = 'school.attended'

    name = fields.Char('Name of Institution')
    school_location = fields.Char('School Location')

class QualificationTitle(models.Model):
    _name = 'qualification.title'

    name = fields.Char('Qualification Title')
    description = fields.Char(string='Description')



class Qualification(models.Model):
    _name = 'qualification'

    qualification_title_id = fields.Many2one('qualification.title',string='Title')
    school_id = fields.Many2one('school.attended',string='Name of Institution')
    qualification_year = fields.Char(string='Qualification Year')
    employee_id = fields.Many2one('hr.employee', string='Employee')



class Guarantor(models.Model):
    _name = 'guarantor'

    name = fields.Char('Guarantor Name')
    gua_phone = fields.Char('Guarantor Phone No.')
    gua_address = fields.Char('Guarantor Address')
    employee_id = fields.Many2one('hr.employee',string='Employee')



class NOKRelationship(models.Model):
    _name = 'nok.relationship'

    name = fields.Char('Next of Kin Relationship')

class hrExtend(models.Model):
    _inherit = 'hr.employee'

    firstname = fields.Char(string='First Name')
    lastname = fields.Char(string='Last Name')
    middlename = fields.Char(string='Middle Name')
    state_id = fields.Many2one('res.country.state',string='State of Origin')
    next_of_kin = fields.Char('Next of Kin')
    nok_phone = fields.Char('Next of Kin Phone No.')
    nok_relationship = fields.Many2one('nok.relationship', help='Next of Kin Relationship')
    emergency_contact = fields.Char(string='Emergency Contact')
    emergency_contact_phone = fields.Char(string='Emergency Contact Phone')
    employment_date = fields.Date('Employment Date')
    employment_status = fields.Selection([('confirmed', 'Confirmed'), ('probation', 'Probation')], string='Employment Status')
    guarantor_ids = fields.One2many('guarantor','employee_id', string='Guarantor(s)')
    qualification_ids = fields.One2many('qualification', 'employee_id', string='Qualification(s)')
    personal_email = fields.Char(string='Personal Email')
    personal_mobile = fields.Char(related='user_id.mobile',string='Personal Mobile')
    bank_account_id = fields.Char(string='Bank Account Number')



class HRPayslipExtend(models.Model):
    _inherit = 'hr.payslip'

    @api.model
    def message_get_reply_to(self, res_ids, default=None):
        mail_thread = self.env['mail.thread']
        res = mail_thread.message_get_reply_to(res_ids, default=default) #default gets its value from the email_from field in the mail.template and NOT from the reply_to field. Already tested and confirmed
        # you may return a different reply to. e.g. {3:'king@yahoo.com'}. The 3 key is compulsory. NOT any other number apart from the 3 key.
        return res

    @api.multi
    def action_email_payslip(self):
        self.ensure_one()
        template = self.env.ref('kin_hr.mail_templ_payslip_email', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)

        #helps pass variables from this code to the rendered view
        #The default prefix tells odoo to set the passed variables as default values in the rendered view
        ctx = dict(
            default_model='hr.payslip',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
        )
        #Rendering a window with its view
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def send_mass_email_payslip(self):
        company_email = self.env.user.company_id.email.strip()
        sender_person_email = self.env.user.partner_id.email.strip()

        for payslip in self:
            emp_email = payslip.employee_id.user_id and payslip.employee_id.user_id.email and payslip.employee_id.user_id.email.strip() or False

            if company_email and sender_person_email and emp_email:
                mail_template = payslip.env.ref('kin_hr.mail_templ_payslip_email')
                mail_template.send_mail(payslip.id, force_send=False)

        return

    department_id = fields.Many2one('hr.department',related='employee_id.department_id',store=True,string='Department')


class HRPaySlipRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.multi
    def close_payslip_run(self):
        self.slip_ids.compute_sheet()
        return super(HRPaySlipRun,self).close_payslip_run()


    @api.multi
    def action_send_mass_payslip(self):
        self.slip_ids.send_mass_email_payslip()
        return












