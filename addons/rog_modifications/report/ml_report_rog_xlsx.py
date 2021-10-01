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

class MLReportWriter(ReportXlsx):

    def _get_data(self, form):
        start_date = form['start_date']
        end_date = form['end_date']
        account_id = form['account_id'][0]

        if not start_date:
            start_date = ''

        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')

        sql_statement = """
                    SELECT  move_id, account_move.name as move_name, account_id, account_move_line.date as date, account_move_line.name, account_move.ref, sum(debit) as debit, sum(credit) as credit
                      FROM account_move_line  
                      inner join account_move
                      ON account_move_line.move_id = account_move.id
                      where account_id = %s and account_move_line.date >= %s and account_move_line.date <= %s
                      group by move_name, move_id, account_id, account_move_line.date, account_move_line.name, account_move.ref
                      order by date asc

                            """
        args = (account_id,start_date, end_date,)
        self.env.cr.execute(sql_statement, args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll


    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        list_dicts = self._get_data(data['form'])

        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        account_id = data['form']['account_id'][0]
        account_name = self.env['account.account'].browse(account_id).name

        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')

        report_worksheet = workbook.add_worksheet('Lines Group by Journal Entry')
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
        report_worksheet.merge_range(0, 0, 0, 5, user_company.name, header_format)

        # Title Format
        report_worksheet.set_row(2, 20)
        report_worksheet.merge_range(2, 0, 2, 5, 'Account Move Lines Grouped by Journal Entries', title_format)

        # Period
        report_worksheet.set_row(3, 20)
        if start_date and end_date:
            report_worksheet.merge_range(3, 0, 3, 5,
                                         'Period Between: ' + datetime.strptime(start_date, '%Y-%m-%d').strftime(
                                             '%d/%m/%Y') + '  and ' + datetime.strptime(end_date,
                                                                                        '%Y-%m-%d').strftime(
                                             '%d/%m/%Y'), title_format)
            report_worksheet.merge_range(4, 0, 4, 5, 'GL Account: %s' % account_name, title_format)
        else:
            report_worksheet.merge_range(3, 0, 3, 5, 'All Period', title_format)



        col = 0
        row = 7
        report_worksheet.set_column(0,0,10)  # set column width with wrap format.
        report_worksheet.set_column(1,1,15)
        report_worksheet.set_column(2, 2, 25)
        report_worksheet.set_column(3, 3, 15)
        report_worksheet.set_column(4, 4, 15)
        report_worksheet.set_column(5, 5, 15)
        report_worksheet.set_column(6, 6, 15)


        report_worksheet.write_row(row, col, ('Date','Journal Entry', 'Name', 'Reference', 'Debit','Credit','Cumulative') , head_format)

        row += 1
        total_debit = total_credit = 0
        first_row = row
        cuml = 0
        for list_dict in list_dicts:
            report_worksheet.write(row, 0,  datetime.strptime(list_dict['date'], '%Y-%m-%d').strftime('%d/%m/%Y'), cell_wrap_format)
            report_worksheet.write(row, 1, list_dict['move_name'], cell_wrap_format)
            report_worksheet.write(row, 2, list_dict['name'], cell_wrap_format)
            report_worksheet.write(row, 3, list_dict['ref'], cell_wrap_format)
            report_worksheet.write(row, 4, list_dict['debit'], cell_amount)
            report_worksheet.write(row, 5, list_dict['credit'], cell_amount)
            total_debit += list_dict['debit'] or 0
            total_credit += list_dict['credit'] or 0
            cuml = total_debit - total_credit
            report_worksheet.write(row, 6, cuml, cell_amount)
            row += 1
        last_row = row
        report_worksheet.write(row, 3, 'TOTAL:', cell_total_currency)
        a1_notation_ref = xl_range(first_row, 4, last_row, 4)
        report_worksheet.write(row, 4, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_debit)
        a1_notation_ref = xl_range(first_row, 5, last_row, 5)
        report_worksheet.write(row, 5, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_credit)
        report_worksheet.write(row, 6, total_debit - total_credit, cell_total_currency)

# The purchase.report.wizard in the PurchaseReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
MLReportWriter('report.rog_modifications.report_ml_excel_rog','ml.report.wizard',parser=report_sxw.rml_parse)


