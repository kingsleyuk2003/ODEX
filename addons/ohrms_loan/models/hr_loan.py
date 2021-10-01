# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.exceptions import except_orm
from openerp.exceptions import UserError, ValidationError
from openerp.tools.float_utils import float_compare

class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Loan Request"

    @api.one
    def _compute_loan_amount(self):
        total_paid = 0.0
        for loan in self:
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            total_paid +=  self.total_cash
            balance_amount = loan.loan_amount - total_paid
            self.total_amount = loan.loan_amount
            self.balance_amount = balance_amount
            self.total_paid_amount = total_paid

    name = fields.Char(string="Loan Name", default="/", readonly=True)
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department")
    installment = fields.Integer(string="No Of Installments", default=1)
    payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today())
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    emp_account_id = fields.Many2one('account.account', string="Employee Loan Receivable Account")
    treasury_account_id = fields.Many2one('account.account', string="Treasury Account")
    journal_id = fields.Many2one('account.journal', string="Journal")
    company_id = fields.Many2one('res.company', 'Company', readonly=True,
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
    loan_amount = fields.Float(string="Loan Amount", required=True)
    total_amount = fields.Float(string="Total Amount", readonly=True, compute='_compute_loan_amount')
    balance_amount = fields.Float(string="Balance Amount", compute='_compute_loan_amount')
    total_paid_amount = fields.Float(string="Total Paid Amount", compute='_compute_loan_amount')
    total_cash = fields.Float(string='Total Cash Collected From Account')
    loan_disapprove_msg = fields.Text(string='Dis-approved Reason')
    loan_disapprove_by = fields.Many2one('res.users', string='Dis-approved By')
    loan_disapprove_date = fields.Datetime(string='Dis-approved Date and Time')


    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('waiting_approval_2', 'Waiting Approval'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )

    @api.model
    def create(self, values):
        loan_count = self.env['hr.loan'].search_count([('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
                                                       ('balance_amount', '!=', 0)])
        if False: # changed from loan_count to False by Kingsley
            raise except_orm('Error!', 'The employee has already a pending installment')
        else:
            values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
            res = super(HrLoan, self).create(values)
            return res

    @api.multi
    def action_refuse(self,msg):
        self.loan_disapprove_by = self.env.user
        self.loan_disapprove_date = datetime.today()
        self.loan_disapprove_msg = msg
        # send email
        partn_ids = []
        user_names = ''
        loan_user = self.employee_id.user_id
        mesg = 'The Loan Request (%s), has been Dis-approved by %s with reason: (%s)' % (
            self.name,  self.env.user.name, msg)

        if loan_user:
            user_names += loan_user.name
            partn_ids.append(loan_user.partner_id.id)

        if partn_ids:
            self.message_post(
                _(mesg),
                subject='%s' % mesg, partner_ids=partn_ids)

        self.env.user.notify_info('%s Will Be Notified by Email' % (user_names))

        return self.write({'state': 'refuse'})



    @api.multi
    def action_submit(self):
        total_amt = 0
        for line in self.loan_lines:  # added by Kingsley
            total_amt += line.amount
        if float_compare(total_amt , self.loan_amount,precision_digits=2) != 0: # added by Kingsley
            raise UserError('Loan Amount is not equals to the total Loan Lines amount. Please click the compute installment button')
        self.write({'state': 'waiting_approval_1'})

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def action_approve(self):
        total_amt = 0
        for line in self.loan_lines:  # added by Kingsley
            total_amt += line.amount
        if float_compare(total_amt, self.loan_amount, precision_digits=2) != 0:  # added by Kingsley
            raise UserError('Loan Amount is not equals to the total Loan Lines amount. Please click the compute installment button')
        self.write({'state': 'approve'})

    @api.multi
    def btn_reset(self):
        self.state = 'draft'

    @api.multi
    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        self.loan_lines.unlink()
        for loan in self:
            date_start = datetime.strptime(loan.payment_date, '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment
            for i in range(1, loan.installment + 1):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                date_start = date_start + relativedelta(months=1)
        return True


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"



    date = fields.Date(string="Payment Date", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    amount = fields.Float(string="Amount", required=True)
    paid = fields.Boolean(string="Paid")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    @api.one
    def _compute_employee_loans(self):
        """This compute the loan amount and total loans count of an employee.
            """
        self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])

    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')


