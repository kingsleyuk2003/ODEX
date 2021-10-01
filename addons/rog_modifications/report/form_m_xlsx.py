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


class FormMReport(ReportXlsx):

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
            where_start_date = "establishment_date >= '%s' AND"%(start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')

        sql_statement = """
            SELECT
                  dpr_import_licence_ref_no,
                  soncap_ref_no,
                  establishment_date,
                  bank,
                  form_m_no,
                  cb_ba_no,
                  product_id,
                  form_m_qty,
                  form_m_value,
                  trx_type,
                  supplier_id,
                  insurance_company_id,
                  insurance_amt,
                  form_m_expiry,
                  purchase_order.state,
                  product_template.name as product_name,
                  supplier.name  as supplier_name,
                  insurance.name as insurance_name          
                FROM
                  purchase_order
                  INNER JOIN purchase_order_line ON purchase_order.id = purchase_order_line.order_id
                  INNER JOIN product_product ON purchase_order_line.product_id = product_product.id
                  INNER JOIN product_template ON product_product.product_tmpl_id = product_template.id
                  INNER JOIN res_partner as supplier ON purchase_order.supplier_id = supplier.id
                  INNER JOIN res_partner as insurance ON purchase_order.insurance_company_id = insurance.id
                WHERE
                    purchase_order.state != 'cancel' AND
                    """ + where_start_date +"""
                     """ + where_products + """
                      establishment_date <= %s
                ORDER BY
                    establishment_date desc
            """
        args = (tuple(product_list_ids) or '',end_date,)
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

        report_worksheet = workbook.add_worksheet('Form M Report')
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
            start_date_format = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            end_date_format = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            report_worksheet.merge_range(0, 0, 0, 15,
                                         '%s FORM M REPORT FROM %s to %s' % (
                                         user_company.name, start_date_format, end_date_format), title_format)
        else:
            report_worksheet.merge_range(0, 0, 0, 10, '%s FORM M REPORT FOR ALL PERIOD' % (user_company.name),
                                         title_format)

        col = 0
        row = 2
        report_worksheet.set_column(row, 0, 7)  # set column width with wrap format.
        report_worksheet.set_column(row, 3, 7)

        report_worksheet.write_row(row, col, ('S/N','DPR IMPORT LICENCE REF NOS', 'SONCAP REF NOS', 'ESTABLISHMENT DATE','BANK', 'FORM M NOS', 'CB /BA NOS', 'PRODUCT', 'FORM M QTY (MT)', 'FORM M VALUE ($)', 'TRX TYPE LC/BC','NAME OF SUPPLIER','INSURANCE COMPANY','INSURANCE AMOUNT','FORM M EXPIRY DATE') , head_format)

        row += 1
        total_form_m_qty = total_form_m_value = 0
        first_row = row
        sn = 0
        for list_dict in list_dicts:
            sn += 1
            report_worksheet.write(row, 0,sn , cell_wrap_format)
            report_worksheet.write(row, 1, list_dict['dpr_import_licence_ref_no'], cell_wrap_format)
            report_worksheet.write(row, 2, list_dict['soncap_ref_no'], cell_wrap_format)
            if list_dict['establishment_date']:
                report_worksheet.write(row, 3, datetime.strptime(list_dict['establishment_date'], '%Y-%m-%d').strftime('%d/%m/%Y'), cell_wrap_format)
            else:
                report_worksheet.write(row, 3, '', cell_wrap_format)
            report_worksheet.write(row, 4, list_dict['bank'], cell_wrap_format)
            report_worksheet.write(row, 5, list_dict['form_m_no'], cell_wrap_format)
            report_worksheet.write(row, 6, list_dict['cb_ba_no'], cell_wrap_format)
            report_worksheet.write(row, 7, list_dict['product_name'], cell_wrap_format)
            report_worksheet.write(row, 8, list_dict['form_m_qty'], cell_amount)
            report_worksheet.write(row, 9, list_dict['form_m_value'], cell_amount)
            report_worksheet.write(row, 10, list_dict['trx_type'], cell_wrap_format)
            report_worksheet.write(row, 11, list_dict['supplier_name'], cell_wrap_format)
            report_worksheet.write(row, 12, list_dict['insurance_name'], cell_wrap_format)
            report_worksheet.write(row, 13, list_dict['insurance_amt'], cell_amount)
            report_worksheet.write(row, 14, datetime.strptime(list_dict['form_m_expiry'], '%Y-%m-%d').strftime('%d/%m/%Y'), cell_wrap_format)
            row += 1
            total_form_m_qty += list_dict['form_m_qty'] or 0
            total_form_m_value += list_dict['form_m_value'] or 0
        last_row  = row
        report_worksheet.write(row,7,'TOTAL',head_format)
        a1_notation_ref = xl_range(first_row, 8, last_row, 8)
        report_worksheet.write(row, 8, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_form_m_qty)
        a1_notation_ref = xl_range(first_row, 8, last_row, 8)
        report_worksheet.write(row, 8, '=SUM(' + a1_notation_ref + ')', cell_total_currency, total_form_m_value)

FormMReport('report.rog_modifications.form_m_report','form.m.wizard',parser=report_sxw.rml_parse)
