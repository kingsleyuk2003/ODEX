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

class BankAdviceReportWriter(ReportXlsx):



    def _get_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        select_per = form['select_per']
        section = form['section']

        salary_rule = self.env['hr.salary.rule']
        is_net_amount = salary_rule.search([('is_net_amount', '=', True)])
        if len(is_net_amount) != 1:
            raise UserError(_('Please set "Is Net Amount" on the configuration to only one salary rule'))

        if not start_date :
            start_date = ''

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        if select_per == '38':
            sql_statement = """        
                         SELECT 
                                 total,employee_id, section, name_related as emp_name, beneficiary_code,company_id,res_company.company_account_number, hr_payslip_line.name, bank_id, hr_bank.name as bank_name ,  bank_account_id,bank_branch,bank_routing_code,bank_account_type                     
                                FROM hr_payslip_line
                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                INNER JOIN hr_bank ON hr_employee.bank_id = hr_bank.id
                                INNER JOIN res_company ON hr_payslip_line.company_id = res_company.id
                                WHERE      
                                    hr_payslip_line.date_from >= %s
                                AND 
                                    hr_payslip_line.date_to <= %s 
                                 AND salary_rule_id = %s
                                 AND section = %s
                        """
        elif select_per == '62':
            # total = total * '1.631578947'   # i.e  0.62 / 0.38  from, x = (total * 0.62) /  0.38
            sql_statement = """        
                                         SELECT 
                                                 (total * 1.631578947) total,employee_id, section, name_related as emp_name, beneficiary_code,company_id,res_company.company_account_number, hr_payslip_line.name, bank_id, hr_bank.name as bank_name ,  bank_account_id,bank_branch,bank_routing_code,bank_account_type                     
                                                FROM hr_payslip_line
                                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                                INNER JOIN hr_bank ON hr_employee.bank_id = hr_bank.id
                                                INNER JOIN res_company ON hr_payslip_line.company_id = res_company.id
                                                WHERE      
                                                    hr_payslip_line.date_from >= %s
                                                AND 
                                                    hr_payslip_line.date_to <= %s 
                                                 AND salary_rule_id = %s
                                                  AND section = %s
                                        """
        elif select_per == '100' :
           # total = total * 2.631578947
            sql_statement = """        
                                                     SELECT 
                                                             (total * 2.631578947) total,employee_id, section, name_related as emp_name, beneficiary_code,company_id,res_company.company_account_number, hr_payslip_line.name, bank_id, hr_bank.name as bank_name ,  bank_account_id,bank_branch,bank_routing_code,bank_account_type                     
                                                            FROM hr_payslip_line
                                                            INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                                            INNER JOIN hr_bank ON hr_employee.bank_id = hr_bank.id
                                                            INNER JOIN res_company ON hr_payslip_line.company_id = res_company.id
                                                            WHERE      
                                                                hr_payslip_line.date_from >= %s
                                                            AND 
                                                                hr_payslip_line.date_to <= %s 
                                                             AND salary_rule_id = %s
                                                              AND section = %s
                                                    """
        args = (start_date, end_date,is_net_amount.id,section,)
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

        report_worksheet = workbook.add_worksheet('Bank Advice Report')
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

        # # Header Format
        # report_worksheet.set_row(0, 30)  # Set row height
        # report_worksheet.merge_range(0, 0, 0, 10, user_company.name, header_format)
        #
        # # Title Format
        # report_worksheet.set_row(2, 20)
        # report_worksheet.merge_range(2, 0, 2, 10, 'Bank Payment Advice Report', title_format)
        #
        # # Period
        # report_worksheet.set_row(3, 20)
        # if start_date and end_date:
        #     report_worksheet.merge_range(3, 0, 3, 10,
        #                                   'Period: ' + datetime.strptime(start_date, '%Y-%m-%d').strftime(
        #                                       '%d/%m/%Y') + '  to ' + datetime.strptime(end_date, '%Y-%m-%d').strftime(
        #                                       '%d/%m/%Y'), title_format)
        # else:
        #     report_worksheet.merge_range(3, 0, 3, 10, 'Period: All', title_format)

        col = 0
        row = 0
        report_worksheet.set_column(0,0,25)  # set column width with wrap format.
        report_worksheet.set_column(1,1,15)
        report_worksheet.set_column(2, 2, 15)
        report_worksheet.set_column(3, 3, 15)
        report_worksheet.set_column(4, 4, 30)
        #report_worksheet.set_column(5, 5, 15)
        #report_worksheet.set_column(6, 6, 15)
        #report_worksheet.set_column(7, 7, 30)

        report_worksheet.write_row(row, col, ('Employee', 'Bank Code','Account no',  'Amount','Narration') , head_format)

        narration_date = datetime.strptime(end_date, '%Y-%m-%d')
        # month_cap = ''
        # mmm = [x.capitalize() for x in narration_date.strftime('%b')]
        # for m in mmm:
        #     month_cap += m

        month = narration_date.strftime('%B')
        year = narration_date.strftime('%Y')


        row += 1
        total_amt = 0
        first_row = row
        sn = 0



        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        select_per = data['form']['select_per']
        section = data['form']['section']

        salary_rule = self.env['hr.salary.rule']
        is_net_amount = salary_rule.search([('is_net_amount', '=', True)])
        if len(is_net_amount) != 1:
            raise UserError(_('Please set "Is Net Amount" on the configuration to only one salary rule'))

        if not start_date:
            start_date = ''

        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')

        for list_dict in list_dicts:
            sn += 1
            #tran_ref = 'SAL_%s_%s_%s' % (month_cap, year, sn)
            #report_worksheet.write(row, 0, tran_ref ,cell_wrap_format)
            report_worksheet.write(row, 0, list_dict['emp_name'].replace(',',''), cell_wrap_format)
            report_worksheet.write(row, 1, list_dict['bank_routing_code'], cell_wrap_format)
            report_worksheet.write(row, 2, list_dict['bank_account_id'], cell_wrap_format)

            # to get the amount field
            additions = 0
            deductions = 0
            payslip_lines = self.env['hr.payslip.line'].search([('date_from', '>=', start_date), ('date_to', '<=', end_date),('employee_id', '=', list_dict['employee_id'])])
            for line in payslip_lines:
                if select_per == '38':
                    if line.slip_id.struct_id.name not in ('GMD', 'RETAIL'):
                        if line.salary_rule_id.is_net_amount:
                            report_worksheet.write(row, 3, line.total, cell_amount_extend)
                elif select_per == '62':
                    if line.salary_rule_id.code != 'PAYE':
                        if line.slip_id.struct_id.name not in ('GMD', 'RETAIL'):
                            if line.salary_rule_id.code not in ( 'LO', 'SAR', 'lieo', 'lwp', 'absent', 'absent_refund', 'lwpr_refund', 'lieo_refund','other_refund', 'reward'):
                                if line.salary_rule_id.is_addition:
                                    additions += line.total * 1.631578947
                                if line.salary_rule_id.is_deduction:
                                    deductions += line.total * 1.631578947
                    if line.salary_rule_id.is_net_amount:
                        report_worksheet.write(row, 3, additions - deductions, cell_amount_extend)
                elif select_per == '100':
                    if line.salary_rule_id.code == 'PAYE':
                        deductions += line.total
                    if line.salary_rule_id.code != 'PAYE':
                        if line.slip_id.struct_id.name not in ('GMD', 'RETAIL'):
                            if line.salary_rule_id.code in ('LO', 'SAR', 'lieo', 'lwp', 'absent', 'absent_refund', 'lwpr_refund', 'lieo_refund', 'other_refund', 'reward'):
                                if line.salary_rule_id.is_addition:
                                    additions += line.total
                                if line.salary_rule_id.is_deduction:
                                    deductions += line.total
                            else:
                                if line.salary_rule_id.is_addition:
                                    additions += line.total * 2.631578947
                                if line.salary_rule_id.is_deduction:
                                    deductions += line.total * 2.631578947
                        else:
                            if line.salary_rule_id.is_addition:
                                additions += line.total
                            if line.salary_rule_id.is_deduction:
                                deductions += line.total
                    if line.salary_rule_id.is_net_amount:
                        report_worksheet.write(row, 3, additions - deductions, cell_amount_extend)

            report_worksheet.write(row, 4, month + ' ' + year + ' Salary', cell_wrap_format)
           #report_worksheet.write(row, 3,  pay_date.strftime('%d/%m/%Y'), cell_wrap_format)
           #report_worksheet.write(row, 4, list_dict['beneficiary_code'], cell_wrap_format)


            #report_worksheet.write(row, 7, list_dict['company_account_number'], cell_wrap_format)
            row += 1

# The purchase.report.wizard in the PurchaseReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
BankAdviceReportWriter('report.rog_modifications.report_bank_advice_excel_rog','bank.advice.report.wizard',parser=report_sxw.rml_parse)


