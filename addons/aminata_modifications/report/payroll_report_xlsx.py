# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw
from datetime import datetime


class PayrollReportWriter(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, objects):

        lines = objects._get_payroll_report_data(data['form'])
        department_obj = self.env['hr.department']
        department_ids = data['form']['department_ids']
        dept_ids = department_obj.search([('id', 'in', department_ids)])

        the_date = datetime.today().strftime('%d %B %Y')
        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        user_company = self.env.user.company_id


        payslip_worksheet = workbook.add_worksheet(data['name'])
        header_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter','font_size':24})
        title_format = workbook.add_format({'bold': True,'underline':1, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        cell_wrap_format = workbook.add_format({'valign':'vjustify','font_size':10})
        cell_total_currency = workbook.add_format({'font_size': 10})
        cell_total_currency.set_num_format('#,#0.00')
        head_format = workbook.add_format({'bold':True})
        cell_department_format = workbook.add_format({'bold': True, 'font_color': 'blue'})

        # Header Format
        payslip_worksheet.set_row(1, 30)
        payslip_worksheet.merge_range(1,2,1,7,user_company.name,header_format)

        #Title Format
        payslip_worksheet.set_row(2, 20)  # Set row height
        payslip_worksheet.merge_range(2, 2, 2, 7, 'Payroll Report from %s to %s '%(start_date,end_date), title_format)

        col = 0
        row = 2
        payslip_worksheet.set_column(1,1, 25,cell_wrap_format)  # set column width with wrap format.
        payslip_worksheet.set_column(2, 2, 20, cell_wrap_format)
        payslip_worksheet.set_column(3, 14, 18, cell_wrap_format)
        payslip_worksheet.set_row(row, 20)
        row += 2
        payslip_worksheet.write_row(row, col, ('S/N', 'Employee', 'Department','Basic Salary','Benefit','Taxable Gross','Income Tax','Employee 4% Contribution','Employer 6%','Salary Deduction','Net Pay','USD Net','LRD Net','Account USD.','Account LRD'), head_format)
        row += 1
        total_net_pay = 0

        for dept_id in dept_ids:
            row += 1
            payslip_worksheet.write(row, 3, dept_id.name.upper(), cell_department_format)
            row += 1
            count = 1

            for line in lines:
                if  (line['dept_id'] == dept_id.id):
                    payslip_worksheet.write(row, col, count, cell_wrap_format)
                    payslip_worksheet.write(row, 1, line['emp_name'], cell_wrap_format)
                    payslip_worksheet.write(row, 2, line['dep_name'], cell_wrap_format)
                    payslip_worksheet.write(row, 3, line['basic'], cell_total_currency)
                    payslip_worksheet.write(row, 4, line['benefit'], cell_total_currency)
                    payslip_worksheet.write(row, 5, line['taxable'], cell_total_currency)
                    payslip_worksheet.write(row, 6, line['income'], cell_total_currency)
                    payslip_worksheet.write(row, 7, line['employee'], cell_total_currency)
                    payslip_worksheet.write(row, 8, line['employer'], cell_total_currency)
                    payslip_worksheet.write(row, 9, line['deduction'], cell_total_currency)
                    payslip_worksheet.write(row, 10, line['net_pay'], cell_total_currency)
                    payslip_worksheet.write(row, 11, line['total_amt_usd'], cell_total_currency)
                    payslip_worksheet.write(row, 12, line['total_amt_lrd'], cell_total_currency)
                    payslip_worksheet.write(row, 13, line['bank_usd'], cell_wrap_format)
                    payslip_worksheet.write(row, 14, line['bank_lrd'], cell_wrap_format)
                    row += 1
                    count += 1
                    total_net_pay += line['net_pay']
        row += 1
        payslip_worksheet.write(row, 9, 'TOTAL NET PAY', head_format)
        payslip_worksheet.write(row, 10, total_net_pay, head_format)
        row += 4
        payslip_worksheet.write(row, 1, '_____________________', head_format)
        payslip_worksheet.write(row, 5, '_____________________', head_format)
        row +=1
        payslip_worksheet.write(row, 1, 'Aminata T. Sackor', head_format)
        payslip_worksheet.write(row, 5, 'Emmanuel T. Togba', head_format)
        row += 1
        payslip_worksheet.write(row, 1, 'GENERAL MANAGER', head_format)
        payslip_worksheet.write(row, 5, 'CHIEF EXECUTIVE OFFICER', head_format)

        return

PayrollReportWriter('report.aminata_modifications.report_payroll_report', 'payroll.report.parser',parser=report_sxw.rml_parse)



