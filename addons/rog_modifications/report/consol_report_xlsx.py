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



    def _get_opening_bal(self,start_date,location_ids,product_id):
        where_loc_from = "and location_id in (%s)" % ','.join(str(loc_id) for loc_id in location_ids)
        where_loc_dest = "and location_dest_id in (%s)" % ','.join(str(loc_id) for loc_id in location_ids)
        sql_statement = """
                select sum(product_qty) from stock_move 
                    where date < %s
                    and state = 'done' 
                    """ + where_loc_from + """
                    and product_id = %s  
                    Union
                    select sum(product_qty) from stock_move 
                    where date < %s
                    and state = 'done' 
                    """ + where_loc_dest + """
                    and product_id = %s   ;
        """
        args = (start_date,product_id,start_date,product_id)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_receipt(self,start_date,end_date,location_ids,product_id):
        where_loc = "and location_dest_id in (%s)" % ','.join(str(loc_id) for loc_id in location_ids)
        sql_statement = """
                select sum(product_qty) from stock_move 
                    where date >= %s 
                    and date <= %s
                    and state = 'done' 
                    """ + where_loc + """
                    and product_id = %s ;
        """
        args = (start_date,end_date,product_id)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_loaded(self,start_date,end_date,location_ids,product_id):
        where_loc = "and location_id in (%s)" % ','.join(str(loc_id) for loc_id in location_ids)
        sql_statement = """
                select sum(product_qty) from stock_move 
                    where date >= %s 
                    and date <= %s
                    and state = 'done' 
                    """ + where_loc + """
                    and product_id = %s ;
        """
        args = (start_date,end_date,product_id)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_physical_stock(self, end_date,location_ids,product_id):
        where_loc = "and stock_location_id in (%s)" % ','.join(str(loc_id) for loc_id in location_ids)
        sql_statement = """
                        select sum(physical_stock) from stock_reading_lines 
                            where read_date = %s 
                            and state = 'approve' 
                            """ + where_loc + """
                            and product_id = %s ;
                """
        args = (end_date, product_id)
        self.env.cr.execute(sql_statement, args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_opening_ticket_count(self,start_date,operation_type,product_id):
        where_type = ''
        if operation_type == 'is_throughput':
            where_type = "and is_throughput_ticket = True"
        elif operation_type == 'is_indepot':
            where_type = "and is_indepot_ticket = True"
        elif operation_type == 'all':
            where_type = ""

        sql_statement = """
                            SELECT count(*) from stock_picking
                            where ticket_date < %s
                            and is_loading_ticket = True
                            """ + where_type + """
                            and product_id = %s  
                             ;
                """
        args = (start_date, product_id)
        self.env.cr.execute(sql_statement, args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_issued_ticket_count(self,start_date,end_date,operation_type,product_id):
        where_type = ''
        if operation_type == 'is_throughput':
            where_type = "and is_throughput_ticket = True"
        elif operation_type == 'is_indepot':
            where_type = "and is_indepot_ticket = True"
        elif operation_type == 'all':
            where_type = ""

        sql_statement = """
                            SELECT count(*) from stock_picking
                            where ticket_date >= %s
                             and ticket_date <= %s
                            and is_loading_ticket = True
                            """ + where_type + """
                            and product_id = %s  
                             ;
                """
        args = (start_date,end_date, product_id)
        self.env.cr.execute(sql_statement, args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_used_ticket_count(self,start_date,end_date,operation_type,product_id):
        where_type = ''
        if operation_type == 'is_throughput':
            where_type = "and is_throughput_ticket = True"
        elif operation_type == 'is_indepot':
            where_type = "and is_indepot_ticket = True"
        elif operation_type == 'all':
            where_type = ""

        sql_statement = """
                            SELECT count(*) from stock_picking
                            where ticket_date >= %s
                             and ticket_date <= %s
                             and state = 'done'
                            and is_loading_ticket = True
                            """ + where_type + """
                            and product_id = %s  
                             ;
                """
        args = (start_date,end_date, product_id)
        self.env.cr.execute(sql_statement, args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def _get_to_be_loaded_count(self,start_date,end_date,operation_type,product_id):
        where_type = ''
        if operation_type == 'is_throughput':
            where_type = "and is_throughput_ticket = True"
        elif operation_type == 'is_indepot':
            where_type = "and is_indepot_ticket = True"
        elif operation_type == 'all':
            where_type = ""

        sql_statement = """
                            SELECT count(*) from stock_picking
                            where ticket_date >= %s
                             and ticket_date <= %s
                             and state not in ('done','cancel')
                            and is_loading_ticket = True
                            """ + where_type + """
                            and product_id = %s  
                             ;
                """
        args = (start_date,end_date, product_id)
        self.env.cr.execute(sql_statement, args)
        dictAll = self.env.cr.dictfetchall()
        return dictAll


    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id

        product_ids = data['form']['product_ids']
        if not product_ids :
            pro_ids = self.env['product.product'].search([('type','=','product'),('white_product','in',['ago','pms','kero','atk','lpfo'])])
            for pr_id in pro_ids:
                product_ids.append(pr_id.id)

        start_date = data['form']['start_date']
        end_date = data['form']['end_date']
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')

        location_ids = []
        loc_ids = False
        stock_location_obj = self.env['stock.location']
        type =  data['form']['type']
        if type == 'is_throughput':
            loc_ids = stock_location_obj.search([('usage','=','internal'),('is_throughput','=',True)])
        elif type == 'is_indepot':
            loc_ids = stock_location_obj.search([('usage','=','internal'),('is_indepot','=',True)])
        elif type == 'all':
            loc_ids = stock_location_obj.search([('usage','=','internal'),'|',('is_throughput','=',True),('is_indepot','=',True)])

        for loc_id in loc_ids:
            location_ids.append(loc_id.id)

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

        operation_type = data['form']['type']
        if operation_type == 'is_throughput':
            report_worksheet.merge_range(2, 0, 2, 7, 'THROUGHPUT MANAGEMENT REPORT-SUMMARY OF OPERATIONS', title_format)
        elif operation_type == 'is_indepot':
            report_worksheet.merge_range(2, 0, 2, 7, 'IN DEPOT MANAGEMENT REPORT-SUMMARY OF OPERATIONS', title_format)
        elif operation_type == 'all':
             report_worksheet.merge_range(2, 0, 2, 7, 'All MANAGEMENT REPORT-SUMMARY OF OPERATIONS', title_format)


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
        report_worksheet.set_column(9, 9, 20)
        report_worksheet.set_column(10, 10, 20)
        report_worksheet.set_column(11, 11, 20)
        report_worksheet.set_column(12, 12, 20)

        head_format_extra_product_name = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10, 'bg_color': 'white', 'color': 'black'})
        head_format_extra_product = workbook.add_format({'bold': True,'align':'center','valign':'vcenter','border': 1,'font_size':10,'bg_color':'blue','color':'white'})
        head_format_extra_ticket = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10, 'bg_color': 'orange','color': 'white'})
        head_format_extra_truck = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 10, 'bg_color': 'green','color': 'white'})
        report_worksheet.merge_range(5, 1, 5, 6, 'Product', head_format_extra_product)
        report_worksheet.merge_range(5, 7, 5, 10, 'Ticket', head_format_extra_ticket)
        report_worksheet.merge_range(5, 11, 5, 12, 'Trucks', head_format_extra_truck)
        row += 1
        report_worksheet.write_row(row, col, ('Product Name',), head_format_extra_product_name)
        report_worksheet.write_row(row, 1, ('Opening Balance (ltrs)', 'Receipt (ltrs)', 'Loaded (ltrs)', 'Balance (ltrs)', 'Physical Stock (ltrs)', 'Loss or Gain (ltrs)'), head_format_extra_product)
        report_worksheet.write_row(row, 7, ('Opening (Count)', 'Issued (Count)', 'Used (Count)', 'Balance (Count)'), head_format_extra_ticket)
        report_worksheet.write_row(row, 11, ('Loaded Nos (Count)', 'To be Loaded (Count)'), head_format_extra_truck)

        product_obj = self.env['product.product']
        for product_id in product_ids :
            opening_bal = receipt = loaded = balance_product = physical_stock = opening_ticket_count = loc_dest_sum = loc_sum = issued_ticket_count = used_ticket_count = balance_ticket = to_be_loaded_count = 0
            report_worksheet.set_row(row, 20)
            row += 1
            product_name = product_obj.browse(product_id).name
            report_worksheet.write(row, 0, product_name, cell_wrap_format)

            #get opening balance
            data_list = self._get_opening_bal(start_date,location_ids,product_id)
            if len(data_list) > 1 :
                if not data_list[1]['sum']:
                    loc_dest_sum = 0
                else:
                    loc_dest_sum = data_list[1]['sum']
            if not data_list[0]['sum']:
                loc_sum = 0
            else:
                loc_sum = data_list[0]['sum']
            opening_bal = abs(loc_sum - loc_dest_sum)
            report_worksheet.write(row, 1, opening_bal, cell_number)

            #get receipt
            data_list = self._get_receipt(start_date, end_date, location_ids, product_id)
            receipt = data_list[0]['sum'] or 0
            report_worksheet.write(row, 2, receipt, cell_number)

            # get loaded
            data_list = self._get_loaded(start_date, end_date, location_ids, product_id)
            loaded = data_list[0]['sum'] or 0
            report_worksheet.write(row, 3, loaded, cell_number)

            #balance
            balance_product = opening_bal + receipt - loaded
            report_worksheet.write(row, 4, balance_product, cell_number)

            #get physical stock
            data_list = self._get_physical_stock(end_date, location_ids, product_id)
            physical_stock = data_list[0]['sum'] or 0
            report_worksheet.write(row, 5, physical_stock, cell_number)

            #Loss or Gain
            report_worksheet.write(row, 6, physical_stock - balance_product, cell_number)

            #Opening Ticket
            data_list = self._get_opening_ticket_count(start_date,operation_type,product_id)
            opening_ticket_count = data_list[0]['count'] or 0
            report_worksheet.write(row, 7, opening_ticket_count, cell_number)

            # Issued Ticket
            data_list = self._get_issued_ticket_count(start_date,end_date,operation_type,product_id)
            issued_ticket_count = data_list[0]['count'] or 0
            report_worksheet.write(row, 8, issued_ticket_count, cell_number)

            # Used Ticket
            data_list = self._get_used_ticket_count(start_date, end_date, operation_type, product_id)
            used_ticket_count = data_list[0]['count'] or 0
            report_worksheet.write(row, 9, used_ticket_count, cell_number)

            #Balace ticket
            balance_ticket = opening_ticket_count + issued_ticket_count - used_ticket_count
            report_worksheet.write(row, 10, balance_ticket, cell_number)

            #Loaded Trucks
            report_worksheet.write(row, 11, used_ticket_count, cell_number)

            #To be loaded
            data_list = self._get_to_be_loaded_count(start_date, end_date, operation_type, product_id)
            to_be_loaded_count = data_list[0]['count'] or 0
            report_worksheet.write(row, 12, to_be_loaded_count, cell_number)

        return

# The sales.report.wizard in the SalesReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
ConsolidatedReportWriter('report.rog_modifications.consol_excel_report_rog','consol.report.wizard')

