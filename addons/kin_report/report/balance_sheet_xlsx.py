# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw
from openerp.exceptions import UserError
from datetime import datetime
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell


class BalanceSheetReportWriter(ReportXlsx):

    def data_section(self,workbook,account_worksheet,row,data,title,account_tag_id,is_debit_credit=False,step=0,trial_balance=False):
        financial_statement_parser = self.env['balance.sheet.parser']

        acc_lists = [account.id for account in account_tag_id.account_ids]
        if not acc_lists:
            raise UserError(
                "Please assign the '"+ title +"' for Custom Report' Tag to the "+ title +" account head")

        data['form'].update({'account_ids': acc_lists})
        list_dicts = financial_statement_parser._get_data(data['form'])
        bal = 0
        return  self._get_section(workbook,account_worksheet, row, list_dicts, title,is_debit_credit,step)




    def _get_section(self,workbook,account_worksheet,row,list_dicts,str_total,is_debit_credit=False,step=0):
        head_sub_format_indent1 = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        head_sub_format_indent1.set_indent(1)
        cell_total_description = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_total_description.set_indent(1 + step)
        cell_total_currency = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_total_currency.set_num_format('#,#00.00')
        curr_format = workbook.add_format({'valign': 'vjustify', 'font_size': 10, 'border': 1})
        curr_format.set_num_format('#,#00.00')
        cell_wrap_format = workbook.add_format({'valign': 'vjustify', 'font_size': 10, 'border': 1})
        cell_wrap_format_indent1 = workbook.add_format({'valign': 'vjustify', 'font_size': 10, 'border': 1})
        cell_wrap_format_indent1.set_indent(1 + step)

        row += 1
        first_row = last_row = row
        first_col = 3
        last_col = 3
        bal = 0
        total_col = 0
        total_row = 0
        for list_dict in list_dicts:
            if list_dict['balance']  <> 0 :
                account_worksheet.write(row, 0, list_dict['code'] + ' ' + list_dict['name'], cell_wrap_format_indent1)
                if is_debit_credit :
                    account_worksheet.write(row, 1, list_dict['debit'], curr_format)
                    account_worksheet.write(row, 2, list_dict['credit'], curr_format)
                    account_worksheet.write(row, 3, list_dict['balance'], curr_format)
                else:
                    account_worksheet.write(row, 1, list_dict['balance'], curr_format)
                bal += list_dict['balance']
                last_row = row
                row += 1

        account_worksheet.write(row, 0, 'Total ' + str_total, cell_total_description)
        if is_debit_credit:
            a1_notation_ref = xl_range(first_row, first_col, last_row, last_col)
            account_worksheet.write(row, 1, '', cell_wrap_format)
            account_worksheet.write(row, 2, '', cell_wrap_format)
            account_worksheet.write_formula(row, 3, '=SUM('+ a1_notation_ref +')', cell_total_currency,bal)
            total_col = 3
            total_row = row
        else:
            a1_notation_ref = xl_range(first_row, first_col-2, last_row, last_col-2)
            account_worksheet.write(row, 1, '=SUM(' + a1_notation_ref + ')', cell_total_currency, bal)
            total_col = 1
            total_row = row

        a1_notation_total_ref = xl_rowcol_to_cell(total_row, total_col)
        return bal, row, a1_notation_total_ref


    def generate_xlsx_report(self, workbook, data, objects):
        self.balance_sheet_xlsx_report(workbook, data, objects)


    def balance_sheet_xlsx_report(self,workbook, data, objects):
        user_company = self.env.user.company_id
        is_debit_credit = data['form']['is_debit_credit']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        if not end_date:
            end_date = datetime.today().strftime('31-12-%d')

        account_worksheet = workbook.add_worksheet(data['name'])
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 24})
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        head_format = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        head_format.set_num_format('#,#00.00')
        head_format_total = workbook.add_format({'bold': True, 'border': 1})
        head_sub_format_indent1 = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        head_sub_format_indent1.set_indent(1)
        cell_total_description = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_wrap_format = workbook.add_format({'valign': 'vjustify', 'font_size': 10, 'border': 1})
        cell_total_currency = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_total_currency.set_num_format('#,#00.00')

        # Header Format
        account_worksheet.set_row(0, 30)  # Set row height
        account_worksheet.merge_range(0, 0, 0, 3, user_company.name, header_format)

        # Title Format
        account_worksheet.set_row(2, 20)
        account_worksheet.merge_range(2, 0, 2, 3, data['name'], title_format)

        # Period
        account_worksheet.set_row(3, 20)
        if start_date and end_date:
            account_worksheet.merge_range(3, 0, 3, 3,
                                          'Period: ' + datetime.strptime(start_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y') + '  to ' + datetime.strptime(end_date,'%Y-%m-%d').strftime(
                                              '%d/%m/%Y'), title_format)
        else:
            account_worksheet.merge_range(3, 0, 3, 3, 'Period: All', title_format)

        col = 0
        row = 5
        account_worksheet.set_column(0, 0, 30)  # set column width with wrap format.
        account_worksheet.set_column(0, 3, 15)


        acc_lists = []
        financial_statement_parser = self.env['balance.sheet.parser']


        if is_debit_credit:
            account_worksheet.write_row(row, col, ('Description', 'Debit (' + user_company.currency_id.symbol + ')',
                                                   'Credit (' + user_company.currency_id.symbol + ')',
                                                   'Balance (' + user_company.currency_id.symbol + ')'), head_format)

        row += 2
        account_worksheet.set_row(row, 15)
        account_worksheet.merge_range(row, 0, row, 3, 'Assets', title_format)

        # For Current Assets
        row += 1
        title = 'Current Assets'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_current_assets')
        bal_current_assets, row, a1_notation_ref_current_assets = self.data_section(workbook, account_worksheet,
                                                                                        row, data, title,
                                                                                        account_tag_id, is_debit_credit,
                                                                                        step=0)

        # Long-term Assets
        row += 2
        title = 'Long-term Assets'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_long_term_assets')
        bal_long_term_assets, row, a1_notation_ref_long_term_assets = self.data_section(workbook, account_worksheet,
                                                                                    row, data, title,
                                                                                    account_tag_id, is_debit_credit,
                                                                                    step=0)

        # Other Assets
        row += 2
        title = 'Other Assets'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_other_assets')
        bal_other_assets, row, a1_notation_ref_other_assets = self.data_section(workbook, account_worksheet,
                                                                                        row, data, title,
                                                                                        account_tag_id, is_debit_credit,
                                                                                        step=0)


        # Total Assets
        bal_total_assets = bal_current_assets + bal_long_term_assets + bal_other_assets
        a1_notation_total_assets = ''
        row += 2
        account_worksheet.write(row, 0, 'Total Assets', head_format_total)
        if is_debit_credit:
            account_worksheet.write(row, 1, '', cell_wrap_format)
            account_worksheet.write(row, 2, '', cell_wrap_format)
            account_worksheet.write(row, 3, '=%s+%s+%s' % (a1_notation_ref_current_assets, a1_notation_ref_long_term_assets,a1_notation_ref_other_assets),
                                    cell_total_currency, bal_total_assets)
            a1_notation_total_assets = xl_rowcol_to_cell(row, 3)
        else:
            account_worksheet.write(row, 1, '=%s+%s+%s' % (a1_notation_ref_current_assets, a1_notation_ref_long_term_assets,a1_notation_ref_other_assets),
                                    cell_total_currency, bal_total_assets)
            a1_notation_total_assets = xl_rowcol_to_cell(row, 1)


        row += 3
        account_worksheet.set_row(row, 15)
        account_worksheet.merge_range(row, 0, row, 3, 'Liabilities', title_format)

        #Current liabilities
        row += 1
        title = 'Current Liabilities'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_current_liabilities')
        bal_current_liabilities, row, a1_notation_ref_current_liabilities = self.data_section(workbook, account_worksheet,
                                                                                        row, data, title,
                                                                                        account_tag_id, is_debit_credit,
                                                                                        step=0)

        # Long-term Liabilities
        row += 2
        title = 'Long-term Liabilities'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_long_term_liabilities')
        bal_long_term_liabilities, row, a1_notation_ref_long_term_liabilities = self.data_section(workbook,
                                                                                              account_worksheet,
                                                                                              row, data, title,
                                                                                              account_tag_id,
                                                                                              is_debit_credit,
                                                                                              step=0)

        # Total Liabilities
        bal_total_liabilities = bal_current_liabilities + bal_long_term_liabilities
        a1_notation_total_liabilities = ''
        row += 2
        account_worksheet.write(row, 0, 'Total Liabilities', head_format_total)
        if is_debit_credit:
            account_worksheet.write(row, 1, '', cell_wrap_format)
            account_worksheet.write(row, 2, '', cell_wrap_format)
            account_worksheet.write(row, 3,
                                    '=%s+%s' % (a1_notation_ref_current_liabilities, a1_notation_ref_long_term_liabilities),
                                    cell_total_currency, bal_total_liabilities)
            a1_notation_total_liabilities = xl_rowcol_to_cell(row, 3)
        else:
            account_worksheet.write(row, 1,
                                    '=%s+%s' % (a1_notation_ref_current_liabilities, a1_notation_ref_long_term_liabilities),
                                    cell_total_currency, bal_total_liabilities)
            a1_notation_total_liabilities = xl_rowcol_to_cell(row, 1)


        row += 3
        account_worksheet.set_row(row, 15)
        account_worksheet.merge_range(row, 0, row, 3, 'Equity', title_format)

        # Equity
        row += 1
        title = "Owner's Equity"
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_equity')
        bal_equity, row, a1_notation_ref_equity = self.data_section(workbook, account_worksheet,
                                                                                                  row, data, title,
                                                                                                  account_tag_id,
                                                                                                  is_debit_credit,
                                                                                                  step=0)

        #Net Income
        acc_lists = []
        account_tag_ids = [self.env.ref('kin_report.account_tag_sales'),self.env.ref('kin_report.account_tag_cogs'),self.env.ref('kin_report.account_tag_selling_expenses'),self.env.ref('kin_report.account_tag_administrative_expenses'),self.env.ref('kin_report.account_tag_non_operating_revenue_gains'),self.env.ref('kin_report.account_tag_non_operating_expenses_losses'),self.env.ref('kin_report.account_tag_income_tax')]
        for account_tag_id in account_tag_ids :
            for account in account_tag_id.account_ids :
                acc_lists.append(account.id)
        if not acc_lists:
            raise UserError("Please assign the appropriate account tags for the account heads")

        data['form'].update({'account_ids': acc_lists})
        list_dicts = financial_statement_parser._get_data(data['form'])
        bal_net_income = 0
        bal_debit = 0
        bal_credit = 0
        for list_dict in list_dicts:
            bal_debit += list_dict['debit']
            bal_credit += list_dict['credit']
            bal_net_income += list_dict['balance']
        a1_notation_net_income = ''
        row += 2
        account_worksheet.write(row, 0, 'Net Income', head_format)
        if is_debit_credit:
            account_worksheet.write(row, 1, bal_debit, cell_total_currency)
            account_worksheet.write(row, 2, bal_credit, cell_total_currency)
            account_worksheet.write(row, 3, bal_net_income,cell_total_currency)
            a1_notation_net_income = xl_rowcol_to_cell(row, 3)
        else:
            account_worksheet.write(row, 1, bal_net_income, cell_total_currency)
            a1_notation_net_income = xl_rowcol_to_cell(row, 1)


        # Total Liabilities and Equity
        bal_total_liabilities_equity = bal_total_liabilities + bal_equity + bal_net_income
        row += 2
        account_worksheet.write(row, 0, 'Total Liabilities and Equity', head_format_total)
        if is_debit_credit:
            account_worksheet.write(row, 1, '', cell_wrap_format)
            account_worksheet.write(row, 2, '', cell_wrap_format)
            account_worksheet.write(row, 3, '=%s+%s+%s' % (a1_notation_total_liabilities, a1_notation_ref_equity,a1_notation_net_income),cell_total_currency, bal_total_liabilities_equity)
        else:
            account_worksheet.write(row, 1, '=%s+%s+%s' % (a1_notation_total_liabilities, a1_notation_ref_equity,a1_notation_net_income),cell_total_currency, bal_total_liabilities_equity)

# The balance.sheet.parser in the BalanceSheetReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
BalanceSheetReportWriter('report.kin_report.report_balance_sheet', 'balance.sheet.parser',parser=report_sxw.rml_parse)


