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


class IncomeStatementReportWriter(ReportXlsx):

    def data_section(self,workbook,account_worksheet,row,data,title,account_tag_id,is_debit_credit=False,step=0,trial_balance=False):
        financial_statement_parser = self.env['income.statement.parser']

        acc_lists = [account.id for account in account_tag_id.account_ids]
        if not acc_lists:
            raise UserError(
                "Please assign the '"+ title +"' for Custom Report' Tag to the "+ title +" account head")

        data['form'].update({'account_ids': acc_lists})
        list_dicts = financial_statement_parser._get_data(data['form'])
        bal = 0
        return  self._render_section(workbook,account_worksheet, row, list_dicts, title,is_debit_credit,step)


    def _render_section(self,workbook,account_worksheet,row,list_dicts,str_total,is_debit_credit=False,step=0):
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
        self.income_statment_xlsx_report(workbook, data, objects)


    #see for the format: http://www.myaccountingcourse.com/financial-statements/multi-step-income-statement
    def income_statment_xlsx_report(self, workbook, data, objects):

        the_date = datetime.today().strftime('%d %B %Y')
        user_company = self.env.user.company_id
        is_debit_credit = data['form']['is_debit_credit']
        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        if not end_date :
            end_date = datetime.today().strftime('31-12-%d')

        account_worksheet = workbook.add_worksheet(data['name'])
        header_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter','font_size':24})
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        head_format = workbook.add_format({'bold':True,'border':1,'font_size': 10})
        head_format.set_num_format('#,#00.00')
        head_format_total = workbook.add_format({'bold': True, 'border': 1})
        head_sub_format_indent1 = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        head_sub_format_indent1.set_indent(1)
        cell_total_description = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_wrap_format = workbook.add_format({'valign': 'vjustify', 'font_size': 10, 'border': 1})
        cell_total_currency = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_total_currency.set_num_format('#,#00.00')

        # Header Format
        account_worksheet.set_row(0,30)  #Set row height
        account_worksheet.merge_range(0,0,0,3,user_company.name,header_format)

        #Title Format
        account_worksheet.set_row(2, 20)
        account_worksheet.merge_range(2, 0, 2, 3, data['name'], title_format)

        #Period
        account_worksheet.set_row(3, 20)
        if start_date and end_date:
            account_worksheet.merge_range(3, 0, 3, 3, 'Period:' + datetime.strptime(start_date,'%Y-%m-%d').strftime('%d/%m/%Y') + '  to   ' + datetime.strptime(end_date,'%Y-%m-%d').strftime('%d/%m/%Y') , title_format)
        else :
            account_worksheet.merge_range(3, 0, 3, 3, 'Period: All',title_format)

        col = 0
        row = 5
        account_worksheet.set_column(0,0, 30)  # set column width with wrap format.
        account_worksheet.set_column(0, 3, 15)

        acc_lists = []
        financial_statement_parser = self.env['income.statement.parser']

        if is_debit_credit :
            account_worksheet.write_row(row, col, ('Description', 'Debit ('+ user_company.currency_id.symbol + ')', 'Credit ('+ user_company.currency_id.symbol + ')','Balance ('+ user_company.currency_id.symbol + ')'), head_format)

        # Sales (Operating Revenue)
        row += 1
        title = 'Sales'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_sales')
        bal_sales, row, a1_notation_ref_sales = self.data_section(workbook, account_worksheet,
                                                                    row, data, title,
                                                                    account_tag_id,
                                                                    is_debit_credit,
                                                                    step=0)
        # Cost of Sales
        row += 2
        title = 'Cost of Goods Sold'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_cogs')
        bal_cogs, row, a1_notation_ref_cog = self.data_section(workbook, account_worksheet,
                                                                  row, data, title,
                                                                  account_tag_id,
                                                                  is_debit_credit,
                                                                  step=0)

        #Gross Profit
        bal_gross_profit = bal_sales+bal_cogs
        a1_notation_gross_profit = ''
        row += 2
        account_worksheet.write(row, 0, 'Gross Profit', head_format_total)
        if is_debit_credit :
            account_worksheet.write(row, 1, '', cell_wrap_format)
            account_worksheet.write(row, 2, '', cell_wrap_format)
            account_worksheet.write(row, 3, '=%s+%s'%(a1_notation_ref_sales,a1_notation_ref_cog), cell_total_currency, bal_gross_profit)
            a1_notation_gross_profit = xl_rowcol_to_cell(row, 3)
        else:
            account_worksheet.write(row, 1, '=%s+%s'%(a1_notation_ref_sales,a1_notation_ref_cog), cell_total_currency, bal_gross_profit)
            a1_notation_gross_profit = xl_rowcol_to_cell(row, 1)


        #Operating Expenses see: https://www.investopedia.com/ask/answers/101314/what-are-differences-between-operating-expenses-and-sga.asp
        #Operating expenses = SG&A Expenses. Sales, General and Administrative Expenses. Sales expenses can be  direct or indirect expenses. see: https://www.investopedia.com/terms/s/sga.asp. Also note that COGS are also direct expenses
        row += 3
        account_worksheet.write(row, 0, 'Operating Expenses', head_format)

        # Selling Expenses
        row += 1
        title = 'Selling and Distribution expenses'
        account_worksheet.write(row, 0, title, head_sub_format_indent1)
        account_tag_id = self.env.ref('kin_report.account_tag_selling_expenses')
        bal_selling_expenses, row, a1_notation_ref_selling_expenses = self.data_section(workbook, account_worksheet,
                                                               row, data, title,
                                                               account_tag_id,
                                                               is_debit_credit,
                                                               step=1)


        # General and Administrative Expenses
        row += 2
        title = 'General and Administrative expenses'
        account_worksheet.write(row, 0, title, head_sub_format_indent1)
        account_tag_id = self.env.ref('kin_report.account_tag_administrative_expenses')
        bal_administrative_expenses, row, a1_notation_ref_admin_exp = self.data_section(workbook, account_worksheet,
                                                                                        row, data, title,
                                                                                        account_tag_id,
                                                                                        is_debit_credit,
                                                                                        step=1)

        # Total Operating Expenses
        bal_operating_expenses = bal_selling_expenses + bal_administrative_expenses
        a1_notation_operating_expenses = ''
        row += 2
        account_worksheet.write(row, 0, 'Total Operating Expenses', head_format_total)
        if is_debit_credit :
            account_worksheet.write(row, 1, '', cell_wrap_format)
            account_worksheet.write(row, 2, '', cell_wrap_format)
            account_worksheet.write(row, 3, bal_operating_expenses, cell_total_currency)
            account_worksheet.write(row, 3, '=%s+%s' % (a1_notation_ref_selling_expenses, a1_notation_ref_admin_exp),cell_total_currency, bal_operating_expenses)
            a1_notation_operating_expenses = xl_rowcol_to_cell(row, 3)
        else:
            account_worksheet.write(row, 1, '=%s+%s' % (a1_notation_ref_selling_expenses, a1_notation_ref_admin_exp), cell_total_currency, bal_operating_expenses)
            a1_notation_operating_expenses = xl_rowcol_to_cell(row, 1)

        # Operating Income
        bal_operating_income = bal_gross_profit + bal_operating_expenses
        a1_notation_operating_income = ''
        row += 2
        account_worksheet.write(row, 0, 'Operating Income', head_format_total)
        if is_debit_credit:
            account_worksheet.write(row, 1, '', cell_wrap_format)
            account_worksheet.write(row, 2, '', cell_wrap_format)
            account_worksheet.write(row, 3, bal_operating_income, cell_total_currency)
            account_worksheet.write(row, 3, '=%s+%s' % (a1_notation_gross_profit, a1_notation_operating_expenses),cell_total_currency, bal_operating_income)
            a1_notation_operating_income = xl_rowcol_to_cell(row, 3)
        else:
            account_worksheet.write(row, 1, '=%s+%s' % (a1_notation_gross_profit, a1_notation_operating_expenses), cell_total_currency, bal_operating_income)
            a1_notation_operating_income = xl_rowcol_to_cell(row, 1)


        # Other Non-Operating Revenues and Gains
        row += 3
        title = 'Other Non-Operating Revenues and Gains'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_non_operating_revenue_gains')
        bal_non_opex_rev_gains, row, a1_notation_ref_non_opex_rev_gains = self.data_section(workbook, account_worksheet,
                                                               row, data, title,
                                                               account_tag_id,
                                                               is_debit_credit,
                                                               step=0)

        # Other Non-Operating Expenses and Losses
        row += 2
        title = 'Other Non-Operating Expenses and Losses'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_non_operating_expenses_losses')
        bal_non_opex_exp_loss, row, a1_notation_ref_non_opex_exp_loss = self.data_section(workbook, account_worksheet,
                                                                                        row, data, title,
                                                                                        account_tag_id,
                                                                                        is_debit_credit,
                                                                                        step=0)

        # Total Non-Operating
        bal_non_operating = bal_non_opex_rev_gains + bal_non_opex_exp_loss
        a1_notation_non_operating = ''
        row += 2
        account_worksheet.write(row, 0, 'Total Non-Operating Income', head_format_total)
        if is_debit_credit:
            account_worksheet.write(row, 1, '', cell_wrap_format)
            account_worksheet.write(row, 2, '', cell_wrap_format)
            account_worksheet.write(row, 3,'=%s+%s' % (a1_notation_ref_non_opex_rev_gains, a1_notation_ref_non_opex_exp_loss),
                                        cell_total_currency, bal_non_operating)
            a1_notation_non_operating = xl_rowcol_to_cell(row, 3)
        else:
            account_worksheet.write(row, 1, '=%s+%s' % (a1_notation_ref_non_opex_rev_gains, a1_notation_ref_non_opex_exp_loss),
                                        cell_total_currency, bal_non_operating)
            a1_notation_non_operating = xl_rowcol_to_cell(row, 1)


        # Income before Tax
        bal_net_income_bf_tax = bal_operating_income + bal_non_operating
        row += 2
        account_worksheet.write(row, 0, 'Income before Tax', head_format_total)
        if is_debit_credit:
            account_worksheet.write(row, 1, '', cell_wrap_format)
            account_worksheet.write(row, 2, '', cell_wrap_format)
            account_worksheet.write(row, 3, bal_net_income_bf_tax, head_format)
            account_worksheet.write(row, 3, '=%s+%s' % (a1_notation_operating_income, a1_notation_non_operating), head_format, bal_net_income_bf_tax)
            a1_notation_income_bf_tax = xl_rowcol_to_cell(row, 3)
        else:
            account_worksheet.write(row, 1, bal_net_income_bf_tax, head_format)
            account_worksheet.write(row, 1, '=%s+%s' % (a1_notation_operating_income, a1_notation_non_operating), head_format, bal_net_income_bf_tax)
            a1_notation_income_bf_tax = xl_rowcol_to_cell(row, 1)

        # Company Income Tax
        row += 2
        title = 'Income Tax'
        account_worksheet.write(row, 0, title, head_format)
        account_tag_id = self.env.ref('kin_report.account_tag_income_tax')
        bal_income_tax, row, a1_notation_ref_income_tax = self.data_section(workbook, account_worksheet,
                                                               row, data, title,
                                                               account_tag_id,
                                                               is_debit_credit,
                                                               step=0)

        # Net Income
        bal_net_income = bal_net_income_bf_tax + bal_income_tax
        row += 2
        account_worksheet.write(row, 0, 'Net Income', head_format_total)
        if is_debit_credit:
            account_worksheet.write(row, 1, '', cell_wrap_format)
            account_worksheet.write(row, 2, '', cell_wrap_format)
            account_worksheet.write(row, 3, bal_net_income, head_format)
            account_worksheet.write(row, 3, '=%s+%s' % (a1_notation_income_bf_tax, a1_notation_ref_income_tax), head_format, bal_net_income)
        else:
            account_worksheet.write(row, 1, '=%s+%s' % (a1_notation_income_bf_tax, a1_notation_ref_income_tax), head_format,bal_net_income)

# The income.statement.parser in the IncomeStatementReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
IncomeStatementReportWriter('report.kin_report.report_income_statement', 'income.statement.parser',parser=report_sxw.rml_parse)


