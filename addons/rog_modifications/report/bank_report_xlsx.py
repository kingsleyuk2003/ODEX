# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell
from openerp.exceptions import UserError

class BankReportWriter(ReportXlsx):

    def _get_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']

        where_start_date = ''
        if start_date :
            where_start_date = "date >= '%s' AND" % (start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        # LEFT JOIN works similar to INNER JOIN but with the extra advantage of showing empty join parameter fields (uncompulsory join fields). It is good for join fields that don't have value. It will still show the records. Unlike INNER JOIN (for compulsory join fields) which will omit those records
        sql_statement = """
            SELECT account_account.name as bank_name,
               sum(debit) as deposit,
               sum(credit) as withdrawal, 
               sum(balance) as balance
          FROM account_move_line 
          LEFT JOIN  account_account ON account_move_line.account_id = account_account.id
          LEFT JOIN account_account_type ON account_account.user_type_id = account_account_type.id
          WHERE 
          """ + where_start_date +"""
          date <= %s and
          account_account_type.type = 'liquidity' 
          GROUP BY bank_name
            """
        args = (end_date,)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll


    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        list_dicts = list_dicts = self._get_data(data['form'])

        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')


        report_worksheet = workbook.add_worksheet('Report')
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
        cell_number = workbook.add_format({'border': 1, 'font_size': 10})
        cell_number.set_num_format('#,#00.00')

        # Header Format
        report_worksheet.set_row(0, 30)  # Set row height
        report_worksheet.merge_range(0, 0, 0, 7, user_company.name, header_format)

        # Title Format
        report_worksheet.set_row(2, 20)
        report_worksheet.merge_range(2, 0, 2, 7, 'Bank / Cash Summary Report', title_format)

        # Period
        report_worksheet.set_row(3, 20)
        if start_date and end_date:
            report_worksheet.merge_range(3, 0, 3, 7,
                                          'Period: ' + datetime.strptime(start_date, '%Y-%m-%d').strftime(
                                              '%d-%m-%Y') + '  to ' + datetime.strptime(end_date, '%Y-%m-%d').strftime(
                                              '%d-%m-%Y'), title_format)
        else:
            report_worksheet.merge_range(3, 0, 3, 7, 'All Period', title_format)

        col = 0
        row = 5
        report_worksheet.set_column(0, 0, 50)
        report_worksheet.set_column(1, 1, 15)
        report_worksheet.set_column(2, 2, 15)
        report_worksheet.set_column(3, 3, 25)

        report_worksheet.write_row(row, col, ('Bank / Cash (NGN)', 'Credit (NGN)', 'Debit (NGN)', 'Bank / Cash Balance (NGN)'), head_format)
        row += 1
        total = 0
        first_row = row
        for list_dict in list_dicts:
            report_worksheet.write(row, 0, list_dict['bank_name'], cell_wrap_format)
            report_worksheet.write(row, 1, list_dict['deposit'], cell_number)
            report_worksheet.write(row, 2, list_dict['withdrawal'], cell_number)
            report_worksheet.write(row, 3, list_dict['deposit']-list_dict['withdrawal'], cell_number)
            row += 1
            total += list_dict['balance']
        last_row = row
        a1_notation_ref = xl_range(first_row, 3, last_row, 3)
        report_worksheet.write(row, 3, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total)

        return

# The sales.report.wizard in the SalesReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
BankReportWriter('report.rog_modifications.bank_excel_report_rog','bank.report.wizard')

