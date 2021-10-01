# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import  models
from datetime import datetime
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw

class PEFPPPRAReport(ReportXlsx):

    def _get_data(self,objects):
        start_date = objects.start_date
        end_date = objects.end_date

        product_ids = objects.product_ids
        product_list_ids =[]
        if not product_ids :
            product_obj = self.env['product.product'].search([])
            for pd in product_obj:
                product_list_ids.append(pd.id)
        else:
            for pd in product_ids:
                product_list_ids.append(pd.id)

        if not product_list_ids :
            where_products = ''
        else:
            where_products = "product_id in %s AND"

        if not start_date :
            where_start_date = ''
        else:
            where_start_date = "issue_date_paid >= '%s' AND"%(start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        sql_statement = """
            SELECT
                  issue_date_paid,
                  name_of_vessel,
                  product_id,
                  purchase_order.volume as volume,
                  purchase_order.rate_pef as pef_rate,
                  pef_payment,
                  status_payment_pef,
                  purchase_order.rate_pppra as pppra_rate,
                  admin_charge,
                  status_payment_pppra,
                  lc_bc_pfi,
                  in_house_no,
                  product_template.name as product_name
                FROM
                  purchase_order
                  INNER JOIN purchase_order_line ON purchase_order.id = purchase_order_line.order_id
                  INNER JOIN product_product ON purchase_order_line.product_id = product_product.id
                  INNER JOIN product_template ON product_product.product_tmpl_id = product_template.id
                WHERE
                    purchase_order.state != 'cancel' AND
                    """ + where_start_date +"""
                    """ + where_products + """
                      issue_date_paid <= %s
                ORDER BY
                    issue_date_paid desc
            """
        args = (tuple(product_list_ids) or '', end_date,)
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

        report_worksheet = workbook.add_worksheet('PEF and PPPRA Report')
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
        report_worksheet.set_row(0, 30)  # Set row height
        # report_worksheet.merge_range(0, 0, 0, 10, user_company.name, header_format)

        # Title Format
        report_worksheet.set_row(2, 20)
        # report_worksheet.merge_range(2, 0, 2, 10, 'Report', title_format)

        # Period
        report_worksheet.set_row(0, 20)
        if start_date and end_date:
            start_date_format =  datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            end_date_format = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            report_worksheet.merge_range(0, 0, 0, 15,
                                          '%s PEF & PPPRA PAYMENT REPORT FROM %s to %s' % (user_company.name,start_date_format,end_date_format), title_format)
        else:
            report_worksheet.merge_range(0, 0, 0, 10, '%s PEF & PPPRA PAYMENT REPORT FOR ALL PERIOD' % (user_company.name), title_format)

        col = 0
        row = 2
        report_worksheet.set_column(row, 0, 7)  # set column width with wrap format.
        report_worksheet.set_column(row, 3, 7)

        report_worksheet.write_row(row, col, ('DATE ISSUED/PAID' , 'NAME OF VESSEL', 'PRODUCT', 'VOLUME (LTRS)','RATE', 'PEF PAYMENT', 'STATUS OF PAYMENT', 'RATE', 'ADMIN CHARGE (PPPRA PAYMENT)', 'STATUS OF PAYMENT', 'LC/BC/PFI','IN - HOUSE NO.') , head_format)

        row += 1
        total_volume = total_pef_payment = 0
        first_row = row
        for list_dict in list_dicts:
            if list_dict['issue_date_paid'] :
                report_worksheet.write(row, 0, datetime.strptime(list_dict['issue_date_paid'], '%Y-%m-%d').strftime('%d/%m/%Y'), cell_wrap_format)
            else:
                report_worksheet.write(row, 0, '', cell_wrap_format)
            report_worksheet.write(row, 1, list_dict['name_of_vessel'], cell_wrap_format)
            report_worksheet.write(row, 2, list_dict['product_name'], cell_amount)
            report_worksheet.write(row, 3, list_dict['volume'], cell_amount)
            report_worksheet.write(row, 4, list_dict['pef_rate'], cell_amount)
            report_worksheet.write(row, 5, list_dict['pef_payment'], cell_amount)
            report_worksheet.write(row, 6,  list_dict['status_payment_pef'], cell_wrap_format)
            report_worksheet.write(row, 7, list_dict['pppra_rate'], cell_amount)
            report_worksheet.write(row, 8 , list_dict['status_payment_pppra'],cell_wrap_format)
            report_worksheet.write(row, 10, list_dict['lc_bc_pfi'], cell_wrap_format)
            report_worksheet.write(row,11,list_dict['in_house_no'],cell_wrap_format)

            row += 1
            total_volume += list_dict['volume'] or 0
            total_pef_payment += list_dict['pef_payment'] or 0
        last_row  = row
        report_worksheet.write(row,2,'TOTAL',head_format)
        a1_notation_ref = xl_range(first_row, 3, last_row, 3)
        report_worksheet.write(row, 3, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_volume)
        a1_notation_ref = xl_range(first_row, 5, last_row, 5)
        report_worksheet.write(row, 5, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_pef_payment)


PEFPPPRAReport('report.rog_modifications.pef_pppra_report','pef.pppra.wizard',parser=report_sxw.rml_parse)
