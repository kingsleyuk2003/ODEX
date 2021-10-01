# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw
from datetime import datetime
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell


class KinStockControlWriter(ReportXlsx):

    def _get_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        retail_station_ids = form['retail_station_ids']

        if not retail_station_ids :
            retail_station_obj = self.env['kin.retail.station'].search([])
            for rt in retail_station_obj:
                retail_station_ids.append(rt.id)

        if not start_date :
            where_start_date = ''
        else:
            where_start_date = "kin_stock_control.stock_control_date >= '%s' AND"%(start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        if not retail_station_ids :
            where_retail_stations = ''
        else:
            where_retail_stations = "kin_stock_control.retail_station_id in %s AND"



        sql_statement = """
            SELECT
                  kin_stock_control.stock_control_date as Date,
                  sum(kin_pump_sale.meter_start) as Meter_Start,
                  sum(kin_pump_sale.meter_end) as Meter_End,
                  sum(kin_pump_sale.rtt) as RTT,
                  sum(kin_pump_sale.sale_qty) as Sale_Qty,
                  sum(kin_pump_sale.price_subtotal) as Price_Subtotal,
                  sum(kin_tank_dipping.opening_stock) as Opening_Stock,
                  sum(kin_tank_dipping.stock_received) as Stock_Received,
                  sum(kin_tank_dipping.current_int_transfer_in) as Internal_IN,
                  sum(kin_tank_dipping.current_int_transfer_out) as Internal_OUT,
                  sum(kin_tank_dipping.stock_at_hand) as Stock_at_hand,
                  sum(kin_tank_dipping.closing_stock) as Closing_Stock,
                  sum(kin_tank_dipping.throughput) as Throughput
                FROM
                  kin_pump_sale
                  INNER JOIN kin_stock_control ON kin_pump_sale.stock_control_id = kin_stock_control.id
                  INNER JOIN kin_tank_dipping ON kin_tank_dipping.stock_control_id  = kin_stock_control.id
                WHERE
                    kin_stock_control.state != 'draft' AND
                    """ + where_start_date +"""
                    """ + where_retail_stations + """
                      kin_stock_control.stock_control_date <= %s
                GROUP BY
                    Date
                ORDER BY
                    Date desc
            """
        args = (tuple(retail_station_ids) or '',end_date,)
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

        control_report_worksheet = workbook.add_worksheet('Control Report')
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 24})
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        head_format = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
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
        control_report_worksheet.set_row(0, 30)  # Set row height
        control_report_worksheet.merge_range(0, 0, 0, 10, user_company.name, header_format)

        # Title Format
        control_report_worksheet.set_row(2, 20)
        control_report_worksheet.merge_range(2, 0, 2, 10, 'Control Report', title_format)

        # Period
        control_report_worksheet.set_row(3, 20)
        if start_date and end_date:
            control_report_worksheet.merge_range(3, 0, 3, 10,
                                          'Period: ' + datetime.strptime(start_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y') + '  to ' + datetime.strptime(end_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y'), title_format)
        else:
            control_report_worksheet.merge_range(3, 0, 3, 10, 'Period: All', title_format)

        retail_station_ids = data['form']['retail_station_ids']
        if retail_station_ids:
            retail_station_obj = self.env['kin.retail.station']
            retail_stations = retail_station_obj.browse(retail_station_ids)
            rt_names = ''
            for rt in retail_stations:
                rt_names += rt.name + ','
            control_report_worksheet.merge_range(4, 0, 4, 20, 'Retail Stations: ' + rt_names, head_format)

        col = 0
        row = 6
        control_report_worksheet.set_column(row, 0, 7)  # set column width with wrap format.
        control_report_worksheet.set_column(row, 3, 7)

        control_report_worksheet.write_row(row, col, ('Date' , 'Meter Start', 'Meter End', 'Return to Tank','Sales Qty.', 'Amount', 'Opening Stock', 'Stock Received', 'INT. TRAN. IN', 'INT. TRAN. OUT', 'Stock at Hand','Closing Stock','ThroughPut') , head_format)

        row += 1
        total_qty = total_amt = 0
        first_row = row
        for list_dict in list_dicts:
            control_report_worksheet.write(row, 0,  datetime.strptime(list_dict['date'], '%Y-%m-%d').strftime('%d/%m/%Y'), cell_wrap_format)
            control_report_worksheet.write(row, 1, list_dict['meter_start'], cell_amount)
            control_report_worksheet.write(row, 2, list_dict['meter_end'], cell_amount)
            control_report_worksheet.write(row, 3, list_dict['rtt'], cell_amount)
            control_report_worksheet.write(row, 4, list_dict['sale_qty'], cell_amount)
            control_report_worksheet.write(row, 5, list_dict['price_subtotal'], cell_amount)
            control_report_worksheet.write(row, 6,  list_dict['opening_stock'], cell_amount)
            control_report_worksheet.write(row, 7, list_dict['stock_received'], cell_amount)
            control_report_worksheet.write(row, 8 , list_dict['internal_in'],cell_amount)
            control_report_worksheet.write(row, 9, list_dict['internal_out'], cell_amount)
            control_report_worksheet.write(row, 10, list_dict['stock_at_hand'], cell_amount)
            control_report_worksheet.write(row, 11, list_dict['closing_stock'], cell_amount)
            control_report_worksheet.write(row, 12, list_dict['throughput'], cell_amount)
            row += 1
            total_qty += list_dict['sale_qty']
            total_amt += list_dict['price_subtotal']
        last_row  = row
        a1_notation_ref = xl_range(first_row, 4, last_row, 4)
        control_report_worksheet.write(row, 4, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_qty)
        a1_notation_ref = xl_range(first_row, 5, last_row, 5)
        control_report_worksheet.write(row, 5, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_amt)
# The purchase.report.wizard in the PurchaseReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
KinStockControlWriter('report.kin_retail_station_rog.stock_control_report','kin.stock.control.wizard',parser=report_sxw.rml_parse)


