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
from openerp import tools
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp

# class CustomerStockStatementReport(models.Model):
#     _name = 'customer.stock.statment.report'
#     _auto = False
#



# class SalesOrderedLineView(models.Model):
#     _name = 'sale.ordered.qty.view'
#     _auto = False
#     # _rec_name = 'date'
#
#     name = fields.Text(string='Description', required=True)
#     product_id = fields.Many2one('product.product', string='Product')
#     product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))
#     product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
#     order_partner_id = fields.Many2one('res.partner',  string='Customer')
#
# class SalesTransferredLineView(models.Model):
#     _name = 'sale.transferred.qty.view'
#     _auto = False
#     # _rec_name = 'date'
#
#     def init(self, cr):
#         tools.drop_view_if_exists(cr, 'sale_transferred_qty_view')
#         cr.execute("""
#             create or replace view sale_transferred_qty_view as (
#                 select
#                     min(dl.id) as id,
#                     dl.name as name,
#                     dl.depreciation_date as depreciation_date,
#                     a.date as date,
#                     (CASE WHEN dlmin.id = min(dl.id)
#                       THEN a.value
#                       ELSE 0
#                       END) as gross_value,
#                     dl.amount as depreciation_value,
#                     dl.amount as installment_value,
#                     (CASE WHEN dl.move_check
#                       THEN dl.amount
#                       ELSE 0
#                       END) as posted_value,
#                     (CASE WHEN NOT dl.move_check
#                       THEN dl.amount
#                       ELSE 0
#                       END) as unposted_value,
#                     dl.asset_id as asset_id,
#                     dl.move_check as move_check,
#                     a.category_id as asset_category_id,
#                     a.partner_id as partner_id,
#                     a.state as state,
#                     count(dl.*) as installment_nbr,
#                     count(dl.*) as depreciation_nbr,
#                     a.company_id as company_id
#                 from account_asset_depreciation_line dl
#                     left join account_asset_asset a on (dl.asset_id=a.id)
#                     left join (select min(d.id) as id,ac.id as ac_id from account_asset_depreciation_line as d inner join account_asset_asset as ac ON (ac.id=d.asset_id) group by ac_id) as dlmin on dlmin.ac_id=a.id
#                 group by
#                     dl.amount,dl.asset_id,dl.depreciation_date,dl.name,
#                     a.date, dl.move_check, a.state, a.category_id, a.partner_id, a.company_id,
#                     a.value, a.id, a.salvage_value, dlmin.id
#         )""")
#
#     date_order = fields.Datetime(string='date')
#     name = fields.Text(string='Description', required=True)
#     product_id = fields.Many2one('product.product', string='Product')
#     product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))
#     product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
#     order_partner_id = fields.Many2one('res.partner',  string='Customer')
#
# class SalesCancelledLineView(models.Model):
#     _name = 'sale.cancelled.qty.view'
#     _auto = False
#     # _rec_name = 'date'
#
#     date_order = fields.Datetime(string='date')
#     name = fields.Text(string='Description', required=True)
#     product_id = fields.Many2one('product.product', string='Product')
#     product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))
#     product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
#     order_partner_id = fields.Many2one('res.partner',  string='Customer')
#
#
# class SalesOrderedLineView(models.Model):
#     _name = 'sale.ordered.qty.view'
#     _auto = False
#     # _rec_name = 'date'
#
#     date_order = fields.Datetime(string='date')
#     name = fields.Text(string='Description', required=True)
#     product_id = fields.Many2one('product.product', string='Product')
#     product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))
#     product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
#     order_partner_id = fields.Many2one('res.partner',  string='Customer')
#
# class StockMoveDoneQtyView(models.Model) :
#     _name = 'stock.move.done.qty.view'
#
#     date = fields.Datetime(string='Date')
#     name = fields.Text(string='Description', required=True)
#     product_id = fields.Many2one('product.product', string='Product')
#     product_uom_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'))
#     product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
#     partner_id = fields.Many2one('res.partner', string='Customer')


class CustomerStocKReportWriter(ReportXlsx):

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
        user_company = self.env.user.company_id
        list_dicts = self._get_data(data['form'])

        product_ids = data['form']['product_ids']
        if not product_ids :
            pro_ids = self.env['product.product'].search([('type','=','product')])
            for pr_id in pro_ids:
                product_ids.append(pr_id.id)


        report_worksheet = workbook.add_worksheet('Customer Stock Summary Report')
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 24})
        title_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        head_format = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10,'bg_color':'blue','color':'white'})
        head_format.set_num_format('#,#0.00')
        head_format_total = workbook.add_format({'bold': True, 'border': 1})
        head_sub_format_indent1 = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        head_sub_format_indent1.set_indent(1)
        cell_total_description = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_wrap_format = workbook.add_format({'valign': 'vjustify', 'font_size': 10, 'border': 1})
        cell_amount = workbook.add_format({'border': 1, 'font_size': 10})
        cell_amount.set_num_format('#,#0.00')
        cell_total_currency = workbook.add_format({'bold': True, 'border': 1, 'font_size': 10})
        cell_total_currency.set_num_format('#,#0.00')
        cell_number = workbook.add_format({'border': 1, 'font_size': 10})
        cell_number.set_num_format('#,#')

        # Header Format
        report_worksheet.set_row(0, 30)  # Set row height
        report_worksheet.merge_range(0, 0, 0, 10, user_company.name, header_format)

        # Title Format
        report_worksheet.set_row(2, 20)
        report_worksheet.merge_range(2, 0, 2, 10, 'Customer Stock Summary Report', title_format)

        # Period
        report_worksheet.merge_range(3, 0, 3, 10, 'Period: All', title_format)

        col = 0
        row = 5
        report_worksheet.set_column(0, 0, 5)
        report_worksheet.set_column(1, 1, 10)
        report_worksheet.set_column(2, 2, 25)
        report_worksheet.set_column(3, 17, 10)

        product_obj =  self.env['product.product']
        for product_id in product_ids :
            report_worksheet.set_row(row, 20)
            row += 2
            product_name = product_obj.browse(product_id).name
            report_worksheet.merge_range(row, col, row, 9, product_name, title_format)
            row += 2

            report_worksheet.write_row(row, col, ('S/N', 'Customer ID' , 'Customer', 'Product.', 'Ordered Qty.', 'Transferred Qty.', 'Cancelled Qty.', 'Un-Ticketed Qty.' , 'Ticketed Qty.', 'Loaded Qty.', 'Un-loaded Qty.', 'Balance Qty.', 'Invoiced', 'Un-Invoiced' ,'Unit Price' ,'Disc(%)', 'Disc. Amt.','Sub-total' ) , head_format)
            row += 1
            total_qty = 0
            first_row = row
            a1_notation_total_qty_start = xl_rowcol_to_cell(row, 1)
            sn = 0
            for list_dict in list_dicts:
                if list_dict['product_id'] == product_id :
                    sn += 1
                    report_worksheet.write(row, 0, sn,cell_wrap_format)
                    report_worksheet.write(row, 1, list_dict['customer_ref'], cell_wrap_format)
                    report_worksheet.write(row, 2, list_dict['customer_name'], cell_wrap_format)
                    report_worksheet.write(row, 3, list_dict['prod_name'], cell_wrap_format)
                    report_worksheet.write(row, 4, list_dict['product_uom_qty'], cell_number)
                    report_worksheet.write(row, 5, list_dict['transfer_created_qty'], cell_number)
                    report_worksheet.write(row, 6, list_dict['cancelled_remaining_qty'], cell_number)
                    report_worksheet.write(row, 7, list_dict['ticket_remaining_qty'], cell_number)
                    report_worksheet.write(row, 8, list_dict['ticket_created_qty'], cell_number)
                    report_worksheet.write(row, 9, list_dict['qty_delivered'], cell_number)
                    report_worksheet.write(row, 10, list_dict['unloaded_balance_qty'], cell_number)
                    report_worksheet.write(row, 11, list_dict['balance_qty'], cell_number)
                    report_worksheet.write(row, 12, list_dict['qty_invoiced'], cell_amount)
                    report_worksheet.write(row, 13, list_dict['qty_to_invoice'], cell_amount)
                    report_worksheet.write(row, 14, list_dict['price_unit'], cell_amount)
                    report_worksheet.write(row, 15, list_dict['discount'], cell_amount)
                    report_worksheet.write(row, 16, list_dict['discount_amt'], cell_amount)
                    report_worksheet.write(row, 17, list_dict['price_subtotal'], cell_amount)
                    row += 1
                    total_qty += list_dict['product_uom_qty']
                last_row  = row
                a1_notation_ref = xl_range(first_row, 4, last_row, 4)
                report_worksheet.write(row, 4, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_qty)
            row += 1
        return

# The sales.report.wizard in the SalesReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
CustomerStocKReportWriter('report.kin_loading.report_customer_stock','customer.stock.report.wizard')


