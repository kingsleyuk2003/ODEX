# -*- coding: utf-8 -*-
from openerp import models, fields, api
from datetime import datetime

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def unlink(self):
        for loan_line in self.loan_ids:
            loan_line.paid = False
        return super(HrPayslip, self).unlink()

    @api.multi
    def compute_sheet(self):
        line_ids = self.get_loan()
        loan_line_ids = self.env['hr.loan.line'].browse(line_ids)
        if loan_line_ids:
            loan_lines = loan_line_ids.filtered(lambda line: datetime.strptime(line.date,'%Y-%m-%d').month == datetime.strptime(self.date_from,'%Y-%m-%d').month)
            for loan_line in loan_lines:
                loan_line.paid = True
        res = super(HrPayslip, self).compute_sheet()
        return res

    @api.one
    def compute_total_paid(self):
        """This compute the total paid amount of Loan.
            """
        total = 0.0
        for line in self.loan_ids:
            if line.paid:
                total += line.amount
        self.total_paid = total

    @api.multi
    def get_loan(self):
        """This gives the installment lines of an employee where the state is not in paid.
            """
        loan_list = []
        loan_ids = self.env['hr.loan.line'].search([('employee_id', '=', self.employee_id.id), ('paid', '=', False)])
        for loan in loan_ids:
            if loan.loan_id.state == 'approve':
                loan_list.append(loan.id)
        self.loan_ids = loan_list
        return loan_list

    @api.multi
    def action_payslip_done(self):
        loan_list = []
        for line in self.loan_ids:
            if line.paid:
                loan_list.append(line.id)
            else:
                line.payslip_id = False
        self.loan_ids = loan_list
        return super(HrPayslip, self).action_payslip_done()


    loan_ids = fields.One2many('hr.loan.line', 'payslip_id', string="Loans")
    total_paid = fields.Float(string="Total Loan Amount", compute='compute_total_paid')