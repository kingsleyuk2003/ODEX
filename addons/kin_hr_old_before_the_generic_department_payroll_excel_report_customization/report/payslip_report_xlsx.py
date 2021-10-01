# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw
from datetime import datetime


class PayslipReportWriter(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, objects):

        lines = objects._get_payslip_report_data(data['form'])
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
        cell_total_currency.set_num_format('#,#00.00')
        head_format = workbook.add_format({'bold':True})
        cell_department_format = workbook.add_format({'bold': True, 'font_color': 'blue'})

        # Header Format
        payslip_worksheet.set_row(1, 30)
        payslip_worksheet.merge_range(1,1,1,6,user_company.name,header_format)

        #Title Format
        payslip_worksheet.set_row(2, 20)  # Set row height
        payslip_worksheet.merge_range(2, 1, 2, 6, 'Payslip Report from %s to %s '%(start_date,end_date), title_format)

        col = 0
        row = 2
        payslip_worksheet.set_column(1,1, 25,cell_wrap_format)  # set column width with wrap format.
        payslip_worksheet.set_column(2, 2, 20, cell_wrap_format)
        payslip_worksheet.set_column(3, 4, 18, cell_wrap_format)
        payslip_worksheet.set_row(row, 20)
        row += 2
        payslip_worksheet.write_row(row, col, ('S/N', 'Employee', 'Department','Amount','Bank Account Number'), head_format)
        row += 1
        total_amount = 0

        for dept_id in dept_ids:
            total_dept_amount = 0
            row += 1
            payslip_worksheet.write(row, 2, dept_id.name.upper(), cell_department_format)
            row += 1
            sn = 1
            for line in lines:
                if  (line['dept_id'] == dept_id.id):
                    payslip_worksheet.write(row, col, sn, cell_wrap_format)
                    payslip_worksheet.write(row, 1, line['emp_name'], cell_wrap_format)
                    payslip_worksheet.write(row, 2, line['dep_name'], cell_wrap_format)
                    payslip_worksheet.write(row, 3, line['total_amount'], cell_total_currency)
                    payslip_worksheet.write(row, 4, line['bank_acc'], cell_wrap_format)
                    row += 1
                    sn += 1
                    total_amount  += line['total_amount']
                    total_dept_amount += line['total_amount']
            payslip_worksheet.write(row, 2, 'Dept. Amt', head_format)
            payslip_worksheet.write(row, 3, total_dept_amount, head_format)
            row += 1
        row += 2
        payslip_worksheet.write(row, 0, line['serial_no'], head_format)
        payslip_worksheet.write(row, 2, 'TOTAL AMOUNT', head_format)
        payslip_worksheet.write(row, 3, total_amount, head_format)
        return


# The payslip.report.parser in the PayslipReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
PayslipReportWriter('report.kin_hr.report_payslip_report', 'payslip.report.parser',parser=report_sxw.rml_parse)


