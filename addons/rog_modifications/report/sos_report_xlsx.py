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

class SOSReportWriter(ReportXlsx):


    def _get_order_details(self,start_date,end_date,product_id):
        sql_statement = """
                SELECT
                        sum(sol.product_uom_qty) as product_uom_qty,             
                        sum(sol.qty_delivered) as qty_delivered,   
                        sum(sol.transfer_created_qty) as transfer_created_qty,             
                        sum(sol.unloaded_balance_qty) as unloaded_balance_qty, 
                        sum(sol.cancelled_remaining_qty) as cancelled_qty ,
                        sum(sol.balance_qty) as balance_qty            
                    FROM sale_order_line as sol     
                    WHERE
                        sol.date_order >= %s 
                        and sol.date_order <= %s
                        and product_id = %s                  
                        and sol.state IN ('sale','done')
        """
        args = (start_date,end_date,product_id)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll


    def _get_last_invoice_line_date(self,start_date,end_date,product_id):
        sql_statement = """
                Select date from account_move_line
                where date = (SELECT MAX(date) 
                from account_move_line 
                where date >= %s
                and date <= %s
                and product_id = %s 
                and journal_id = 52 
                and debit > 0)              
        """
        args = (start_date,end_date,product_id)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll


    def _get_total_receipt(self,start_date,end_date):
        acc_id = 430
        sql_statement = """
                Select sum(credit) as total_receipt from account_move_line
                where date >= %s
                and date <= %s
                and account_id = %s
                and credit > 0
                and name = 'Customer Payment'              
        """
        args = (start_date,end_date,acc_id)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll


    def _get_last_receipt_date(self,start_date,end_date):
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
                and account_move_line.name = 'Customer Payment')                  
        """
        args = (start_date,end_date)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll


    def _get_balance_receivable(self,start_date,end_date):
        acc_id = 430
        sql_statement = """
                Select sum(balance) as balance from account_move_line
                 where date >= %s
                 and date <= %s
                 and account_id = %s                   
        """
        args = (start_date,end_date,acc_id)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_balance_receivable_deferred(self,start_date,end_date):
        acc_id = 430
        sql_statement = """
                Select sum(balance) as cum_bal from account_move_line
                 where date >= %s
                 and date <= %s
                 and account_id in (%s,533,734,735,736,737)    
                            
        """
        args = (start_date,end_date,acc_id)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll




    def generate_xlsx_report(self, workbook, data, objects):

        user_company = self.env.user.company_id

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
        cell_wrap_format = workbook.add_format({ 'valign': 'vcenter', 'font_size': 10, 'border': 1})
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

        report_worksheet.set_column(0, 0, 10)
        report_worksheet.set_column(1, 1, 20)
        report_worksheet.set_column(2, 2, 20)
        report_worksheet.set_column(3, 3, 30)
        report_worksheet.set_column(4, 4, 30)
        report_worksheet.set_column(5, 5, 30)
        report_worksheet.set_column(6, 6, 30)
        report_worksheet.set_column(7, 7, 30)
        report_worksheet.set_column(8, 8, 30)
        report_worksheet.set_column(9, 9, 30)
        report_worksheet.set_column(10, 10, 30)

        report_worksheet.set_row(row, 20)
        row += 1

        head_format_extra_white = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10,
             'bg_color': 'white', 'color': 'black'})
        head_format_extra_order = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10, 'bg_color': 'blue',
             'color': 'white'})
        head_format_extra_finance = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10,
             'bg_color': 'orange', 'color': 'white'})

        report_worksheet.merge_range(row, 1, row, 5, 'SALES ORDER STATUS (in Lts)', head_format_extra_order)
        report_worksheet.merge_range(row, 6, row, 8, 'FINANCIAL STATUS (in N)', head_format_extra_finance)
        row += 1

        report_worksheet.write_row(row, 0, ('Product',), head_format_extra_white)
        report_worksheet.write_row(row, 1, (
            'Total Order Qty. (ltrs)', 'Total Delivered Qty. (ltrs)', 'Total Transferred Qty. (ltrs)',
            'Cancelled Qty. (ltrs)', 'Balanced Qty. to be Delivered (ltrs)'), head_format_extra_order)
        # report_worksheet.write_row(row, 6, (
        #     'Date of ROG last Invoice (Date)', 'Amount so far Received (in N)', 'Last Date of Receipt (Dt)',
        #     'Balance  to be received (in N)', 'Excess to be returned (in N)'), head_format_extra_finance)
        report_worksheet.write_row(row, 6, ('Date of ROG last Invoice (Date)', 'Amount so far Received (in N)', 'Last Date of Receipt (Dt)'), head_format_extra_finance)

        product_obj = self.env['product.product']
        for product_id in product_ids:
            opening_bal = receipt = loaded = balance_product = physical_stock = opening_ticket_count = loc_dest_sum = loc_sum = issued_ticket_count = used_ticket_count = balance_ticket = to_be_loaded_count = 0
            report_worksheet.set_row(row, 20)
            row += 1
            product_name = product_obj.browse(product_id).name
            report_worksheet.write(row, 0, product_name, cell_wrap_format)

            #get order details
            data_list = self._get_order_details(start_date, end_date, product_id)

            product_uom_qty = data_list and data_list[0]['product_uom_qty'] or 0
            report_worksheet.write(row, 1, product_uom_qty, cell_number)

            qty_delivered = data_list and data_list[0]['qty_delivered'] or 0
            report_worksheet.write(row, 2, product_uom_qty, cell_number)

            transfer_created_qty = data_list and data_list[0]['transfer_created_qty'] or 0
            report_worksheet.write(row, 3, product_uom_qty, cell_number)

            cancelled_qty = data_list and data_list[0]['cancelled_qty'] or 0
            report_worksheet.write(row, 4, product_uom_qty, cell_number)

            balance_qty = data_list and data_list[0]['balance_qty'] or 0
            report_worksheet.write(row, 5, product_uom_qty, cell_number)

            # get last invoice date
            data_list = self._get_last_invoice_line_date(start_date, end_date, product_id)
            last_invoice_date = data_list and data_list[0]['date'] or 0
            if last_invoice_date:
                last_invoice_date = datetime.strptime(last_invoice_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                report_worksheet.write(row, 6, last_invoice_date, cell_number)

            # amount so far received
            data_list = self._get_total_receipt(start_date, end_date)
            payment_received = data_list and data_list[0]['total_receipt'] or 0
            report_worksheet.write(row, 7, payment_received, cell_number)

            # last date of receipt
            data_list = self._get_last_receipt_date(start_date, end_date)
            last_receipt_date = data_list and data_list[0]['date'] or 0
            if last_receipt_date:
                last_receipt_date = datetime.strptime(last_receipt_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                report_worksheet.write(row, 8, last_receipt_date, cell_number)

            # # balance to be received
            # data_list = self._get_balance_receivable(start_date, end_date)
            # bal_receivable = data_list and data_list[0]['balance'] or 0
            # report_worksheet.write(row, 9, bal_receivable, cell_number)
            #
            # # excess to be returned
            # data_list = self._get_balance_receivable_deferred(start_date, end_date)
            # rec_def = data_list and data_list[0]['cum_bal'] or 0
            # report_worksheet.write(row, 10, rec_def, cell_number)

        return



# The sales.report.wizard in the SalesReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
SOSReportWriter('report.rog_modifications.sos_excel_report_rog','sos.report.wizard')

