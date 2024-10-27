# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2005-2006 Axelor SARL. (http://www.axelor.com)
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from openerp import api, fields, models, _
from openerp.exceptions import UserError
from openerp.tools import float_compare, float_is_zero
from datetime import datetime, timedelta


class HRBank(models.Model):
    _name = 'hr.bank'

    name = fields.Char(string='Bank')


class PFA(models.Model):
    _name = 'hr.pfa'

    name = fields.Char(string='PFA')
    code = fields.Char(string='PFA Code')


class ExitMode(models.Model):
    _name = 'hr.exit.mode'

    name = fields.Char(string='Name')


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
    exit_date = fields.Date('Exit Date')
    exit_mode_id = fields.Many2one('hr.exit.mode',string='Exit Mode')
    employment_status = fields.Selection([('confirmed', 'Confirmed'), ('probation', 'Probation')], string='Employment Status')
    guarantor_ids = fields.One2many('guarantor','employee_id', string='Guarantor(s)')
    qualification_ids = fields.One2many('qualification', 'employee_id', string='Qualification(s)')
    personal_email = fields.Char(string='Personal Email')
    personal_mobile = fields.Char(related='user_id.mobile',string='Personal Mobile')
    bank_account_id = fields.Char(string='Bank Account Number')
    bank_id = fields.Many2one('hr.bank',string='Bank')
    bank_branch = fields.Char(string='Bank Branch')
    bank_routing_code = fields.Char(string='Routing Bank Code')
    beneficiary_code = fields.Char(string='Beneficiary Code')
    bank_account_type = fields.Selection([('savings', 'Savings'), ('current', 'Current'),('corporate', 'Corporate')], string='Bank Account Type')
    pfa_id = fields.Many2one('hr.pfa', string='PFA')
    rsa = fields.Char(string='RSA')
    paye = fields.Char(string='P.A.Y.E I.D')




class HRPayslipExtend(models.Model):
    _inherit = 'hr.payslip'




    @api.onchange('employee_id')
    def onchange_kin_hr_employee_id(self):
        employee = self.employee_id
        self.update({
                'hr_pfa_id': employee.pfa_id
            })




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



    def process_sheet(self, cr, uid, ids, context=None):
        move_pool = self.pool.get('account.move')
        hr_payslip_line_pool = self.pool['hr.payslip.line']
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Payroll')

        for slip in self.browse(cr, uid, ids, context=context):
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to
            if not slip.employee_id.user_id :
                raise UserError(_('Please contact the HR manager or Admin to link the employee to a user'))

            partner_id = slip.employee_id.user_id.partner_id

            name = _('Payslip of %s') % (slip.employee_id.name)
            move = {
                'narration': name,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'date': date,
                'partner_id' : partner_id.id,
            }
            for line in slip.details_by_salary_rule_category:
                amt = slip.credit_note and -line.total or line.total
                if float_is_zero(amt, precision_digits=precision):
                    continue
                debit_account_id = line.salary_rule_id.account_debit.id
                credit_account_id = line.salary_rule_id.account_credit.id

                if debit_account_id:
                    debit_line = (0, 0, {
                        'name': line.name,
                    'partner_id': hr_payslip_line_pool._get_partner_id(cr, uid, line, credit_account=False, context=context),
                        'account_id': debit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amt > 0.0 and amt or 0.0,
                        'credit': amt < 0.0 and -amt or 0.0,
                        'partner_id': partner_id.id,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
                        'tax_line_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                    })
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

                if credit_account_id:
                    credit_line = (0, 0, {
                        'name': line.name,
                        'partner_id': hr_payslip_line_pool._get_partner_id(cr, uid, line, credit_account=True, context=context),
                        'account_id': credit_account_id,
                        'journal_id': slip.journal_id.id,
                        'date': date,
                        'debit': amt < 0.0 and -amt or 0.0,
                        'credit': amt > 0.0 and amt or 0.0,
                        'partner_id': partner_id.id,
                        'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
                        'tax_line_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
                    })
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_credit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (slip.journal_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                    'partner_id': partner_id.id,
                })
                line_ids.append(adjust_credit)

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                acc_id = slip.journal_id.default_debit_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (slip.journal_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'partner_id': False,
                    'account_id': acc_id,
                    'journal_id': slip.journal_id.id,
                    'date': date,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                    'partner_id': partner_id.id,
                })
                line_ids.append(adjust_debit)

            move.update({'line_ids': line_ids})
            move_id = move_pool.create(cr, uid, move, context=context)
            self.write(cr, uid, [slip.id], {'move_id': move_id, 'date' : date}, context=context)
            move_pool.post(cr, uid, [move_id], context=context)
        return

    department_id = fields.Many2one('hr.department',related='employee_id.department_id',store=True,string='Department')
    hr_pfa_id = fields.Many2one('hr.pfa', string='PFA')

class HRPaySlipRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.multi
    def confirm_payslip_run(self):
        for slip in self.slip_ids:
            if slip.state == 'done':
                raise UserError('Sorry, Some payslips may have been confirmed and done. you cannot confirm these batch')
            slip.process_sheet()
        self.state = 'done'
        return

    @api.multi
    def close_payslip_run(self):
        self.slip_ids.compute_sheet()
        return super(HRPaySlipRun,self).close_payslip_run()


    @api.multi
    def action_send_mass_payslip(self):
        self.slip_ids.send_mass_email_payslip()
        return

    @api.multi
    def unlink(self):
        for slip in self.slip_ids:
            if self.state != 'draft' :
                raise UserError(_('Please Reset this Payslip Batch to Draft State, by clicking the "Set to Draft" button, before deletion'))
            if slip.state != 'draft':
                raise UserError(_('You cannot delete a payslip that is not in draft state. Reset the payslip to draft state and try deleting it'))
            slip.unlink()
        return super(HRPaySlipRun, self).unlink()

    state = fields.Selection(selection_add=[('done', 'Done')])


class HRPaylipLine(models.Model):
    _inherit = 'hr.payslip.line'

    department_id = fields.Many2one('hr.department', related='slip_id.department_id', store=True,string='Department')
    hr_pfa_id = fields.Many2one(related='slip_id.hr_pfa_id', store=True)
    date_from = fields.Date(related='slip_id.date_from', store=True)
    date_to = fields.Date(related='slip_id.date_to', store=True)



class HRSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_employee_pension = fields.Boolean(string='Is Employee Pension')
    is_employer_pension = fields.Boolean(string='Is Employer Pension')
    is_net_amount = fields.Boolean(string='Is Net Amount')
    is_paye = fields.Boolean(string='Is P.A.Y.E')



class ResCompany(models.Model):
    _inherit = "res.company"

    company_account_number = fields.Char(string='Company Debit Account Number ')


class HRHolidays(models.Model):
    _inherit = 'hr.holidays'

    def _check_state_access_right(self, cr, uid, vals, context=None):
        if vals.get('state') and vals['state'] not in ['draft', 'confirm', 'cancel'] and not self.pool['res.users'].has_group(cr, uid, 'base.group_user'):
            return False
        return True

    @api.model
    def create(self, vals):
        res = super(HRHolidays,self).create(vals)
        res.signal_workflow('reset')
        return res

    # state = fields.Selection( default='draft')  #It still does not give the desired resuult because the workflow confirms it from draft state, so the best option is to incorporate it inside the create()


