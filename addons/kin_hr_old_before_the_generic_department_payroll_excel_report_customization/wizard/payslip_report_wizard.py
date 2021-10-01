# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api


class PayslipReportWizard(models.TransientModel):
    _name = 'payroll.report.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }

    @api.multi
    def payslip_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0] #converts all objects to lists that can be easily be passed to the report
        data = {'name': 'Payslip Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'start_date' : wiz_data['start_date'],'end_date':wiz_data['end_date'],'department_ids':wiz_data['department_ids'],'rule_id' : wiz_data['rule_id']}
        return  {
                    'name':'Payslip Report',
                    'type': 'ir.actions.report.xml',
                    'report_name': 'kin_hr.report_payslip_report',
                    'datas':data, #It is required you use datas as parameter, otherwise it will transfer data correctly.

                }


    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    rule_id = fields.Many2one('hr.salary.rule', string='Salary Rule')
    department_ids = fields.Many2many('hr.department', 'hr_department_rel', 'payslip_wiz_id', 'dept_id', string='Departments', required=True)
    # employee_ids = fields.Many2many('hr.employee', 'hr_employee_rel', 'payslip_wiz_id', 'emp_id', string='Employees', required=True)





