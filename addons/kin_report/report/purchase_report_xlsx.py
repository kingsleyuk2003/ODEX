# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw
from datetime import datetime
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell


class PurchaseReportWriter(ReportXlsx):

    def _get_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        where_start_date = ''
        if not start_date :
            where_start_date = ''
        else:
            where_start_date = "purchase_order_line.date_order >= '%s' AND"%(start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')


        sql_statement = """
            SELECT
              row_number() over(order by purchase_order_line.date_order) as sn,
              purchase_order_line.product_qty,
              supplier.name as supplier_name,
              purchase_order_line.date_order,
              purchase_order_line.name as description,
              purchase_order_line.price_unit ,
              purchase_order_line.price_subtotal,
              purchase_order_line.discount,
              purchase_order_line.discount_amt,
              purchase_person.name as purchase_person ,
              purchase_order.name as purchase_order_name,
              purchase_order.partner_ref,
              res_currency.name as currency_name
            FROM
              purchase_order_line
              INNER JOIN res_partner as supplier ON purchase_order_line.partner_id = supplier.id
              INNER JOIN purchase_order ON purchase_order_line.order_id = purchase_order.id
              INNER JOIN res_users  ON purchase_order.user_id   = res_users.id
              INNER JOIN res_partner as purchase_person  ON res_users.partner_id = purchase_person.id
              INNER JOIN res_currency ON purchase_order_line.currency_id = res_currency.id
             WHERE
             """ + where_start_date +"""
             purchase_order_line.date_order <= %s AND
              purchase_order.state IN ('purchase','done')
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

        purchase_report_worksheet = workbook.add_worksheet('Purchase Report')
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
        purchase_report_worksheet.set_row(0, 30)  # Set row height
        purchase_report_worksheet.merge_range(0, 0, 0, 10, user_company.name, header_format)

        # Title Format
        purchase_report_worksheet.set_row(2, 20)
        purchase_report_worksheet.merge_range(2, 0, 2, 10, 'Purchase Report', title_format)

        # Period
        purchase_report_worksheet.set_row(3, 20)
        if start_date and end_date:
            purchase_report_worksheet.merge_range(3, 0, 3, 10,
                                          'Period: ' + datetime.strptime(start_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y') + '  to ' + datetime.strptime(end_date, '%Y-%m-%d').strftime(
                                              '%d/%m/%Y'), title_format)
        else:
            purchase_report_worksheet.merge_range(3, 0, 3, 10, 'Period: All', title_format)

        col = 0
        row = 5
        purchase_report_worksheet.set_column(row, 0, 5)  # set column width with wrap format.
        purchase_report_worksheet.set_column(row, 3, 7)

        purchase_report_worksheet.write_row(row, col, ('S/N', 'Qty' , 'Supplier', 'Order Date', 'Description','Unit Price', 'Purchase Price', 'Disc(%)', 'Disc. Amt.', 'Currency', 'Purchase Person', 'Purchase Order ID','Reference') , head_format)

        row += 1
        total_qty = 0
        first_row = row
        a1_notation_total_qty_start = xl_rowcol_to_cell(row, 1)
        for list_dict in list_dicts:
            purchase_report_worksheet.write(row, 0, list_dict['sn'],cell_wrap_format)
            purchase_report_worksheet.write(row, 1, list_dict['product_qty'], cell_wrap_format)
            purchase_report_worksheet.write(row, 2, list_dict['supplier_name'], cell_wrap_format)
            purchase_report_worksheet.write(row, 3, list_dict['date_order'], cell_wrap_format)
            purchase_report_worksheet.write(row, 4, list_dict['description'], cell_wrap_format)
            purchase_report_worksheet.write(row, 5, list_dict['price_unit'], cell_amount)
            purchase_report_worksheet.write(row, 6, list_dict['price_subtotal'], cell_amount)
            purchase_report_worksheet.write(row, 7,  list_dict['discount'], cell_amount)
            purchase_report_worksheet.write(row, 8, list_dict['discount_amt'], cell_amount)
            purchase_report_worksheet.write(row, 9 , list_dict['currency_name'],cell_wrap_format)
            purchase_report_worksheet.write(row, 10, list_dict['purchase_person'], cell_wrap_format)
            purchase_report_worksheet.write(row, 11, list_dict['purchase_order_name'], cell_wrap_format)
            purchase_report_worksheet.write(row, 12, list_dict['partner_ref'], cell_wrap_format)
            row += 1
            total_qty += list_dict['product_qty']
        last_row  = row
        a1_notation_ref = xl_range(first_row, 1, last_row, 1)
        purchase_report_worksheet.write(row, 1, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_qty)

# The purchase.report.wizard in the PurchaseReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
PurchaseReportWriter('report.kin_report.report_purchase_report','purchase.report.wizard',parser=report_sxw.rml_parse)


