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

class GeneralReportWriter(ReportXlsx):

    def _get_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        pfa_ids = form['pfa_ids']
        emp_ids = form['emp_ids']
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

        if not pfa_ids :
            pfa_obj = self.env['hr.pfa'].search([])
            for pfa in pfa_obj:
                pfa_ids.append(pfa.id)

        if not emp_ids :
            emp_obj = self.env['hr.employee'].search([('pfa_id','in',pfa_ids)], order="name desc")
            for emp in emp_obj:
                emp_ids.append(emp.id)

        if not start_date :
            start_date = ''

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        if select_per == '38':
            sql_statement = """
                    SELECT  *  FROM                
                               (SELECT 
                                    total as employee_pension, hr_payslip.employee_id                     
                                FROM hr_payslip_line
                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                INNER JOIN hr_payslip ON hr_payslip_line.slip_id = hr_payslip.id
                                WHERE      
                                    hr_payslip_line.date_from >= %s
                                AND 
                                    hr_payslip_line.date_to <= %s
                                    AND hr_payslip.hr_pfa_id in %s
                                AND salary_rule_id in %s
                                AND hr_payslip.employee_id  in %s
                                 ) as t1
    
                                INNER JOIN
    
                                    (SELECT 
                                            total as employer_pension, hr_payslip.employee_id , identification_id,name_related,  hr_payslip.company_id, hr_payslip_line.name,  hr_payslip_line.department_id, 
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
                                               AND hr_payslip.employee_id  in %s
                                               ) as t2
                                ON t1.employee_id = t2.employee_id 
                         
                        """
        elif select_per == '62':
            # total = total * '1.631578947'   # i.e  0.62 / 0.38  from, x = (total * 0.62) /  0.38
            sql_statement = """
                                SELECT  *  FROM                
                                           (SELECT 
                                                total * 1.631578947 as employee_pension, hr_payslip.employee_id                     
                                            FROM hr_payslip_line
                                            INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                            INNER JOIN hr_payslip ON hr_payslip_line.slip_id = hr_payslip.id
                                            WHERE      
                                                hr_payslip_line.date_from >= %s
                                            AND 
                                                hr_payslip_line.date_to <= %s
                                                AND hr_payslip.hr_pfa_id in %s
                                            AND salary_rule_id in %s
                                            AND hr_payslip.employee_id  in %s
                                             ) as t1

                                            INNER JOIN

                                                (SELECT 
                                                        total * 1.631578947 as employer_pension, hr_payslip.employee_id , identification_id,name_related,  hr_payslip.company_id, hr_payslip_line.name,  hr_payslip_line.department_id, 
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
                                                           AND hr_payslip.employee_id  in %s
                                                           ) as t2
                                            ON t1.employee_id = t2.employee_id 

                                    """
        elif select_per == '100' :
           # total = total * 2.631578947
           sql_statement = """
                                            SELECT  *  FROM                
                                                       (SELECT 
                                                            total * 2.631578947 as employee_pension, hr_payslip.employee_id                     
                                                        FROM hr_payslip_line
                                                        INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                                        INNER JOIN hr_payslip ON hr_payslip_line.slip_id = hr_payslip.id
                                                        WHERE      
                                                            hr_payslip_line.date_from >= %s
                                                        AND 
                                                            hr_payslip_line.date_to <= %s
                                                            AND hr_payslip.hr_pfa_id in %s
                                                        AND salary_rule_id in %s
                                                        AND hr_payslip.employee_id  in %s
                                                         ) as t1

                                                        INNER JOIN

                                                            (SELECT 
                                                                    total * 2.631578947 as employer_pension, hr_payslip.employee_id , identification_id,name_related,  hr_payslip.company_id, hr_payslip_line.name,  hr_payslip_line.department_id, 
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
                                                                       AND hr_payslip.employee_id  in %s
                                                                       ) as t2
                                                        ON t1.employee_id = t2.employee_id 

                                                """

        args = (
            start_date, end_date, tuple(pfa_ids), tuple(employee_pension_salary_rule_ids), tuple(emp_ids), start_date, end_date, tuple(pfa_ids),
            tuple(employer_pension_salary_rule_ids),tuple(emp_ids),)
        self.env.cr.execute(sql_statement, args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll

    def _get_data_gmd(self, form):
        start_date = form['start_date']
        end_date = form['end_date']
        pfa_ids = form['pfa_ids']
        emp_ids = form['emp_ids']
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

        if not emp_ids:
            emp_obj = self.env['hr.employee'].search([('pfa_id', 'in', pfa_ids)], order="name desc")
            for emp in emp_obj:
                emp_ids.append(emp.id)

        if not start_date:
            start_date = ''

        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')


        sql_statement = """
                    SELECT  *  FROM                
                               (SELECT 
                                    total as employee_pension, hr_payslip.employee_id                     
                                FROM hr_payslip_line
                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id 
                                INNER JOIN hr_payslip ON hr_payslip_line.slip_id = hr_payslip.id
                                WHERE      
                                    hr_payslip_line.date_from >= %s
                                AND 
                                    hr_payslip_line.date_to <= %s
                                    AND hr_payslip.hr_pfa_id in %s
                                AND salary_rule_id in %s
                                AND hr_payslip.employee_id  in %s
                                 ) as t1

                                INNER JOIN

                                    (SELECT 
                                            total as employer_pension, hr_payslip.employee_id , identification_id,name_related,  hr_payslip.company_id, hr_payslip_line.name,  hr_payslip_line.department_id, 
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
                                               AND hr_payslip.employee_id  in %s
                                               ) as t2
                                ON t1.employee_id = t2.employee_id 
                    WHERE identification_id = '001'
                        """


        args = (
            start_date, end_date, tuple(pfa_ids), tuple(employee_pension_salary_rule_ids), tuple(emp_ids), start_date,
            end_date, tuple(pfa_ids),
            tuple(employer_pension_salary_rule_ids), tuple(emp_ids),)
        self.env.cr.execute(sql_statement, args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll


    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        slist_dicts = self._get_data(data['form'])

        pfa_ids = data['form']['pfa_ids']
        if not pfa_ids :
            pfa_obj = self.env['hr.pfa'].search([])
            for pfa in pfa_obj:
                pfa_ids.append(pfa.id)

        emp_ids = data['form']['emp_ids']
        if not emp_ids:
            emp_obj = self.env['hr.employee'].search([('pfa_id', 'in', pfa_ids)], order="name desc")
            for emp in emp_obj:
                emp_ids.append(emp.id)

        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')

        report_worksheet = workbook.add_worksheet('General Format Pension Report')
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 24})
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        head_format = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10,'bg_color':'blue','color':'white'})
        head_format.set_num_format('#,#00.00')
        head_format_total = workbook.add_format({'bold': True, 'border': 1})
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
        report_worksheet.merge_range(0, 0, 0, 4, user_company.name, header_format)

        # Title Format
        report_worksheet.set_row(2, 20)
        report_worksheet.merge_range(2, 0, 2, 4, 'Staff Deduction/Contribution Details', title_format)

        # Period
        report_worksheet.set_row(3, 20)
        if start_date and end_date:
            report_worksheet.merge_range(3, 0, 3, 4,
                                          'Between ' + datetime.strptime(start_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y') + '  and ' + datetime.strptime(end_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y'), title_format)
        else:
            report_worksheet.merge_range(3, 0, 3, 4, 'All', title_format)

        col = 0
        row = 6
        report_worksheet.set_column(0,0,10)  # set column width with wrap format.
        report_worksheet.set_column(1,1,15)
        report_worksheet.set_column(2, 2, 15)
        report_worksheet.set_column(3, 3, 15)
        report_worksheet.set_column(4, 4, 15)

        report_worksheet.write_row(row, col, ('Period' ,'Employee Amt.','Employer Amt.', 'Total Contribution','Date') , head_format)
        left_title_format = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'font_size': 11})

        employees = self.env['hr.employee'].search([('id','in',emp_ids),('pfa_id','in',pfa_ids)], order="identification_id desc")
        for emp in employees:
            emp_iden_no = emp.identification_id
            emp_name = emp.name
            pfa_no = emp.rsa
            row += 1
            report_worksheet.merge_range(row, 0, row, 4, '%s                      %s     %s' % (emp_iden_no, emp_name,pfa_no), left_title_format)

            list_dicts = filter(lambda line: line['employee_id'] == emp.id, slist_dicts)  # reference: https://stackoverflow.com/a/25373204
            total_amt = total_emp_amt = total_emply_amt = 0
            first_row = row + 1
            for list_dict in list_dicts:
                row += 1
                if list_dict['identification_id'] == '001':
                    list_gmd_dicts = self._get_data_gmd(data['form'])
                    report_worksheet.write(row, 0, datetime.strptime(list_gmd_dicts[0]['date_to'], '%Y-%m-%d').strftime('%d-%B-%Y'), cell_wrap_format)
                    report_worksheet.write(row, 1, list_gmd_dicts[0]['employee_pension'], cell_amount)
                    report_worksheet.write(row, 2, list_gmd_dicts[0]['employer_pension'], cell_amount)
                    total = list_gmd_dicts[0]['employee_pension'] + list_gmd_dicts[0]['employer_pension']
                    report_worksheet.write(row, 3, total, cell_amount)
                    report_worksheet.write(row, 4, datetime.strptime(list_gmd_dicts[0]['date_to'], '%Y-%m-%d').strftime('%d-%B-%Y'), cell_wrap_format)
                    total_amt += total
                    total_emp_amt += list_gmd_dicts[0]['employee_pension']
                    total_emply_amt += list_gmd_dicts[0]['employer_pension']
                else:
                    report_worksheet.write(row, 0,
                                           datetime.strptime(list_dict['date_to'], '%Y-%m-%d').strftime('%d-%B-%Y'),
                                           cell_wrap_format)
                    report_worksheet.write(row, 1, list_dict['employee_pension'], cell_amount)
                    report_worksheet.write(row, 2, list_dict['employer_pension'], cell_amount)
                    total = list_dict['employee_pension'] + list_dict['employer_pension']
                    report_worksheet.write(row, 3, total, cell_amount)
                    report_worksheet.write(row, 4,
                                           datetime.strptime(list_dict['date_to'], '%Y-%m-%d').strftime('%d-%B-%Y'),
                                           cell_wrap_format)
                    total_amt += total
                    total_emp_amt += list_dict['employee_pension']
                    total_emply_amt += list_dict['employer_pension']
            last_row = row
            row += 1
            a1_notation_ref = xl_range(first_row, 1, last_row, 1)
            report_worksheet.write(row, 1, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_emp_amt)
            a1_notation_ref = xl_range(first_row, 2, last_row, 2)
            report_worksheet.write(row, 2, '=SUM(' + a1_notation_ref + ')', cell_total_currency,total_emply_amt )
            a1_notation_ref = xl_range(first_row, 3, last_row, 3)
            report_worksheet.write(row, 3, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_amt)

# The purchase.report.wizard in the PurchaseReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
GeneralReportWriter('report.rog_modifications.report_general_excel_rog','general.report.wizard',parser=report_sxw.rml_parse)


