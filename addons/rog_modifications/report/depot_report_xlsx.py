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

class DepotReportWriter(ReportXlsx):


    def _get_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        type = form['type']
        product_ids = form['product_ids']

        where_start_date = ''
        if start_date :
            where_start_date = "ticket_date >= '%s' AND" % (start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        where_type = ''
        where_type_sol = ''
        if type == 'is_throughput':
            where_type = "is_throughput_ticket = True AND"
            where_type_sol = "WHERE is_throughput_order = True"
        elif type == 'is_internal_use':
            where_type = "is_internal_use_ticket = True AND"
            where_type_sol = "WHERE is_internal_use_order = True"
        elif type == 'is_indepot':
            where_type = "is_indepot_ticket = True AND"
            where_type_sol = "WHERE is_throughput_order = False and is_internal_use_order = False"
        elif type == 'all':
            where_type = ""

        where_prod = ''
        if product_ids :
            where_prod = "product_id in (%s) AND" % ','.join(str(pr_id) for pr_id in product_ids)

        # LEFT JOIN works similar to INNER JOIN but with the extra advantage of showing empty join parameter fields (uncompulsory join fields). It is good for join fields that don't have value. It will still show the records. Unlike INNER JOIN (for compulsory join fields) which will omit those records
        sql_statement = """SELECT * FROM
                                (SELECT product_id, product_product.name_template as product_name, sum(total_dispatch_qty) as total_dispatched
                                  FROM stock_picking
                                  LEFT JOIN product_product ON stock_picking.product_id = product_product.id
                                  WHERE picking_type_code = 'outgoing'  and                               
                                    """ + where_start_date + """
                                    """ + where_type + """                       
                                    """ + where_prod + """     
                                    ticket_date <= %s 
                                  GROUP BY product_id,product_name) as total_dispatched
                                                                  
                                INNER JOIN 
                                
                                (SELECT count(*) as total_tickets, product_id 
                                FROM stock_picking
                                GROUP BY product_id) as total_tickets
                                ON total_dispatched.product_id = total_tickets.product_id
                                
                                INNER JOIN
                                
                                (SELECT count(loaded_date) as total_tickets_loaded,product_id
                                  FROM stock_picking
                                  GROUP BY product_id) as total_tickets_loaded
                                ON total_dispatched.product_id = total_tickets_loaded.product_id
                                
                                INNER JOIN                                
                                
                                (SELECT ((select count(*) from stock_picking  where picking_type_code = 'outgoing' and product_id = 6) - (select count(loaded_date) from stock_picking  where picking_type_code = 'outgoing' and product_id = 6)) as total_tickets_unloaded , product_id
                                  FROM stock_picking
                                  GROUP BY product_id) as total_tickets_unloaded
                                ON total_dispatched.product_id = total_tickets_unloaded.product_id
                                
                                 INNER JOIN 
                                
                                 (SELECT sum(transfer_created_qty) as total_qty_transferred, sum(balance_qty) as product_qty_balance,product_id 
                                 FROM sale_order_line 
                                  """ + where_type_sol + """ 
                                 GROUP BY product_id) as total_qty_transferred
                                ON total_dispatched.product_id = total_qty_transferred.product_id
                                
                                INNER JOIN 
                                
                                (SELECT  count(*) as total_tickets_cancelled ,product_id 
                                  FROM stock_picking
                                  WHERE state = 'cancel'
                                  GROUP BY product_id) as total_tickets_cancelled
                                 ON total_dispatched.product_id = total_tickets_cancelled.product_id                                   
                        """
        args = (end_date,)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll



    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        list_dicts = self._get_data(data['form'])

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
        report_worksheet.merge_range(0, 0, 0, 10, user_company.name, header_format)

        # Title Format
        report_worksheet.set_row(2, 20)

        type = data['form']['type']
        if type == 'is_throughput':
            report_worksheet.merge_range(2, 0, 2, 9, 'Throughput Depot Operations Summary Report', title_format)
        elif type == 'is_internal_use':
            report_worksheet.merge_range(2, 0, 2, 9, 'Throughput Depot Operations Summary Report', title_format)
        elif type == 'is_indepot':
            report_worksheet.merge_range(2, 0, 2, 9, 'In Depot Operations Summary Report', title_format)
        elif type == 'all':
            report_worksheet.merge_range(2, 0, 2, 9, 'All Depot Operations Summary Report', title_format)

        # Period
        report_worksheet.set_row(3, 20)
        if start_date and end_date:
            report_worksheet.merge_range(3, 0, 3, 9,
                                          'Period: ' + datetime.strptime(start_date, '%Y-%m-%d').strftime(
                                              '%d-%m-%Y') + '  to ' + datetime.strptime(end_date, '%Y-%m-%d').strftime(
                                              '%d-%m-%Y'), title_format)
        else:
            report_worksheet.merge_range(3, 0, 3, 7, 'All Period', title_format)

        col = 0
        row = 5
        report_worksheet.set_column(0, 0, 20)
        report_worksheet.set_column(1, 1, 20)
        report_worksheet.set_column(2, 2, 20)
        report_worksheet.set_column(3, 3, 20)
        report_worksheet.set_column(4, 4, 20)
        report_worksheet.set_column(5, 5, 20)
        report_worksheet.set_column(6, 6, 20)
        report_worksheet.set_column(7, 7, 20)
        report_worksheet.set_column(8, 8, 20)
        report_worksheet.set_column(9, 9, 20)

        report_worksheet.write_row(row, col, ('Product', 'Total Dispatched (ltrs)', 'Total Tickets (Count)','Total Tickets Loaded (Count)', 'Total Tickets Unloaded (Count)', 'Total Qty Transferred (ltrs)','Total Tickets Cancelled (Count)','Total Loaded Trucks (Count)','Total Unloaded Truck (Count)','Product Qty Balance (ltrs)'),
                                   head_format)

        row += 1
        sn = 0
        for list_dict in list_dicts:
            sn += 1
            report_worksheet.write(row, 0, list_dict['product_name'], cell_wrap_format)
            report_worksheet.write(row, 1, list_dict['total_dispatched'], cell_amount)
            report_worksheet.write(row, 2, list_dict['total_tickets'], cell_amount)
            report_worksheet.write(row, 3, list_dict['total_tickets_loaded'], cell_amount)
            report_worksheet.write(row, 4, list_dict['total_tickets_unloaded'], cell_amount)
            report_worksheet.write(row, 5, list_dict['total_qty_transferred'], cell_amount)
            report_worksheet.write(row, 6, list_dict['total_tickets_cancelled'], cell_amount)
            report_worksheet.write(row, 7, list_dict['total_tickets_loaded'], cell_amount)
            report_worksheet.write(row, 8, list_dict['total_tickets_unloaded'], cell_amount)
            report_worksheet.write(row, 9, list_dict['product_qty_balance'], cell_amount)
            row += 1
        return

# The sales.report.wizard in the SalesReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
DepotReportWriter('report.rog_modifications.depot_excel_report_rog','depot.report.wizard')

