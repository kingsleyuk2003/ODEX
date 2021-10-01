# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw
from datetime import datetime


class StockLevelReportWriter(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, objects):
        stock_loc_ids = data['form']['stock_location_ids']
        stock_location_obj = self.env['stock.location']
        category_ids = data['form']['category_ids']
        product_categ_obj = self.env['product.category']
        the_date = datetime.today().strftime('%d %B %Y')
        user_company = self.env.user.company_id

        stock_location_ids = stock_location_obj.search([('id', 'in', stock_loc_ids)])
        product_categ_ids = product_categ_obj.search([('id', 'in', category_ids)])

        stock_level_parser = self.env['stock.level.parser']
        list_dicts = stock_level_parser._get_stock_level_data(data['form'])

        stock_level_worksheet = workbook.add_worksheet('stock level')
        header_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter','font_size':24})
        title_format = workbook.add_format({'bold': True,'underline':1, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        cell_product_category_format = workbook.add_format({'bold':True,'font_color':'blue'})
        cell_wrap_format = workbook.add_format({'valign':'vjustify','font_size':10})
        head_format = workbook.add_format({'bold':True})

        # Header Format
        stock_level_worksheet.set_row(2,30)  #Set row height
        stock_level_worksheet.merge_range(2,2,2,9,user_company.name,header_format)

        #Title Format
        stock_level_worksheet.set_row(4, 20)
        stock_level_worksheet.merge_range(4, 2, 4, 9, 'Current Stock Level as at %s '%(the_date), title_format)

        col = 2
        row = 5
        stock_level_worksheet.set_column(3,3, 50,cell_wrap_format)  # set column width with wrap format.
        for location_id in stock_location_ids :
            stock_level_worksheet.set_row(row, 20)
            row += 2
            stock_level_worksheet.merge_range(row, col, row, 9, location_id.name, title_format)
            row +=2
            stock_level_worksheet.write_row(row, col, ('S/N', 'Product', 'Quantity'),head_format)
            row += 1

            for category_id in product_categ_ids :
                row += 1
                sn = 1
                stock_level_worksheet.write(row, 3, category_id.name.upper(), cell_product_category_format)
                row += 1

                for list_dict in list_dicts :
                    if (list_dict['location_id'] == location_id.id) and (list_dict['categ_id'] == category_id.id) :
                        stock_level_worksheet.write(row,col,sn,cell_wrap_format)
                        stock_level_worksheet.write(row,3,list_dict['name'],cell_wrap_format)
                        stock_level_worksheet.write(row,4,list_dict['sum'],cell_wrap_format)
                        row += 1
                        sn += 1


StockLevelReportWriter('report.kin_stock_level.report_stock_level', 'stock.level.parser',parser=report_sxw.rml_parse)


