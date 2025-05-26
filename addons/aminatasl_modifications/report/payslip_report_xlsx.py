# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw
from datetime import datetime
from openerp.exceptions import UserError
from openerp import _

class PayrollReportWriter(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, objects):

        # lines = objects._get_payslip_report_data(data['form'])
        department_obj = self.env['hr.department']
        department_ids = data['form']['department_ids']

        salary_rule = self.env['hr.salary.rule']
        is_net_amount = salary_rule.search([('is_net_amount', '=', True)])
        if len(is_net_amount) != 1:
            raise UserError(_('Please set "Is Net Amount" on the configuration to only one salary rule'))

        if not department_ids:
            dept_obj = department_obj.search([])
            for dept in dept_obj:
                department_ids.append(dept.id)

        dept_ids = department_obj.search([('id', 'in', department_ids)])

        # the_date = datetime.today().strftime('%d %B %Y')
        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        user_company = self.env.user.company_id


        payslip_worksheet = workbook.add_worksheet(data['name'])
        header_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter','font_size':24})
        title_format = workbook.add_format({'bold': True,'underline':1, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        cell_wrap_format = workbook.add_format({'valign':'vjustify','font_size':10})
        cell_currency = workbook.add_format({'font_size': 10})
        cell_currency.set_num_format('#,#00.00')
        head_format = workbook.add_format({'bold':True})
        cell_total_currency = workbook.add_format({'bold':True})
        cell_total_currency.set_num_format('#,#00.00')
        cell_department_format = workbook.add_format({'bold': True, 'font_color': 'blue'})

        # Header Format
        payslip_worksheet.set_row(1, 30)
        payslip_worksheet.merge_range(1,1,1,6,user_company.name,header_format)

        #Title Format
        payslip_worksheet.set_row(2, 20)  # Set row height
        payslip_worksheet.merge_range(2, 1, 2, 6, 'Department Payroll Report from %s to %s '%(start_date,end_date), title_format)

        col = 0
        row = 2
        payslip_worksheet.set_column(1,1, 25,cell_wrap_format)  # set column width with wrap format.
        payslip_worksheet.set_column(2, 2, 20, cell_wrap_format)
        payslip_worksheet.set_column(3, 4, 18, cell_wrap_format)
        payslip_worksheet.set_row(row, 20)
        row += 2

        dict_srule = {}
        cc = 4

        payslip_worksheet.write(row, 0, 'S/N', head_format)
        payslip_worksheet.write(row, 1, 'Employee', head_format)
        payslip_worksheet.write(row, 2, 'Department', head_format)
        payslip_worksheet.write(row, 3, 'Bank Account No.', head_format)

        #this order = 'sequence asc'still works fine
        #salary_rules = self.env['hr.salary.rule'].search([('appears_on_payslip', '=', True)],order = 'sequence asc')

        salary_rules = self.env['hr.salary.rule'].search([('appears_on_payslip', '=', True)])
        salary_rules = salary_rules.sorted(key=lambda r: r.sequence, reverse=False)
        for salary_rule in salary_rules:
            dict_srule[cc] = salary_rule.name
            payslip_worksheet.write(row, cc, salary_rule.name, head_format)
            cc +=1

        row += 1
        sn_count = 0
        sn = 1
        total_net = 0

        for dept_id in dept_ids:
            employee_ids  = dept_id.member_ids
            total_dept_net = 0
            row += 1
            payslip_worksheet.write(row, 2, dept_id.name.upper(), cell_department_format)
            row += 1

            for employee in employee_ids:
                start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').strftime('%Y-%m-%d')
                end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').strftime('%Y-%m-%d')
                payslip_lines = self.env['hr.payslip.line'].search([('date_from', '>=', start_date), ('date_to', '<=', end_date),('employee_id','=',employee.id)])

                payslip_worksheet.write(row, col, sn, cell_wrap_format)
                payslip_worksheet.write(row, 1, employee.name, cell_wrap_format)
                payslip_worksheet.write(row, 2, dept_id.name, cell_wrap_format)
                payslip_worksheet.write(row, 3, employee.bank_account_id, cell_wrap_format)

                for line in payslip_lines:
                    if line.salary_rule_id.appears_on_payslip:
                        coln = dict_srule.keys()[dict_srule.values().index(line.salary_rule_id.name)] #see ref: https://stackoverflow.com/questions/8023306/get-key-by-value-in-dictionary
                        payslip_worksheet.write(row, coln, line.total, cell_currency)
                        if line.salary_rule_id.is_net_amount :
                            total_net += line.total
                            total_dept_net += line.total
                row += 1
                sn += 1
                sn_count += 1
            payslip_worksheet.write(row, cc-2, 'Department Net:', head_format)
            payslip_worksheet.write(row, cc-1, total_dept_net, cell_total_currency)
            row += 1

        row += 2
        payslip_worksheet.write(row, cc-2, 'TOTAL NET:', head_format)
        payslip_worksheet.write(row, cc-1, total_net, cell_total_currency)
        return

# The payslip.report.parser in the PayslipReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
PayrollReportWriter('report.aminatasl_modifications.report_payroll_report', 'payroll.report.parser',parser=report_sxw.rml_parse)


