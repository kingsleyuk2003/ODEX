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

class SalesSummaryReportWriter(ReportXlsx):

    def _get_last_invoice_line_date(self,start_date,end_date,product_id,partner_id):
        sql_statement = """
                Select date from account_move_line
                where date = (SELECT MAX(date) 
                from account_move_line 
                where date >= %s
                and date <= %s
                and product_id = %s 
                and journal_id = 52 
                and debit > 0
                and partner_id = %s)              
        """
        args = (start_date,end_date,product_id,partner_id)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_last_receipt_date(self,start_date,end_date,partner_id):
        sql_statement = """
                Select date from account_move_line
                where date = (SELECT MAX(date) 
                from account_move_line 
                Left join account_journal
                on account_move_line.journal_id = account_journal.id
                where type in ('cash','bank')    
                and date >= %s
                and date <= %s          
                and credit > 0
                and account_move_line.name = 'Customer Payment'
                and partner_id = %s)                  
        """
        args = (start_date,end_date,partner_id)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_total_receipt(self,start_date,end_date,partner_id):
        acc_id = self.env['res.partner'].browse(partner_id).property_account_receivable_id.id
        sql_statement = """
                Select sum(credit) as total_receipt from account_move_line
                where date >= %s
                and date <= %s
                and account_id = %s
                and partner_id = %s 
                and credit > 0
                and name = 'Customer Payment'              
        """
        args = (start_date,end_date,acc_id,partner_id)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_balance_receivable(self,start_date,end_date,partner_id):
        acc_id = self.env['res.partner'].browse(partner_id).property_account_receivable_id.id
        sql_statement = """
                Select sum(balance) as balance from account_move_line
                 where date >= %s
                 and date <= %s
                 and account_id = %s    
                and partner_id = %s               
        """
        args = (start_date,end_date,acc_id,partner_id)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_balance_receivable_deferred(self,start_date,end_date,partner_id):
        acc_id = self.env['res.partner'].browse(partner_id).property_account_receivable_id.id
        sql_statement = """
                Select sum(balance) as cum_bal from account_move_line
                 where date >= %s
                 and date <= %s
                 and account_id in (%s,533,734,735,736,737)    
                and partner_id = %s               
        """
        args = (start_date,end_date,acc_id,partner_id)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_order_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        partner_id = form['partner_id']
        product_ids = form['product_ids']

        where_start_date = ''
        if start_date:
            where_start_date = "sol.date_order >= '%s' AND" % (start_date)

        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')

        where_type = "sol.is_throughput_order = False AND sol.is_internal_use_order = False AND"

        where_partner = ''
        if partner_id:
            where_partner = "sol.order_partner_id = '%s' AND" % (partner_id[0])

        where_prod = ''
        if product_ids:
            where_prod = "sol.product_id in (%s) AND" % ','.join(str(pr_id) for pr_id in product_ids)

        sql_statement = """
                    SELECT row_number() over(order by sol.order_partner_id) as sn,          
                        sol.order_partner_id,                
                        sum(sol.product_uom_qty) as product_uom_qty,             
                        sum(sol.qty_delivered) as qty_delivered,   
                        sum(sol.transfer_created_qty) as transfer_created_qty,             
                        sum(sol.unloaded_balance_qty) as unloaded_balance_qty, 
                        sum(sol.cancelled_remaining_qty) as cancelled_qty ,
                        sum(sol.balance_qty) as balance_qty,
                        sum(sol.balance_amt) as balance_amt,
                        sol.product_id,
                        customer.name as customer_name
                    FROM sale_order_line as sol
                    LEFT JOIN res_partner as customer ON sol.order_partner_id = customer.id           
                    LEFT JOIN sale_order as sale_order ON sol.order_id = sale_order.id
                    WHERE
                     """ + where_start_date + """
                     """ + where_type + """
                     """ + where_partner + """
                     """ + where_prod + """
                     sol.date_order <= %s AND
                      sol.state IN ('sale','done')
                      GROUP BY customer_name,  sol.order_partner_id, sol.product_id
                    """
        args = (end_date,)
        self.env.cr.execute(sql_statement, args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll



    def generate_xlsx_report(self, workbook, data, objects):

        user_company = self.env.user.company_id
        list_dicts = self._get_order_data(data['form'])

        product_ids = data['form']['product_ids']
        if not product_ids:
            pro_ids = self.env['product.product'].search([('type', '=', 'product')])
            for pr_id in pro_ids:
                product_ids.append(pr_id.id)

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
        report_worksheet.merge_range(2, 0, 2, 7, 'MANAGEMENT REPORT-SUMMARY OF SALES', title_format)

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
        report_worksheet.set_column(0, 0, 30)
        report_worksheet.set_column(1, 1, 10)
        report_worksheet.set_column(2, 2, 20)
        report_worksheet.set_column(3, 3, 20)
        report_worksheet.set_column(4, 4, 30)
        report_worksheet.set_column(5, 5, 30)
        report_worksheet.set_column(6, 6, 30)
        report_worksheet.set_column(7, 7, 30)
        report_worksheet.set_column(8, 8, 30)
        report_worksheet.set_column(9, 9, 30)
        report_worksheet.set_column(10, 10, 30)
        report_worksheet.set_column(11, 11, 30)

        product_obj = self.env['product.product']
        for product_id in product_ids:
            report_worksheet.set_row(row, 20)
            product_name = product_obj.browse(product_id).name
            report_worksheet.merge_range(row, col, row, 7, product_name, title_format)
            row += 2

            head_format_extra_white = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10, 'bg_color': 'white', 'color': 'black'})
            head_format_extra_order = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10, 'bg_color': 'blue', 'color': 'white'})
            head_format_extra_finance = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10, 'bg_color': 'orange', 'color': 'white'})
            report_worksheet.merge_range(row, 2, row, 6, 'SALES ORDER STATUS (in Lts)', head_format_extra_order)
            report_worksheet.merge_range(row, 7, row, 11, 'FINANCIAL STATUS (in N)', head_format_extra_finance)
            row += 1
            report_worksheet.write_row(row, 0, ('Customer Name',), head_format_extra_white)
            report_worksheet.write_row(row, 1, ('Product',), head_format_extra_white)
            report_worksheet.write_row(row, 2, ('Total Order Qty. (ltrs)', 'Total Delivered Qty. (ltrs)', 'Total Transferred Qty. (ltrs)', 'Cancelled Qty. (ltrs)', 'Balanced Qty. to be Delivered (ltrs)'), head_format_extra_order)
            report_worksheet.write_row(row, 7, ( 'Date of ROG last Invoice (Date)', 'Amount so far Received (in N)', 'Last Date of Receipt (Dt)', 'Balance  to be received (in N)', 'Excess to be returned (in N)'), head_format_extra_finance)
            row += 1
            total_product_uom_qty = total_qty_delivered = total_transfer_created_qty = total_cancelled_qty = total_balance_qty = total_payment_received = total_bal_receivable = total_bal_receivable_defferred = 0
            first_row = row
            a1_notation_total_qty_start = xl_rowcol_to_cell(row, 1)
            sale_order = self.env['sale.order']
            last_row = 0
            for list_dict in list_dicts:
                if list_dict['product_id'] == product_id:
                    # report_worksheet.write(row, 0, list_dict['sn'],cell_wrap_format)
                    report_worksheet.write(row, 0, list_dict['customer_name'], cell_wrap_format)
                    report_worksheet.write(row, 1, product_name, cell_wrap_format)
                    report_worksheet.write(row, 2, list_dict['product_uom_qty'], cell_number)
                    report_worksheet.write(row, 3, list_dict['qty_delivered'], cell_number)
                    report_worksheet.write(row, 4, list_dict['transfer_created_qty'], cell_number)
                    report_worksheet.write(row, 5, list_dict['cancelled_qty'],cell_number)
                    report_worksheet.write(row, 6, list_dict['balance_qty'], cell_number)

                    partner_id = list_dict['order_partner_id']

                    # get last invoice date
                    data_list = self._get_last_invoice_line_date(start_date, end_date, product_id, partner_id)
                    last_invoice_date = data_list and data_list[0]['date'] or 0
                    if last_invoice_date:
                        last_invoice_date = datetime.strptime(last_invoice_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                        report_worksheet.write(row, 7, last_invoice_date, cell_number)

                    #amount so far received
                    data_list = self._get_total_receipt(start_date, end_date, partner_id)
                    payment_received = data_list and data_list[0]['total_receipt'] or 0
                    report_worksheet.write(row, 8, payment_received, cell_number)

                    #last date of receipt
                    data_list = self._get_last_receipt_date(start_date, end_date, partner_id)
                    last_receipt_date = data_list and data_list[0]['date'] or 0
                    if last_receipt_date:
                        last_receipt_date = datetime.strptime(last_receipt_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                        report_worksheet.write(row, 9, last_receipt_date, cell_number)

                    #balance to be received
                    data_list = self._get_balance_receivable(start_date, end_date, partner_id)
                    bal_receivable = data_list and data_list[0]['balance'] or 0
                    report_worksheet.write(row, 10, bal_receivable, cell_number)

                    #excess to be returned
                    data_list = self._get_balance_receivable_deferred(start_date, end_date, partner_id)
                    rec_def = data_list and data_list[0]['cum_bal'] or 0
                    report_worksheet.write(row, 11, rec_def, cell_number)

                    row += 1
                    total_product_uom_qty += list_dict['product_uom_qty']
                    total_qty_delivered += list_dict['qty_delivered']
                    total_transfer_created_qty += list_dict['transfer_created_qty']
                    total_cancelled_qty += list_dict['cancelled_qty']
                    total_balance_qty += list_dict['balance_qty']
                    total_payment_received += payment_received
                    total_bal_receivable += bal_receivable
                    total_bal_receivable_defferred += rec_def

                last_row = row

            a1_notation_ref = xl_range(first_row, 2, last_row, 2)
            report_worksheet.write(row, 2, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_product_uom_qty)
            a1_notation_ref = xl_range(first_row, 3, last_row, 3)
            report_worksheet.write(row, 3, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_qty_delivered)
            a1_notation_ref = xl_range(first_row, 4, last_row, 4)
            report_worksheet.write(row, 4, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_transfer_created_qty)
            a1_notation_ref = xl_range(first_row, 5, last_row, 5)
            report_worksheet.write(row, 5, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_cancelled_qty)
            a1_notation_ref = xl_range(first_row, 6, last_row, 6)
            report_worksheet.write(row, 6, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_balance_qty)
            a1_notation_ref = xl_range(first_row, 8, last_row, 8)
            report_worksheet.write(row, 8, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_payment_received)
            a1_notation_ref = xl_range(first_row, 10, last_row, 10)
            report_worksheet.write(row, 10, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_bal_receivable)
            a1_notation_ref = xl_range(first_row, 11, last_row, 11)
            report_worksheet.write(row, 11, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_bal_receivable_defferred)
            row += 3
        return

# The sales.report.wizard in the SalesReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
SalesSummaryReportWriter('report.rog_modifications.sales_summary_excel_report_rog','sales.summary.report.wizard')

