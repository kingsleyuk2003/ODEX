# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api

class PayrollReportParser(models.TransientModel):

    _inherit = 'payroll.report.parser'

    def _get_payroll_report_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        department_ids = form['department_ids']

        sql_statement = """
                     SELECT
                        hr_employee.name_related as emp_name,
                        hr_salary_rule.name as rule_name,
                        hr_department.name as dep_name,
                        hr_department.id as dept_id,
                        hr_employee.bank_account_number_usd as bank_usd,
                        hr_employee.bank_account_number_lrd as bank_lrd,
                        sum(table2.total_amount) as basic,
                        sum(table3.total_amount) as benefit,
                        sum(table4.total_amount) as taxable,
                        sum(table5.total_amount) as income,
                        sum(table6.total_amount) as employee,
                        sum(table7.total_amount) as employer,
                        sum(table8.total_amount) as deduction,
                        sum(hr_payslip_line.total) as net_pay,
                        sum(table9.total_amount) as total_amt_usd,
                        sum(table10.total_amount) as total_amt_lrd
                    FROM
                        hr_payslip_line
                        INNER JOIN hr_salary_rule ON  hr_payslip_line.salary_rule_id = hr_salary_rule.id
                        INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id
                        INNER JOIN hr_department ON hr_employee.department_id = hr_department.id
                        INNER JOIN
                        (SELECT
                                hr_employee.name_related as emp_name1,
                                hr_salary_rule.name  ,
                                hr_department.name as dep_name1,
                                hr_employee.bank_account_number_usd as bank_usd1,
                                hr_employee.bank_account_number_lrd ,
                                sum(hr_payslip_line.total) as total_amount
                                FROM
                                hr_payslip_line
                                INNER JOIN hr_salary_rule ON  hr_payslip_line.salary_rule_id = hr_salary_rule.id
                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id
                                INNER JOIN hr_department ON hr_employee.department_id = hr_department.id
                                WHERE
                                   hr_payslip_line.code = %s AND
                                   hr_employee.department_id  in %s AND
                                   hr_payslip_line.date_from >= %s AND
                                   hr_payslip_line.date_to <= %s
                                GROUP BY
                                  hr_employee.name_related,
                                  hr_salary_rule.name,
                                 dep_name1 ,
                                  emp_name1,
                                  bank_usd1,
                                  hr_employee.bank_account_number_lrd ) as table2 ON table2.emp_name1 = hr_employee.name_related
                        INNER JOIN
                        (SELECT
                                hr_employee.name_related as emp3,
                                hr_salary_rule.name,
                                hr_department.name,
                                hr_employee.bank_account_number_usd,
                                hr_employee.bank_account_number_lrd,
                                sum(hr_payslip_line.total) as total_amount
                                FROM
                                hr_payslip_line
                                INNER JOIN hr_salary_rule ON  hr_payslip_line.salary_rule_id = hr_salary_rule.id
                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id
                                INNER JOIN hr_department ON hr_employee.department_id = hr_department.id
                                WHERE
                                   hr_payslip_line.code = %s AND
                                   hr_employee.department_id  in %s AND
                                   hr_payslip_line.date_from >= %s AND
                                   hr_payslip_line.date_to <= %s
                                GROUP BY
                                    emp3,
                                    hr_salary_rule.name,
                                    hr_department.name,
                                    hr_employee.bank_account_number_usd,
                                    hr_employee.bank_account_number_lrd
                                 ) as table3 ON emp3 = hr_employee.name_related
                        INNER JOIN
                        (SELECT
                                hr_employee.name_related as emp4,
                                hr_salary_rule.name,
                                hr_department.name,
                                hr_employee.bank_account_number_usd,
                                hr_employee.bank_account_number_lrd,
                                sum(hr_payslip_line.total) as total_amount
                                FROM
                                hr_payslip_line
                                INNER JOIN hr_salary_rule ON  hr_payslip_line.salary_rule_id = hr_salary_rule.id
                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id
                                INNER JOIN hr_department ON hr_employee.department_id = hr_department.id
                                WHERE
                                   hr_payslip_line.code = %s AND
                                   hr_employee.department_id  in %s AND
                                   hr_payslip_line.date_from >= %s AND
                                   hr_payslip_line.date_to <= %s
                                GROUP BY
                                    emp4,
                                    hr_salary_rule.name,
                                    hr_department.name,
                                    hr_employee.bank_account_number_usd,
                                    hr_employee.bank_account_number_lrd
                                 ) as table4 ON emp4 = hr_employee.name_related
                         INNER JOIN
                        (SELECT
                                hr_employee.name_related as emp5,
                                hr_salary_rule.name,
                                hr_department.name,
                                hr_employee.bank_account_number_usd,
                                hr_employee.bank_account_number_lrd,
                                sum(hr_payslip_line.total) as total_amount
                                FROM
                                hr_payslip_line
                                INNER JOIN hr_salary_rule ON  hr_payslip_line.salary_rule_id = hr_salary_rule.id
                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id
                                INNER JOIN hr_department ON hr_employee.department_id = hr_department.id
                                WHERE
                                   hr_payslip_line.code = %s AND
                                   hr_employee.department_id  in %s AND
                                   hr_payslip_line.date_from >= %s AND
                                   hr_payslip_line.date_to <= %s
                                GROUP BY
                                    emp5,
                                    hr_salary_rule.name,
                                    hr_department.name,
                                    hr_employee.bank_account_number_usd,
                                    hr_employee.bank_account_number_lrd
                                 ) as "table5" ON emp5 = hr_employee.name_related
                        INNER JOIN
                        (SELECT
                                hr_employee.name_related as emp6,
                                hr_salary_rule.name,
                                hr_department.name,
                                hr_employee.bank_account_number_usd,
                                hr_employee.bank_account_number_lrd,
                                sum(hr_payslip_line.total) as total_amount
                                FROM
                                hr_payslip_line
                                INNER JOIN hr_salary_rule ON  hr_payslip_line.salary_rule_id = hr_salary_rule.id
                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id
                                INNER JOIN hr_department ON hr_employee.department_id = hr_department.id
                                WHERE
                                   hr_payslip_line.code = %s AND
                                   hr_employee.department_id  in %s AND
                                   hr_payslip_line.date_from >= %s AND
                                   hr_payslip_line.date_to <= %s
                                GROUP BY
                                    emp6,
                                    hr_salary_rule.name,
                                    hr_department.name,
                                    hr_employee.bank_account_number_usd,
                                    hr_employee.bank_account_number_lrd
                                 ) as "table6" ON emp6 = hr_employee.name_related
                        INNER JOIN
                        (SELECT
                                hr_employee.name_related as emp7,
                                hr_salary_rule.name,
                                hr_department.name,
                                hr_employee.bank_account_number_usd,
                                hr_employee.bank_account_number_lrd,
                                sum(hr_payslip_line.total) as total_amount
                                FROM
                                hr_payslip_line
                                INNER JOIN hr_salary_rule ON  hr_payslip_line.salary_rule_id = hr_salary_rule.id
                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id
                                INNER JOIN hr_department ON hr_employee.department_id = hr_department.id
                                WHERE
                                   hr_payslip_line.code = %s AND
                                   hr_employee.department_id  in %s AND
                                   hr_payslip_line.date_from >= %s AND
                                   hr_payslip_line.date_to <= %s
                                GROUP BY
                                    emp7,
                                    hr_salary_rule.name,
                                    hr_department.name,
                                    hr_employee.bank_account_number_usd,
                                    hr_employee.bank_account_number_lrd
                                 ) as "table7" ON emp7 = hr_employee.name_related
                        INNER JOIN
                        (SELECT
                                hr_employee.name_related as emp8,
                                hr_salary_rule.name,
                                hr_department.name,
                                hr_employee.bank_account_number_usd,
                                hr_employee.bank_account_number_lrd,
                                sum(hr_payslip_line.total) as total_amount
                                FROM
                                hr_payslip_line
                                INNER JOIN hr_salary_rule ON  hr_payslip_line.salary_rule_id = hr_salary_rule.id
                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id
                                INNER JOIN hr_department ON hr_employee.department_id = hr_department.id
                                WHERE
                                   hr_payslip_line.code = %s AND
                                   hr_employee.department_id  in %s AND
                                   hr_payslip_line.date_from >= %s AND
                                   hr_payslip_line.date_to <= %s
                                GROUP BY
                                    emp8,
                                    hr_salary_rule.name,
                                    hr_department.name,
                                    hr_employee.bank_account_number_usd,
                                    hr_employee.bank_account_number_lrd
                                 ) as "table8" ON emp8 = hr_employee.name_related
                        INNER JOIN
                        (SELECT
                                hr_employee.name_related as emp9,
                                hr_salary_rule.name,
                                hr_department.name,
                                hr_employee.bank_account_number_usd,
                                hr_employee.bank_account_number_lrd,
                                sum(hr_payslip_line.total) as total_amount
                                FROM
                                hr_payslip_line
                                INNER JOIN hr_salary_rule ON  hr_payslip_line.salary_rule_id = hr_salary_rule.id
                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id
                                INNER JOIN hr_department ON hr_employee.department_id = hr_department.id
                                WHERE
                                   hr_payslip_line.code = %s AND
                                   hr_employee.department_id  in %s AND
                                   hr_payslip_line.date_from >= %s AND
                                   hr_payslip_line.date_to <= %s
                                GROUP BY
                                    emp9,
                                    hr_salary_rule.name,
                                    hr_department.name,
                                    hr_employee.bank_account_number_usd,
                                    hr_employee.bank_account_number_lrd
                                 ) as "table9" ON emp9 = hr_employee.name_related
                        INNER JOIN
                        (SELECT
                                hr_employee.name_related as emp10,
                                hr_salary_rule.name,
                                hr_department.name,
                                hr_employee.bank_account_number_usd,
                                hr_employee.bank_account_number_lrd,
                                sum(hr_payslip_line.total) as total_amount
                                FROM
                                hr_payslip_line
                                INNER JOIN hr_salary_rule ON  hr_payslip_line.salary_rule_id = hr_salary_rule.id
                                INNER JOIN hr_employee ON hr_payslip_line.employee_id = hr_employee.id
                                INNER JOIN hr_department ON hr_employee.department_id = hr_department.id
                                WHERE
                                   hr_payslip_line.code = %s AND
                                   hr_employee.department_id  in %s AND
                                   hr_payslip_line.date_from >= %s AND
                                   hr_payslip_line.date_to <= %s
                                GROUP BY
                                    emp10,
                                    hr_salary_rule.name,
                                    hr_department.name,
                                    hr_employee.bank_account_number_usd,
                                    hr_employee.bank_account_number_lrd
                                 ) as "table10" ON emp10 = hr_employee.name_related
                    WHERE
                          hr_payslip_line.code = %s AND
                          hr_employee.department_id  in %s AND
                          hr_payslip_line.date_from >= %s AND
                          hr_payslip_line.date_to <= %s
                    GROUP BY
                          rule_name,
                          dep_name,
                          dept_id,
                          emp_name,
                          bank_usd,
                          bank_lrd ;
                    """
        args = ('BASIC',tuple(department_ids), start_date,end_date,'BENEFIT',tuple(department_ids), start_date,end_date,'TAXABLE',tuple(department_ids), start_date,end_date,'INCOME_TAX_LRD',tuple(department_ids), start_date,end_date,'EMPLOYEE',tuple(department_ids), start_date,end_date,'EMPLOYER',tuple(department_ids), start_date,end_date,'SD',tuple(department_ids), start_date,end_date,'HQ_USD_NET', tuple(department_ids),start_date,end_date,'HQ_LRD_NET',tuple(department_ids), start_date,end_date,'HQ_NET', tuple(department_ids), start_date,end_date,)
        self.env.cr.execute(sql_statement, args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll





