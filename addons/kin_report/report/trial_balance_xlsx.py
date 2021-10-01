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


class TrialBalanceReportWriter(ReportXlsx):

    def data_section(self,workbook,account_worksheet,row,data,title,account_tag_id,is_debit_credit=False,step=0,trial_balance=False):
        financial_statement_parser = self.env['trial.balance.parser']

        acc_lists = [account.id for account in account_tag_id.account_ids]
        if not acc_lists:
            raise UserError(
                "Please assign the '"+ title +"' for Custom Report' Tag to the "+ title +" account head")

        data['form'].update({'account_ids': acc_lists})
        list_dicts = financial_statement_parser._get_data(data['form'])
        bal = 0
        return  self._render_trial_balance(workbook, account_worksheet, row, list_dicts, title,
                                                             is_debit_credit, step)




    def _render_trial_balance(self,workbook,account_worksheet,row,list_dicts,str_total,is_debit_credit=False,step=0):
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
        debit_bal = 0
        credit_bal = 0
        for list_dict in list_dicts:
            account_worksheet.write(row, 0, list_dict['code'] + ' ' + list_dict['name'], cell_wrap_format_indent1)
            if list_dict['balance'] > 0 :
                account_worksheet.write(row, 1, list_dict['balance'], curr_format)
                debit_bal += list_dict['balance']
            elif list_dict['balance'] < 0 :
                account_worksheet.write(row, 2, abs(list_dict['balance']), curr_format)
                credit_bal += list_dict['balance']
            row += 1
        return debit_bal,credit_bal, row



    def generate_xlsx_report(self, workbook, data, objects):
        self.trial_balance_xlsx_report(workbook, data, objects)



    def trial_balance_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        is_debit_credit = False
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
                                              '%d/%m/%Y') + '  to ' + datetime.strptime(end_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y'), title_format)
        else:
            account_worksheet.merge_range(3, 0, 3, 3, 'Period: All', title_format)

        col = 0
        row = 5
        account_worksheet.set_column(0, 0, 30)  # set column width with wrap format.
        account_worksheet.set_column(0, 3, 15)

        account_worksheet.write_row(row, col, ('Description', 'Debit Bal. (' + user_company.currency_id.symbol + ')',
                                                   'Credit Bal. (' + user_company.currency_id.symbol + ')'), head_format)

        debit_bal = 0
        credit_bal = 0

        # For Current Assets
        title = 'Current Assets'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_current_assets')
        bal_debit,bal_credit, row = self.data_section(workbook, account_worksheet,
                                                                                        row, data, title,
                                                                                        account_tag_id, is_debit_credit,
                                                                                        step=0,trial_balance=True)
        debit_bal += bal_debit
        credit_bal += bal_credit

        # Long-term Assets
        title = 'Long-term Assets'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_long_term_assets')
        bal_debit, bal_credit, row = self.data_section(workbook, account_worksheet,
                                                       row, data, title,
                                                       account_tag_id, is_debit_credit,
                                                       step=0, trial_balance=True)
        debit_bal += bal_debit
        credit_bal += bal_credit

        # Other Assets
        title = 'Other Assets'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_other_assets')
        bal_debit, bal_credit, row = self.data_section(workbook, account_worksheet,
                                                       row, data, title,
                                                       account_tag_id, is_debit_credit,
                                                       step=0, trial_balance=True)
        debit_bal += bal_debit
        credit_bal += bal_credit

        # Current liabilities
        title = 'Current Liabilities'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_current_liabilities')
        bal_debit, bal_credit, row = self.data_section(workbook, account_worksheet,
                                                       row, data, title,
                                                       account_tag_id, is_debit_credit,
                                                       step=0, trial_balance=True)
        debit_bal += bal_debit
        credit_bal += bal_credit

        # Long-term Liabilities
        title = 'Long-term Liabilities'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_long_term_liabilities')
        bal_debit, bal_credit, row = self.data_section(workbook, account_worksheet,
                                                       row, data, title,
                                                       account_tag_id, is_debit_credit,
                                                       step=0, trial_balance=True)
        debit_bal += bal_debit
        credit_bal += bal_credit

        # Equity
        title = "Owner's Equity"
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_equity')
        bal_debit, bal_credit, row = self.data_section(workbook, account_worksheet,
                                                       row, data, title,
                                                       account_tag_id, is_debit_credit,
                                                       step=0, trial_balance=True)
        debit_bal += bal_debit
        credit_bal += bal_credit

        # Sales (Operating Revenue)
        title = 'Sales'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_sales')
        bal_debit, bal_credit, row = self.data_section(workbook, account_worksheet,
                                                       row, data, title,
                                                       account_tag_id, is_debit_credit,
                                                       step=0, trial_balance=True)
        debit_bal += bal_debit
        credit_bal += bal_credit

        # Cost of Sales
        title = 'Cost of Goods Sold'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_cogs')
        bal_debit, bal_credit, row = self.data_section(workbook, account_worksheet,
                                                       row, data, title,
                                                       account_tag_id, is_debit_credit,
                                                       step=0, trial_balance=True)
        debit_bal += bal_debit
        credit_bal += bal_credit

        # Selling Expenses
        title = 'Selling expenses'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_selling_expenses')
        bal_debit, bal_credit, row = self.data_section(workbook, account_worksheet,
                                                       row, data, title,
                                                       account_tag_id, is_debit_credit,
                                                       step=0, trial_balance=True)
        debit_bal += bal_debit
        credit_bal += bal_credit

        # Administrative Expenses
        title = 'Administrative expenses'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_administrative_expenses')
        bal_debit, bal_credit, row = self.data_section(workbook, account_worksheet,
                                                       row, data, title,
                                                       account_tag_id, is_debit_credit,
                                                       step=0, trial_balance=True)
        debit_bal += bal_debit
        credit_bal += bal_credit

        # Other Non-Operating Revenues and Gains
        title = 'Other Non-Operating Revenues and Gains'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_non_operating_revenue_gains')
        bal_debit, bal_credit, row = self.data_section(workbook, account_worksheet,
                                                       row, data, title,
                                                       account_tag_id, is_debit_credit,
                                                       step=0, trial_balance=True)
        debit_bal += bal_debit
        credit_bal += bal_credit

        # Other Non-Operating Expenses and Losses
        title = 'Other Non-Operating Expenses and Losses'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_non_operating_expenses_losses')
        bal_debit, bal_credit, row = self.data_section(workbook, account_worksheet,
                                                       row, data, title,
                                                       account_tag_id, is_debit_credit,
                                                       step=0, trial_balance=True)
        debit_bal += bal_debit
        credit_bal += bal_credit

        # Company Income Tax
        title = 'Income Tax'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_income_tax')
        bal_debit, bal_credit, row = self.data_section(workbook, account_worksheet,
                                                       row, data, title,
                                                       account_tag_id, is_debit_credit,
                                                       step=0, trial_balance=True)
        debit_bal += bal_debit
        debit_bal += bal_credit

        row += 1
        account_worksheet.write(row, 0, 'Total', head_format)
        account_worksheet.write(row, 1, debit_bal, cell_total_currency)
        account_worksheet.write(row, 2, debit_bal, cell_total_currency)

# The trial.balance.parser in the TrialBalanceReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
TrialBalanceReportWriter('report.kin_report.report_trial_balance', 'trial.balance.parser',parser=report_sxw.rml_parse)


