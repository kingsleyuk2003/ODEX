# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell


class SalesReportWriter(ReportXlsx):

    def _get_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        company_id = form['company_id'][0]
        operating_unit_ids = form['operating_unit_ids']
        from_ou = ''
        where_ou = ''
        where_start_date = ''
        if not start_date :
            where_start_date = ''
        else:
            where_start_date = "sale_order_line.date_order >= '%s' AND"%(start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        if company_id:
            where_company = "sale_order_line.company_id = %s AND" % (company_id)

        if operating_unit_ids :
            from_ou =  "INNER JOIN operating_unit ON sale_order.operating_unit_id = operating_unit.id "
            where_ou = "sale_order.operating_unit_id in (%s) AND" % ','.join(str(ou_id) for ou_id in operating_unit_ids)

        sql_statement = """
            SELECT
              row_number() over(order by sale_order_line.date_order) as sn,
              sale_order_line.product_uom_qty,
              customer.name as customer_name,
              sale_order_line.date_order,
              sale_order_line.name as description,
              sale_order_line.price_unit ,
              sale_order_line.price_subtotal,
              sale_order_line.purchase_price,
              sale_order_line.discount,
              sale_order_line.discount_amt,
              sale_order_line.margin,
              res_partner.name as sales_person ,
              sale_order.name as sale_order_name,
              sale_order.client_order_ref,
              qty_to_invoice,
              qty_invoiced,
              qty_delivered,
              res_currency.name as currency_name
            FROM
              sale_order_line
              INNER JOIN res_partner as customer ON sale_order_line.order_partner_id = customer.id
              INNER JOIN res_users  ON sale_order_line.salesman_id = res_users.id
              INNER JOIN res_partner  ON res_users.partner_id = res_partner.id
              INNER JOIN sale_order ON sale_order_line.order_id = sale_order.id
              INNER JOIN res_currency ON sale_order_line.currency_id = res_currency.id
              """ + from_ou + """
             WHERE
             """ + where_start_date +"""
             """ + where_company + """
             """ + where_ou + """
             sale_order_line.date_order <= %s AND
              sale_order_line.state IN ('sale','done')
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
        operating_unit_ids = data['form']['operating_unit_ids']
        ous = ''
        if operating_unit_ids :
            for operating_unit_id in operating_unit_ids:
                ou_name = self.env['operating.unit'].browse(operating_unit_id).name
                ous +=',' + ou_name
        else:
            ous = 'All Operating Units'

        sales_report_worksheet = workbook.add_worksheet('Sales Report')
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
        sales_report_worksheet.set_row(0, 30)  # Set row height
        sales_report_worksheet.merge_range(0, 0, 0, 10, user_company.name, header_format)

        # Title Format
        sales_report_worksheet.set_row(2, 20)
        sales_report_worksheet.merge_range(2, 0, 2, 10, 'Sales Report for %s ' % ous.strip(',') , title_format)

        # Period
        sales_report_worksheet.set_row(3, 20)
        if start_date and end_date:
            sales_report_worksheet.merge_range(3, 0, 3, 10,
                                          'Period: ' + datetime.strptime(start_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y') + '  to ' + datetime.strptime(end_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y'), title_format)
        else:
            sales_report_worksheet.merge_range(3, 0, 3, 10, 'Period: All', title_format)

        col = 0
        row = 5
        sales_report_worksheet.set_column(row, 0, 5)  # set column width with wrap format.
        sales_report_worksheet.set_column(row, 3, 7)

        sales_report_worksheet.write_row(row, col, ('S/N', 'Qty' , 'Customer', 'Order Date', 'Description','Unit Price' , 'Selling Price', 'Cost Price', 'Disc(%)', 'Disc. Amt.', 'Margin','Currency', 'Sales Person', 'Sales Order ID','Reference','Qty. To Invoice','Qty. Invoiced','Qty Delivered') , head_format)

        row += 1
        total_qty = 0
        first_row = row
        a1_notation_total_qty_start = xl_rowcol_to_cell(row, 1)
        for list_dict in list_dicts:
            sales_report_worksheet.write(row, 0, list_dict['sn'],cell_wrap_format)
            sales_report_worksheet.write(row, 1, list_dict['product_uom_qty'], cell_wrap_format)
            sales_report_worksheet.write(row, 2, list_dict['customer_name'], cell_wrap_format)
            sales_report_worksheet.write(row, 3, datetime.strptime(list_dict['date_order'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S'), cell_wrap_format)
            sales_report_worksheet.write(row, 4, list_dict['description'], cell_wrap_format)
            sales_report_worksheet.write(row, 5, list_dict['price_unit'], cell_amount)
            sales_report_worksheet.write(row, 6, list_dict['price_subtotal'], cell_amount)
            sales_report_worksheet.write(row, 7,  list_dict['purchase_price'], cell_amount)
            sales_report_worksheet.write(row, 8, list_dict['discount'], cell_amount)
            sales_report_worksheet.write(row, 9, list_dict['discount_amt'], cell_amount)
            sales_report_worksheet.write(row, 10, list_dict['margin'], cell_amount)
            sales_report_worksheet.write(row, 11 , list_dict['currency_name'],cell_wrap_format)
            sales_report_worksheet.write(row, 12, list_dict['sales_person'], cell_wrap_format)
            sales_report_worksheet.write(row, 13, list_dict['sale_order_name'], cell_wrap_format)
            sales_report_worksheet.write(row, 14, list_dict['client_order_ref'], cell_wrap_format)
            sales_report_worksheet.write(row, 15, list_dict['qty_to_invoice'], cell_wrap_format)
            sales_report_worksheet.write(row, 16, list_dict['qty_invoiced'], cell_wrap_format)
            sales_report_worksheet.write(row, 17, list_dict['qty_delivered'], cell_wrap_format)
            row += 1
            total_qty += list_dict['product_uom_qty']
        last_row  = row
        a1_notation_ref = xl_range(first_row, 1, last_row, 1)
        sales_report_worksheet.write(row, 1, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_qty)


# The sales.report.wizard in the SalesReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
SalesReportWriter('report.kin_report.report_sales_report','sales.report.wizard')


