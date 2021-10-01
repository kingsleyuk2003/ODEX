# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw
from datetime import datetime
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell
from openerp.exceptions import UserError
from openerp import  _

class PayeReportWriter(ReportXlsx):

    def _get_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']

        salary_rule = self.env['hr.salary.rule']
        is_paye = salary_rule.search([('is_paye', '=', True)])
        if len(is_paye) != 1:
            raise UserError(_('Please set "Is PAYE" on the configuration to only one salary rule'))

        if not start_date :
            start_date = ''

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        sql_statement = """        
                     SELECT 
                             total,identification_id as staff_id, name_related as emp_name ,paye            
                            FROM hr_payslip_line
                            INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id                            
                            WHERE      
                                hr_payslip_line.date_from >= %s
                            AND 
                                hr_payslip_line.date_to <= %s 
                             AND salary_rule_id = %s
                    """
        args = (start_date, end_date,is_paye.id,)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll


    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        list_dicts = self._get_data(data['form'])

        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')

        report_worksheet = workbook.add_worksheet('P.A.Y.E Report')
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 24})
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        head_format = workbook.add_format({'bold': True,  'font_size': 10})
        head_format.set_num_format('#,#00.00')
        head_sub_format_indent1 = workbook.add_format({'bold': True,  'font_size': 10})
        head_sub_format_indent1.set_indent(1)
        cell_total_description = workbook.add_format({'bold': True,  'font_size': 10})
        cell_wrap_format = workbook.add_format({'valign': 'vjustify', 'font_size': 10})
        cell_amount = workbook.add_format({ 'font_size': 10})
        cell_amount.set_num_format('#,#00.00')
        cell_amount_extend = workbook.add_format({ 'font_size': 10})
        cell_amount_extend.set_num_format('0')
        cell_total_currency = workbook.add_format({'bold': True,  'font_size': 10})
        cell_total_currency.set_num_format('#,#00.00')

        # Header Format
        report_worksheet.set_row(0, 30)  # Set row height
        report_worksheet.merge_range(0, 0, 0, 10, user_company.name, header_format)

        # Title Format
        report_worksheet.set_row(2, 20)
        report_worksheet.merge_range(2, 0, 2, 10, 'STAFF P.A.Y.E Details', title_format)

        # Period
        report_worksheet.set_row(3, 20)
        if start_date and end_date:
            report_worksheet.merge_range(3, 0, 3, 10,
                                          'Period: ' + datetime.strptime(start_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y') + '  to ' + datetime.strptime(end_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y'), title_format)
        else:
            report_worksheet.merge_range(3, 0, 3, 10, 'Period: All', title_format)

        col = 0
        row = 6
        report_worksheet.set_column(0,0,5)  # set column width with wrap format.
        report_worksheet.set_column(1,1,10)
        report_worksheet.set_column(2, 2, 30)
        report_worksheet.set_column(3, 3, 15)

        report_worksheet.write_row(row, col, ('S/N','Staff ID','Staff Name', 'P.A.Y.E ID', 'P.A.Y.E Amt') , head_format)

        row += 1
        sn = 0
        total = 0
        first_row = row
        for list_dict in list_dicts:
            sn += 1
            report_worksheet.write(row, 0, sn ,cell_wrap_format)
            report_worksheet.write(row, 1, list_dict['staff_id'], cell_wrap_format)
            report_worksheet.write(row, 2, list_dict['emp_name'], cell_wrap_format)
            report_worksheet.write(row, 3, list_dict['paye'], cell_wrap_format)
            report_worksheet.write(row, 4, list_dict['total'], cell_amount)
            total += list_dict['total']
            row += 1
        last_row = row
        report_worksheet.write(row, 3, 'TOTAL:', head_format)
        a1_notation_ref = xl_range(first_row, 4, last_row, 4)
        report_worksheet.write(row, 4, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total)

# The purchase.report.wizard in the PurchaseReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
PayeReportWriter('report.kin_hr.report_paye_excel','paye.report.wizard',parser=report_sxw.rml_parse)


