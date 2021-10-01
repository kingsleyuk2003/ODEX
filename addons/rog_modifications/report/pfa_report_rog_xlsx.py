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

class PFAReportWriter(ReportXlsx):

    def _get_data(self, form):
        start_date = form['start_date']
        end_date = form['end_date']
        pfa_ids = form['pfa_ids']
        select_per = form['select_per']

        employee_pension_salary_rule_ids = []
        employer_pension_salary_rule_ids = []

        salary_rule = self.env['hr.salary.rule']
        is_employee_pension = salary_rule.search([('is_employee_pension', '=', True)])
        if not is_employee_pension:
            raise UserError(_('Please set "Is Employee Pension" on at least one salary rule'))
        else:
            for emp_pen in is_employee_pension:
                employee_pension_salary_rule_ids.append(emp_pen.id)

        is_employer_pension = salary_rule.search([('is_employer_pension', '=', True)])
        if not is_employer_pension:
            raise UserError(_('Please set "Is Employer Pension", on at least one salary rule'))
        else:
            for empy_pen in is_employer_pension:
                employer_pension_salary_rule_ids.append(empy_pen.id)

        if not pfa_ids:
            pfa_obj = self.env['hr.pfa'].search([])
            for pfa in pfa_obj:
                pfa_ids.append(pfa.id)

        if not start_date:
            start_date = ''

        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')

        total = False
        if select_per == '38':
            sql_statement = """
                            SELECT  *  FROM                
                                   (SELECT 
                                        sum(total) as employee_pension, hr_payslip.employee_id                     
                                    FROM hr_payslip_line
                                    INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                    INNER JOIN hr_payslip ON hr_payslip_line.slip_id = hr_payslip.id
                                    WHERE      
                                        hr_payslip_line.date_from >= %s
                                    AND 
                                        hr_payslip_line.date_to <= %s
                                        AND hr_payslip.hr_pfa_id in %s
            			            AND salary_rule_id in %s
                                    Group By hr_payslip.employee_id
                                     ) as t1

                                    INNER JOIN

                                        (SELECT 
                                                sum(total) as employer_pension, hr_payslip.employee_id , identification_id,name_related,  hr_payslip.company_id, hr_payslip_line.name,  hr_payslip_line.department_id, 
                                                   hr_payslip_line.date_from, hr_payslip_line.date_to, hr_payslip_line.hr_pfa_id, rsa, paye, hr_pfa.name as pfa_name, hr_pfa.code as pfa_code
                                              FROM hr_payslip_line
                                              INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                              INNER JOIN hr_payslip ON hr_payslip_line.slip_id = hr_payslip.id
                                              INNER JOIN hr_pfa ON hr_payslip.hr_pfa_id = hr_pfa.id                                  
                                              WHERE      
                                                   hr_payslip_line.date_from >= %s
                                                   AND hr_payslip_line.date_to <= %s
                                                   AND hr_payslip.hr_pfa_id in %s
                                                   AND salary_rule_id in %s
                                                   GROUP BY
                                                  hr_payslip.employee_id,identification_id, name_related,hr_payslip.company_id,  hr_payslip_line.name, hr_payslip_line.department_id, 
                                                   hr_payslip_line.date_from, hr_payslip_line.date_to, hr_payslip_line.hr_pfa_id, rsa, paye,pfa_name,pfa_code) as t2
                                    ON t1.employee_id = t2.employee_id 

                                    """
        elif select_per == '62':
            # total = total * '1.631578947'   # i.e  0.62 / 0.38  from, x = (total * 0.62) /  0.38
            sql_statement = """
                                        SELECT  *  FROM                
                                               (SELECT 
                                                    sum(total * 1.631578947) as employee_pension, hr_payslip.employee_id                     
                                                FROM hr_payslip_line
                                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                                INNER JOIN hr_payslip ON hr_payslip_line.slip_id = hr_payslip.id
                                                WHERE      
                                                    hr_payslip_line.date_from >= %s
                                                AND 
                                                    hr_payslip_line.date_to <= %s
                                                    AND hr_payslip.hr_pfa_id in %s
                        			            AND salary_rule_id in %s
                                                Group By hr_payslip.employee_id
                                                 ) as t1

                                                INNER JOIN

                                                    (SELECT 
                                                            sum(total * 1.631578947) as employer_pension, hr_payslip.employee_id , identification_id,name_related,  hr_payslip.company_id, hr_payslip_line.name,  hr_payslip_line.department_id, 
                                                               hr_payslip_line.date_from, hr_payslip_line.date_to, hr_payslip_line.hr_pfa_id, rsa, paye, hr_pfa.name as pfa_name, hr_pfa.code as pfa_code
                                                          FROM hr_payslip_line
                                                          INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                                          INNER JOIN hr_payslip ON hr_payslip_line.slip_id = hr_payslip.id
                                                          INNER JOIN hr_pfa ON hr_payslip.hr_pfa_id = hr_pfa.id                                  
                                                          WHERE      
                                                               hr_payslip_line.date_from >= %s
                                                               AND hr_payslip_line.date_to <= %s
                                                               AND hr_payslip.hr_pfa_id in %s
                                                               AND salary_rule_id in %s
                                                               GROUP BY
                                                              hr_payslip.employee_id,identification_id, name_related,hr_payslip.company_id,  hr_payslip_line.name, hr_payslip_line.department_id, 
                                                               hr_payslip_line.date_from, hr_payslip_line.date_to, hr_payslip_line.hr_pfa_id, rsa, paye,pfa_name,pfa_code) as t2
                                                ON t1.employee_id = t2.employee_id 

                                                """
        elif select_per == '100' :
           # total = total * 2.631578947
           sql_statement = """
                                        SELECT  *  FROM                
                                               (SELECT 
                                                    sum(total * 2.631578947) as employee_pension, hr_payslip.employee_id                     
                                                FROM hr_payslip_line
                                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                                INNER JOIN hr_payslip ON hr_payslip_line.slip_id = hr_payslip.id
                                                WHERE      
                                                    hr_payslip_line.date_from >= %s
                                                AND 
                                                    hr_payslip_line.date_to <= %s
                                                    AND hr_payslip.hr_pfa_id in %s
                        			            AND salary_rule_id in %s
                                                Group By hr_payslip.employee_id
                                                 ) as t1

                                                INNER JOIN

                                                    (SELECT 
                                                            sum(total * 2.631578947) as employer_pension, hr_payslip.employee_id , identification_id,name_related,  hr_payslip.company_id, hr_payslip_line.name,  hr_payslip_line.department_id, 
                                                               hr_payslip_line.date_from, hr_payslip_line.date_to, hr_payslip_line.hr_pfa_id, rsa, paye, hr_pfa.name as pfa_name, hr_pfa.code as pfa_code
                                                          FROM hr_payslip_line
                                                          INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                                          INNER JOIN hr_payslip ON hr_payslip_line.slip_id = hr_payslip.id
                                                          INNER JOIN hr_pfa ON hr_payslip.hr_pfa_id = hr_pfa.id                                  
                                                          WHERE      
                                                               hr_payslip_line.date_from >= %s
                                                               AND hr_payslip_line.date_to <= %s
                                                               AND hr_payslip.hr_pfa_id in %s
                                                               AND salary_rule_id in %s
                                                               GROUP BY
                                                              hr_payslip.employee_id,identification_id, name_related,hr_payslip.company_id,  hr_payslip_line.name, hr_payslip_line.department_id, 
                                                               hr_payslip_line.date_from, hr_payslip_line.date_to, hr_payslip_line.hr_pfa_id, rsa, paye,pfa_name,pfa_code) as t2
                                                ON t1.employee_id = t2.employee_id 

                                                """
        args = (start_date, end_date, tuple(pfa_ids), tuple(employee_pension_salary_rule_ids), start_date, end_date, tuple(pfa_ids), tuple(employer_pension_salary_rule_ids),)
        self.env.cr.execute(sql_statement, args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll


    def _get_data_gmd(self, form):
        start_date = form['start_date']
        end_date = form['end_date']
        pfa_ids = form['pfa_ids']
        select_per = form['select_per']

        employee_pension_salary_rule_ids = []
        employer_pension_salary_rule_ids = []

        salary_rule = self.env['hr.salary.rule']
        is_employee_pension = salary_rule.search([('is_employee_pension', '=', True)])
        if not is_employee_pension:
            raise UserError(_('Please set "Is Employee Pension" on at least one salary rule'))
        else:
            for emp_pen in is_employee_pension:
                employee_pension_salary_rule_ids.append(emp_pen.id)

        is_employer_pension = salary_rule.search([('is_employer_pension', '=', True)])
        if not is_employer_pension:
            raise UserError(_('Please set "Is Employer Pension", on at least one salary rule'))
        else:
            for empy_pen in is_employer_pension:
                employer_pension_salary_rule_ids.append(empy_pen.id)

        if not pfa_ids:
            pfa_obj = self.env['hr.pfa'].search([])
            for pfa in pfa_obj:
                pfa_ids.append(pfa.id)

        if not start_date:
            start_date = ''

        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')

        total = False
        sql_statement = """
                            SELECT  *  FROM                
                                   (SELECT 
                                        sum(total) as employee_pension, hr_payslip.employee_id                     
                                    FROM hr_payslip_line
                                    INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                    INNER JOIN hr_payslip ON hr_payslip_line.slip_id = hr_payslip.id
                                    WHERE      
                                        hr_payslip_line.date_from >= %s
                                    AND 
                                        hr_payslip_line.date_to <= %s
                                        AND hr_payslip.hr_pfa_id in %s
            			            AND salary_rule_id in %s
                                    Group By hr_payslip.employee_id
                                     ) as t1

                                    INNER JOIN

                                        (SELECT 
                                                sum(total) as employer_pension, hr_payslip.employee_id , identification_id,name_related,  hr_payslip.company_id, hr_payslip_line.name,  hr_payslip_line.department_id, 
                                                   hr_payslip_line.date_from, hr_payslip_line.date_to, hr_payslip_line.hr_pfa_id, rsa, paye, hr_pfa.name as pfa_name, hr_pfa.code as pfa_code
                                              FROM hr_payslip_line
                                              INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                              INNER JOIN hr_payslip ON hr_payslip_line.slip_id = hr_payslip.id
                                              INNER JOIN hr_pfa ON hr_payslip.hr_pfa_id = hr_pfa.id                                  
                                              WHERE      
                                                   hr_payslip_line.date_from >= %s
                                                   AND hr_payslip_line.date_to <= %s
                                                   AND hr_payslip.hr_pfa_id in %s
                                                   AND salary_rule_id in %s
                                                   GROUP BY
                                                  hr_payslip.employee_id,identification_id, name_related,hr_payslip.company_id,  hr_payslip_line.name, hr_payslip_line.department_id, 
                                                   hr_payslip_line.date_from, hr_payslip_line.date_to, hr_payslip_line.hr_pfa_id, rsa, paye,pfa_name,pfa_code) as t2
                                    ON t1.employee_id = t2.employee_id 
                            WHERE identification_id = '001'
                                    """

        args = (start_date, end_date, tuple(pfa_ids), tuple(employee_pension_salary_rule_ids), start_date, end_date, tuple(pfa_ids), tuple(employer_pension_salary_rule_ids),)
        self.env.cr.execute(sql_statement, args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll


    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        slist_dicts = self._get_data(data['form'])

        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')


        report_worksheet = workbook.add_worksheet('PFA Pension Report')
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 24})
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        head_format = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10,'bg_color':'blue','color':'white'})
        head_format.set_num_format('#,#00.00')
        head_format_total = workbook.add_format({'bold': True, 'border': 1,'font_size': 10})
        head_sub_format_indent1 = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        head_sub_format_indent1.set_indent(1)
        cell_total_description = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_wrap_format = workbook.add_format({'valign': 'vjustify', 'font_size': 10, 'border': 1})
        cell_amount = workbook.add_format({'border': 1, 'font_size': 10})
        cell_amount.set_num_format('#,#00.00')
        cell_total_currency = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_total_currency.set_num_format('#,#00.00')

        # Header Format
        report_worksheet.set_row(0, 30)  # Set row height
        report_worksheet.merge_range(0, 0, 0, 10, user_company.name, header_format)

        # Title Format
        report_worksheet.set_row(2, 20)
        report_worksheet.merge_range(2, 0, 2, 10, 'Staff Pension Fund Details', title_format)

        # Period
        report_worksheet.set_row(3, 20)
        if start_date and end_date:
            report_worksheet.merge_range(3, 0, 3, 10,
                                          'Between: ' + datetime.strptime(start_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y') + '  and ' + datetime.strptime(end_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y'), title_format)
        else:
            report_worksheet.merge_range(3, 0, 3, 10, 'All Period', title_format)

        col = 0
        row = 6
        report_worksheet.set_column(0,0,5)  # set column width with wrap format.
        report_worksheet.set_column(1,1,25)
        report_worksheet.set_column(2, 2, 15)
        report_worksheet.set_column(3, 3, 15)
        report_worksheet.set_column(4, 4, 15)
        report_worksheet.set_column(5, 5, 15)
        report_worksheet.set_column(6, 6, 15)
        report_worksheet.set_column(7, 7, 15)

        report_worksheet.write_row(row, col, ('S/N' , 'Employee Name',  'I.D No.' ,'PIN No.', 'Employee Amt.','Employer Amt.', 'Pension Arrears','Total') , head_format)

        pfa_obj = self.env['hr.pfa']
        hr_pfa_ids = data['form']['pfa_ids']

        if not hr_pfa_ids:
            search_pfa_obj = self.env['hr.pfa'].search([])
            for pfa in search_pfa_obj:
                hr_pfa_ids.append(pfa.id)
        pfa_ids = pfa_obj.search([('id', 'in', hr_pfa_ids)])

        left_title_format = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'font_size': 11})
        row += 1
        grand_total_amt = grand_total_emp_amt = grand_total_emply_amt = 0
        for pfa in pfa_ids:
            row +=1
            report_worksheet.merge_range(row, 0, row, 10, '%s                      %s' % (pfa.code,pfa.name), left_title_format)

            row +=1
            underline_cell_wrap_format = workbook.add_format({'valign': 'vjustify', 'underline': 1, 'font_size': 10, 'border': 1})
            report_worksheet.merge_range(row, 0, row, 10,  'PENSION CONTRIBUTION', underline_cell_wrap_format)

            row += 1
            total_amt = total_emp_amt = total_emply_amt = 0
            first_row = row
            sn = 0

            list_dicts = filter(lambda line: line['hr_pfa_id'] == pfa.id ,slist_dicts)  #reference: https://stackoverflow.com/a/25373204
            for list_dict in list_dicts:
                sn += 1
                if list_dict['identification_id'] == '001':
                    list_gmd_dicts = self._get_data_gmd(data['form'])
                    report_worksheet.write(row, 0, sn ,cell_wrap_format)
                    report_worksheet.write(row, 1, list_gmd_dicts[0]['name_related'], cell_wrap_format)
                    report_worksheet.write(row, 2, list_gmd_dicts[0]['identification_id'], cell_wrap_format)
                    report_worksheet.write(row, 3, list_gmd_dicts[0]['rsa'], cell_amount)
                    report_worksheet.write(row, 4, list_gmd_dicts[0]['employee_pension'], cell_amount)
                    report_worksheet.write(row, 5, list_gmd_dicts[0]['employer_pension'], cell_amount)
                    report_worksheet.write(row, 6, 0, cell_amount)
                    total = list_gmd_dicts[0]['employee_pension'] + list_gmd_dicts[0]['employer_pension']
                    report_worksheet.write(row, 7, total, cell_amount)
                    row += 1
                    total_amt += total
                    total_emp_amt += list_gmd_dicts[0]['employee_pension']
                    total_emply_amt += list_gmd_dicts[0]['employer_pension']
                else:
                    report_worksheet.write(row, 0, sn, cell_wrap_format)
                    report_worksheet.write(row, 1, list_dict['name_related'], cell_wrap_format)
                    report_worksheet.write(row, 2, list_dict['identification_id'], cell_wrap_format)
                    report_worksheet.write(row, 3, list_dict['rsa'], cell_amount)
                    report_worksheet.write(row, 4, list_dict['employee_pension'], cell_amount)
                    report_worksheet.write(row, 5, list_dict['employer_pension'], cell_amount)
                    report_worksheet.write(row, 6, 0, cell_amount)
                    total = list_dict['employee_pension'] + list_dict['employer_pension']
                    report_worksheet.write(row, 7, total, cell_amount)
                    row += 1
                    total_amt += total
                    total_emp_amt += list_dict['employee_pension']
                    total_emply_amt += list_dict['employer_pension']
            last_row = row
            report_worksheet.write(row, 3, 'PFA Total:', head_format_total)
            a1_notation_ref = xl_range(first_row, 4, last_row, 4)
            report_worksheet.write(row, 4, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_emp_amt)
            a1_notation_ref = xl_range(first_row, 5, last_row, 5)
            report_worksheet.write(row, 5, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_emply_amt)
            a1_notation_ref = xl_range(first_row, 7, last_row, 7)
            report_worksheet.write(row, 7, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_amt)
            row +=1
            grand_total_emp_amt += total_emp_amt
            grand_total_emply_amt += total_emply_amt
            grand_total_amt += total_amt
        row += 2
        report_worksheet.write(row, 3, 'Grand Total:', head_format_total)
        report_worksheet.write(row, 4, grand_total_emp_amt, cell_total_currency)
        report_worksheet.write(row, 5, grand_total_emply_amt, cell_total_currency)
        report_worksheet.write(row, 7, grand_total_amt, cell_total_currency)

# The purchase.report.wizard in the PurchaseReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
PFAReportWriter('report.rog_modifications.report_pfa_excel_rog','pfa.report.wizard',parser=report_sxw.rml_parse)


