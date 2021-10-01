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

class ConsolidatedReportWriter(ReportXlsx):

    def _get_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        type = form['type']
        partner_id = form['partner_id']
        product_ids = form['product_ids']

        where_start_date = ''
        if start_date :
            where_start_date = "sol.date_order >= '%s' AND" % (start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        where_type = ''
        if type == 'is_throughput' :
            where_type = "sol.is_throughput_order = True AND"
        elif type == 'is_internal_use' :
            where_type = "sol.is_internal_use_order = True AND"
        elif type == 'is_indepot' :
            where_type = "sol.is_throughput_order = False AND sol.is_internal_use_order = False AND"
        elif type == 'all' :
            where_type = ""

        where_partner = ''
        if partner_id :
            where_partner = "sol.order_partner_id = '%s' AND" % (partner_id[0])

        where_prod = ''
        if product_ids:
            where_prod = "sol.product_id in (%s) AND" % ','.join(str(pr_id) for pr_id in product_ids)

        # LEFT JOIN works similar to INNER JOIN but with the extra advantage of showing empty join parameter fields (uncompulsory join fields). It is good for join fields that don't have value. It will still show the records. Unlike INNER JOIN (for compulsory join fields) which will omit those records
        sql_statement = """
            SELECT row_number() over(order by sol.date_order) as sn,
                sol.order_id,                
                sol.order_partner_id,                
                sol.product_uom_qty,
                sol.date_order, 
                sol.qty_delivered,   
                sol.transfer_created_qty,             
                sol.unloaded_balance_qty, 
                sol.balance_qty,
                sol.balance_amt,
                sol.product_id,
                sol.name as prod_name   ,
                customer.name as customer_name ,
                sol.price_unit
            FROM sale_order_line as sol
            LEFT JOIN res_partner as customer ON sol.order_partner_id = customer.id           
            LEFT JOIN sale_order as sale_order ON sol.order_id = sale_order.id
            WHERE
             """ + where_start_date +"""
             """ + where_type +"""
             """ + where_partner +"""
             """ + where_prod + """
             sol.date_order <= %s AND
             sol.cancelled_remaining_qty = 0 AND
              sol.state IN ('sale','done')
            """
        args = (end_date,)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_summary_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        type = form['type']
        partner_id = form['partner_id']
        product_ids = form['product_ids']

        where_start_date = ''
        if start_date :
            where_start_date = "sol.date_order >= '%s' AND" % (start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        where_type = ''
        if type == 'is_throughput' :
            where_type = "sol.is_throughput_order = True AND"
        elif type == 'is_internal_use' :
            where_type = "sol.is_internal_use_order = True AND"
        elif type == 'is_indepot' :
            where_type = "sol.is_throughput_order = False AND sol.is_internal_use_order = False AND"
        elif type == 'all' :
            where_type = ""

        where_partner = ''
        if partner_id :
            where_partner = "sol.order_partner_id = '%s' AND" % (partner_id[0])

        where_prod = ''
        if product_ids:
            where_prod = "sol.product_id in (%s) AND" % ','.join(str(pr_id) for pr_id in product_ids)

        # LEFT JOIN works similar to INNER JOIN but with the extra advantage of showing empty join parameter fields (uncompulsory join fields). It is good for join fields that don't have value. It will still show the records. Unlike INNER JOIN (for compulsory join fields) which will omit those records
        sql_statement = """
            SELECT row_number() over(order by sol.order_partner_id) as sn,          
                sol.order_partner_id,                
                sum(sol.product_uom_qty) as product_uom_qty,             
                sum(sol.qty_delivered) as qty_delivered,   
                sum(sol.transfer_created_qty) as transfer_created_qty,             
                sum(sol.unloaded_balance_qty) as unloaded_balance_qty, 
                sum(sol.balance_qty) as balance_qty,
                sum(sol.balance_amt) as balance_amt,
                sol.product_id,
                customer.name as customer_name
            FROM sale_order_line as sol
            LEFT JOIN res_partner as customer ON sol.order_partner_id = customer.id           
            LEFT JOIN sale_order as sale_order ON sol.order_id = sale_order.id
            WHERE
             """ + where_start_date +"""
             """ + where_type +"""
             """ + where_partner +"""
             """ + where_prod + """
             sol.date_order <= %s AND
             sol.cancelled_remaining_qty = 0 AND
              sol.state IN ('sale','done')
              GROUP BY customer_name,  sol.order_partner_id, sol.product_id
            """
        args = (end_date,)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll



    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        summary_detail = data['form']['summary_detail']
        list_dicts = []
        if summary_detail == 'summary':
            list_dicts = self._get_summary_data(data['form'])
        elif summary_detail == 'detail':
            list_dicts = self._get_data(data['form'])



        product_ids = data['form']['product_ids']
        if not product_ids :
            pro_ids = self.env['product.product'].search([('type','=','product')])
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

        type = data['form']['type']

        if type == 'is_throughput':
            if summary_detail == 'summary' :
                report_worksheet.merge_range(2, 0, 2, 7, 'Throughput Consolidated Summary Report', title_format)
            if summary_detail == 'detail' :
                report_worksheet.merge_range(2, 0, 2, 7, 'Throughput Consolidated Detailed Report', title_format)
        elif type == 'is_internal_use':
            if summary_detail == 'summary' :
                report_worksheet.merge_range(2, 0, 2, 7, 'Internal Use Consolidated Summary Report', title_format)
            if summary_detail == 'detail' :
                report_worksheet.merge_range(2, 0, 2, 7, 'Internal Use Consolidated Detailed Report', title_format)
        elif type == 'is_indepot':
            if summary_detail == 'summary' :
                report_worksheet.merge_range(2, 0, 2, 7, 'In Depot Consolidated Summary Report', title_format)
            if summary_detail == 'detail' :
                report_worksheet.merge_range(2, 0, 2, 7, 'In Depot Consolidated Detailed Report', title_format)
        elif type == 'all':
            if summary_detail == 'summary' :
                report_worksheet.merge_range(2, 0, 2, 7, 'All Consolidated Summary Report', title_format)
            if summary_detail == 'detail' :
                report_worksheet.merge_range(2, 0, 2, 7, 'All Consolidated Detailed Report', title_format)


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
        report_worksheet.set_column(1, 1, 20)
        report_worksheet.set_column(2, 2, 20)
        report_worksheet.set_column(3, 3, 20)
        report_worksheet.set_column(4, 4, 20)
        report_worksheet.set_column(5, 5, 20)
        report_worksheet.set_column(6, 6, 20)
        report_worksheet.set_column(7, 7, 20)
        report_worksheet.set_column(8, 8, 20)

        product_obj =  self.env['product.product']
        for product_id in product_ids :
            report_worksheet.set_row(row, 20)
            row += 2
            product_name = product_obj.browse(product_id).name
            report_worksheet.merge_range(row, col, row, 7, product_name, title_format)
            row += 2

            if summary_detail == 'summary':
                report_worksheet.write_row(row, col, ('Customer', 'Purchased Qty. (ltrs)',  'Loaded Qty. (ltrs)', 'Transferred Qty. (ltrs)' ,'Unused Tickets Qty. (ltrs)', 'Product Balance (ltrs)','Balance Amount (NGN)') , head_format)
            elif summary_detail == 'detail':
                report_worksheet.write_row(row, col, ('Customer', 'Purchased Qty. (ltrs)', 'Date' ,'Loaded Qty. (ltrs)', 'Transferred Qty. (ltrs)' , 'Transferred To','Unused Tickets Qty. (ltrs)', 'Product Balance (ltrs)', 'Balance Amount (NGN)' ) , head_format)


            row += 1
            total_product_uom_qty = total_qty_delivered = total_transfer_created_qty = total_unloaded_balance_qty = total_balance_qty = total_balance_amt = 0
            first_row = row
            a1_notation_total_qty_start = xl_rowcol_to_cell(row, 1)
            sale_order = self.env['sale.order']
            for list_dict in list_dicts:
                if list_dict['product_id'] == product_id :
                   # report_worksheet.write(row, 0, list_dict['sn'],cell_wrap_format)
                    report_worksheet.write(row, 0, list_dict['customer_name'], cell_wrap_format)
                    report_worksheet.write(row, 1, list_dict['product_uom_qty'], cell_number)
                    if summary_detail == 'detail':
                        order_id = list_dict['order_id']
                        transfer_to = []
                        for sot in sale_order.browse(order_id).child_sale_order_transfer_ids:
                            transfer_to.append(sot.partner_id.name + "(" + '{:,.0f}'.format(sot.order_line[0].product_uom_qty) + ")")
                        transfer_to = ', '.join(transfer_to)
                        report_worksheet.write(row, 2, datetime.strptime(list_dict['date_order'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S'), cell_wrap_format)
                        report_worksheet.write(row, 3, list_dict['qty_delivered'], cell_number)
                        report_worksheet.write(row, 4, list_dict['transfer_created_qty'], cell_number)
                        report_worksheet.write(row, 5, transfer_to, cell_wrap_format)
                        report_worksheet.write(row, 6, list_dict['unloaded_balance_qty'], cell_number)
                        report_worksheet.write(row, 7, list_dict['balance_qty'], cell_number)
                        report_worksheet.write(row, 8, list_dict['balance_amt'] , cell_number)
                    elif summary_detail == 'summary':
                        report_worksheet.write(row, 2, list_dict['qty_delivered'], cell_number)
                        report_worksheet.write(row, 3, list_dict['transfer_created_qty'], cell_number)
                        report_worksheet.write(row, 4, list_dict['unloaded_balance_qty'], cell_number)
                        report_worksheet.write(row, 5, list_dict['balance_qty'], cell_number)
                        report_worksheet.write(row, 6, list_dict['balance_amt'], cell_number)
                    row += 1
                    total_product_uom_qty += list_dict['product_uom_qty']
                    total_qty_delivered += list_dict['qty_delivered']
                    total_transfer_created_qty += list_dict['transfer_created_qty']
                    total_unloaded_balance_qty += list_dict['unloaded_balance_qty']
                    total_balance_qty += list_dict['balance_qty']
                    total_balance_amt += list_dict['balance_amt']
                last_row = row
                if summary_detail == 'detail':
                    a1_notation_ref = xl_range(first_row, 1, last_row, 1)
                    report_worksheet.write(row, 1, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_product_uom_qty)
                    a1_notation_ref = xl_range(first_row, 3, last_row, 3)
                    report_worksheet.write(row, 3, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_qty_delivered)
                    a1_notation_ref = xl_range(first_row, 4, last_row, 4)
                    report_worksheet.write(row, 4, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_transfer_created_qty)
                    a1_notation_ref = xl_range(first_row, 6, last_row, 6)
                    report_worksheet.write(row, 6, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_unloaded_balance_qty)
                    a1_notation_ref = xl_range(first_row, 7, last_row, 7)
                    report_worksheet.write(row, 7, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_balance_qty)
                    a1_notation_ref = xl_range(first_row, 8, last_row, 8)
                    report_worksheet.write(row, 8, '=SUM(' + a1_notation_ref + ')', cell_total_currency,total_balance_amt)
                elif summary_detail == 'summary':
                    a1_notation_ref = xl_range(first_row, 1, last_row, 1)
                    report_worksheet.write(row, 1, '=SUM(' + a1_notation_ref + ')', cell_total_currency,total_product_uom_qty)
                    a1_notation_ref = xl_range(first_row, 2, last_row, 2)
                    report_worksheet.write(row, 2, '=SUM(' + a1_notation_ref + ')', cell_total_currency,total_qty_delivered)
                    a1_notation_ref = xl_range(first_row, 3, last_row, 3)
                    report_worksheet.write(row, 3, '=SUM(' + a1_notation_ref + ')', cell_total_currency,total_transfer_created_qty)
                    a1_notation_ref = xl_range(first_row, 4, last_row, 4)
                    report_worksheet.write(row, 4, '=SUM(' + a1_notation_ref + ')', cell_total_currency,total_unloaded_balance_qty)
                    a1_notation_ref = xl_range(first_row, 5, last_row, 5)
                    report_worksheet.write(row, 5, '=SUM(' + a1_notation_ref + ')', cell_total_currency,total_balance_qty)
                    a1_notation_ref = xl_range(first_row, 6, last_row, 6)
                    report_worksheet.write(row, 6, '=SUM(' + a1_notation_ref + ')', cell_total_currency,total_balance_amt)
            row += 1
        return

# The sales.report.wizard in the SalesReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
ConsolidatedReportWriter('report.rog_modifications.consolidated_excel_report_rog','consolidated.report.wizard')

