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


class LoadingProgramme(ReportXlsx):

    def _get_data(self,form):
        partner_id = form['partner_id']
        product_ids = form['product_ids']

        where_partner = ''
        if partner_id :
            where_partner = "sol.order_partner_id = '%s' AND" % (partner_id[0])


        where_prod = ''
        if product_ids:
            where_prod = "sol.product_id in (%s) AND" % ','.join(str(pr_id) for pr_id in product_ids)

        # LEFT JOIN works similar to INNER JOIN but with the extra advantage of showing empty join parameter fields (uncompulsory join fields). It is good for join fields that don't have value. It will still show the records. Unlike INNER JOIN (for compulsory join fields) which will omit those records
        sql_statement = """
            SELECT
               sum(sol.qty_to_invoice) as qty_to_invoice, sum(sol.price_unit) as price_unit, sum(sol.product_uom_qty) as product_uom_qty,
               sum(sol.qty_invoiced) as qty_invoiced,
               sum(sol.price_subtotal) as price_subtotal, sum(sol.discount) as discount, sum(sol.price_reduce) as price_reduce,
               sum(sol.qty_delivered) as qty_delivered, sum(sol.price_total) as price_total,
               sum(sol.purchase_price) as purchase_price, sum(sol.margin) as margin, sum(sol.discount_amt) as discount_amt,
               sum(sol.qty_available) as qty_available, sum(sol.product_ticket_qty) as product_ticket_qty,
               sum(sol.ticket_remaining_qty) as ticket_remaining_qty, sum(sol.ticket_created_qty) as ticket_created_qty,
               sum(sol.transfer_created_qty) as transfer_created_qty, sum(sol.cancelled_remaining_qty) as cancelled_remaining_qty,
               sum(sol.unloaded_balance_qty) as unloaded_balance_qty, sum(sol.balance_qty) as balance_qty,
               sol.name as prod_name,sol.product_id, customer.name as customer_name , customer.ref as customer_ref
            FROM sale_order_line as sol
            LEFT JOIN res_partner as customer ON sol.order_partner_id = customer.id
            WHERE
             """ + where_partner +"""
             """ + where_prod + """
             sol.state IN ('sale','done')
            GROUP BY customer_name , customer_ref, product_id, prod_name
            """
        self.env.cr.execute(sql_statement)
        dictAll = self.env.cr.dictfetchall()

        return dictAll


    def generate_xlsx_report(self, workbook, data, objects):

        prog_id = data['active_ids'][0]
        prog_obj = self.env['loading.programme'].browse(prog_id)

        report_worksheet = workbook.add_worksheet('Loading Programme Excel')
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 24})
        title_format = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'font_size': 14})
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

        # Title Format
        report_worksheet.set_row(1, 20)
        date_time_format =  datetime.strptime(prog_obj.programme_date, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %I:%M:%S %p')
        report_worksheet.merge_range(1, 0, 1, 7,
                                     '%s' % (prog_obj.env.user.company_id.name),
                                     title_format)
        report_worksheet.merge_range(3, 0, 3, 7, 'LOADING PROGRAMME %s       Date and Time: %s'  % (prog_obj.name,date_time_format), title_format)

        col = 0
        row = 1
        row += 4
        report_worksheet.set_column(0,0,5)
        report_worksheet.set_column(1, 1,10)
        report_worksheet.set_column(2, 2, 10)
        report_worksheet.set_column(3, 3,10)
        report_worksheet.set_column(4, 4, 20)
        report_worksheet.set_column(5, 6, 20)
        report_worksheet.set_column(7, 7, 10)
        report_worksheet.set_column(8, 8, 10)
        report_worksheet.set_column(9, 9, 10)
        report_worksheet.write_row(row, col, (
        'S/N', 'TICKET NO.', 'TRUCK NO.' ,'PRD.', 'QTY.', 'COY NAME', 'RECEIVING ADDRESS','LOCATION', 'STATE','STATION CODE' ,'DPR NO.'), head_format)
        row += 1
        sn = 0
        total_qty = 0
        first_row = row
        for ticket in prog_obj.ticket_ids :
            sn += 1
            report_worksheet.write(row, 0, sn, cell_wrap_format)
            report_worksheet.write(row, 1, ticket.name, cell_wrap_format)
            report_worksheet.write(row, 2, ticket.truck_no, cell_wrap_format)
            report_worksheet.write(row, 3, ticket.product_id.name, cell_wrap_format)
            report_worksheet.write(row, 4, ticket.ticket_load_qty, cell_amount)
            report_worksheet.write(row, 5, ticket.partner_id.name, cell_wrap_format)
            report_worksheet.write(row, 6, ticket.receiving_station_address, cell_wrap_format)
            report_worksheet.write(row, 7, ticket.location_addr_id, cell_wrap_format)
            report_worksheet.write(row, 8, ticket.dpr_state if ticket.dpr_state else '' , cell_wrap_format)
            report_worksheet.write(row, 9, ticket.station_code if ticket.station_code else '', cell_wrap_format)
            report_worksheet.write(row, 10, ticket.dpr_no, cell_wrap_format)
            total_qty += ticket.ticket_load_qty
            row += 1
        # last_row = row
        # a1_notation_ref = xl_range(first_row, 3, last_row, 3)
        # report_worksheet.write(row, 2,'Total QTY.',head_format)
        # report_worksheet.write(row, 3, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_qty)
        row += 4
        report_worksheet.merge_range(row, 0, row, 5, 'ROG/OPS/038                                                  REV.00', cell_wrap_format)
        return

# The sales.report.wizard in the SalesReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
LoadingProgramme('report.kin_loading.report_loading_programme_excel','loading.programme.wizard')


