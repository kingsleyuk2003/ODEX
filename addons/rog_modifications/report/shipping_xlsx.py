# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsxAbstract
# from odoo.report import report_sxw
from openerp import  models
from datetime import datetime
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw


class ShippingReport(ReportXlsx):

    def _get_data(self,objects):
        start_date = objects.start_date
        end_date = objects.end_date
        product_ids = objects.product_ids.ids


        if not product_ids :
            product_obj = self.env['product.product'].search([('white_product','in',['pms','ago','kero'])])
            for prod in product_obj:
                product_ids.append(prod.id)

        if not start_date :
            where_start_date = ''
        else:
            where_start_date = "ship_to_ship.date >= '%s' AND"%(start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        if not product_ids :
            where_product_ids = ''
        else:
            where_product_ids = "ship_to_ship.product_id in %s AND"

        sql_statement = """
            SELECT
                  date,
                  mf,
                  bank_qty,
                  supplier_id,
                  mv_vessel,
                  dv_vessel,
                  dv_bl_qty,
                  product_id,
                  tank_farm,
                  discharge_date,
                  shore_receipt,
                  shore_tank,
                  state
                FROM
                  ship_to_ship
                WHERE
                    state != 'cancel' AND
                    """ + where_start_date +"""
                    """ + where_product_ids + """
                      date <= %s
                ORDER BY
                    Date desc
            """
        args = (tuple(product_ids) or '',end_date,)
        self.env.cr.execute(sql_statement,args)
        dictAll = self.env.cr.dictfetchall()

        return dictAll


    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        list_dicts = self._get_data(objects)

        start_date = objects.start_date
        end_date = objects.end_date
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')

        control_report_worksheet = workbook.add_worksheet('Shipping Product Report')
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
        # control_report_worksheet.merge_range(0, 0, 0, 10, user_company.name, header_format)

        # Title Format
        control_report_worksheet.set_row(2, 20)
        # control_report_worksheet.merge_range(2, 0, 2, 10, 'Report', title_format)

        prod_names = ''
        product_ids = objects.product_ids.ids
        if product_ids:
            product_obj = self.env['product.product']
            products = product_obj.browse(product_ids)
            prod_names = ''
            for prod in products:
                prod_names += prod.name + ' '
            # control_report_worksheet.merge_range(4, 0, 4, 20, 'Products : ' + prod_names, head_format)

        if not product_ids :
            product_obj = self.env['product.product'].search([('white_product','in',['pms','ago','kero'])])
            for prod in product_obj:
                prod_names += prod.name + ' '

        # Period
        control_report_worksheet.set_row(0, 20)
        if start_date and end_date:
            start_date_format =  datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            end_date_format = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            control_report_worksheet.merge_range(0, 0, 0, 10,
                                          '%s %s REPORT FROM %s to %s' % (user_company.name,prod_names,start_date_format,end_date_format), title_format)
        else:
            control_report_worksheet.merge_range(0, 0, 0, 10, '%s %s REPORT FOR ALL PERIOD' % (user_company.name,prod_names), title_format)

        col = 0
        row = 2
        control_report_worksheet.set_column(row, 0, 7)  # set column width with wrap format.
        control_report_worksheet.set_column(row, 3, 7)

        control_report_worksheet.write_row(row, col, ('Date' , 'MF', 'BANK QTY (MT)', 'SUPPLIER','MV VESSEL', 'DV VESSEL', 'DV BL QTY (MT)', 'PRODUCT', 'TANK FARM', 'DISCH. DATE', 'SHORE RECEIPT (LTRS)','SHORE TAN (MT)') , head_format)

        row += 1
        total_shore_receipt = total_shore_tank = 0
        first_row = row
        for list_dict in list_dicts:
            control_report_worksheet.write(row, 0,  datetime.strptime(list_dict['date'], '%Y-%m-%d').strftime('%d/%m/%Y'), cell_wrap_format)
            control_report_worksheet.write(row, 1, list_dict['mf'], cell_wrap_format)
            control_report_worksheet.write(row, 2, list_dict['bank_qty'], cell_amount)
            control_report_worksheet.write(row, 3, list_dict['supplier_id'], cell_wrap_format)
            control_report_worksheet.write(row, 4, list_dict['mv_vessel'], cell_wrap_format)
            control_report_worksheet.write(row, 5, list_dict['dv_vessel'], cell_wrap_format)
            control_report_worksheet.write(row, 6,  list_dict['dv_bl_qty'], cell_amount)
            control_report_worksheet.write(row, 7, list_dict['product_id'], cell_wrap_format)
            control_report_worksheet.write(row, 8 , list_dict['tank_farm'],cell_wrap_format)
            control_report_worksheet.write(row, 9, datetime.strptime(list_dict['discharge_date'] or False, '%Y-%m-%d').strftime('%d/%m/%Y'), cell_wrap_format)
            control_report_worksheet.write(row, 10, list_dict['shore_receipt'], cell_amount)
            control_report_worksheet.write(row, 11, list_dict['shore_tank'], cell_amount)

            row += 1
            total_shore_receipt += list_dict['shore_receipt'] or 0
            total_shore_tank += list_dict['shore_tank'] or 0
        last_row  = row
        control_report_worksheet.write(row,9,'TOTAL RECEIPT',head_format)
        a1_notation_ref = xl_range(first_row, 10, last_row, 10)
        control_report_worksheet.write(row, 10, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_shore_receipt)
        a1_notation_ref = xl_range(first_row, 11, last_row, 11)
        control_report_worksheet.write(row, 11, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_shore_tank)
# The purchase.report.wizard in the PurchaseReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
ShippingReport('report.rog_modifications.shipping_report','shipping.wizard',parser=report_sxw.rml_parse)


