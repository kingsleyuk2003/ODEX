# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import  models
from datetime import datetime


class CaseFileReport(models.AbstractModel):
    _name = 'report.rog_legal.case_file_report'
    _inherit = 'report.report_xlsx.abstract'

    def _get_data(self,objects):
        start_date = objects.start_date
        end_date = objects.end_date

        if not start_date :
            where_start_date = ''
        else:
            where_start_date = "open_dispute_date >= '%s' AND"%(start_date)

        if not end_date :
            end_date = datetime.today().strftime('%Y-%m-%d')


        sql_statement = """
            SELECT
                  open_dispute_date,
                  close_dispute_date,
                  case_file_no,
                  plantiff,
                  defendant,
                  suit_number,
                  court_name,
                  judge_magistrate_name,
                  location,
                  state,
                  description
                FROM
                  legal_case
                WHERE
                    state != 'cancel' AND
                    """ + where_start_date +"""
                      open_dispute_date <= %s
                ORDER BY
                    open_dispute_date desc
            """
        args = (end_date,)
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

        report_worksheet = workbook.add_worksheet('Case File Register Report')
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
            report_worksheet.merge_range(0, 0, 0, 10,
                                          '%s CASE FILE REPORT FROM %s to %s' % (user_company.name,start_date_format,end_date_format), title_format)
        else:
            report_worksheet.merge_range(0, 0, 0, 10, '%s CASE FILE REPORT FOR ALL PERIOD' % (user_company.name), title_format)

        col = 0
        row = 2
        report_worksheet.set_column(row, 0, 7)  # set column width with wrap format.
        report_worksheet.set_column(row, 3, 7)

        report_worksheet.write_row(row, col, ('Open Dispute Date' , 'Close Dispute Date','Case File No.', 'Claimant / Plantiff', 'Defendant','Suit Number','Court Name','Judge / Magistrate Name' ,'Location', 'Status','Case Description') , head_format)

        row += 1
        for list_dict in list_dicts:
            report_worksheet.write(row, 0, datetime.strptime(list_dict['open_dispute_date'], '%Y-%m-%d').strftime('%d/%m/%Y'), cell_wrap_format)
            if list_dict['close_dispute_date']:
                report_worksheet.write(row, 1, datetime.strptime(list_dict['close_dispute_date'],'%Y-%m-%d').strftime('%d/%m/%Y'), cell_wrap_format)
            else:
                report_worksheet.write(row, 1, '', cell_wrap_format)
            report_worksheet.write(row, 2, list_dict['case_file_no'], cell_wrap_format)
            report_worksheet.write(row, 3, list_dict['plantiff'], cell_wrap_format)
            report_worksheet.write(row, 4, list_dict['defendant'], cell_wrap_format)
            report_worksheet.write(row, 5, list_dict['defendant'], cell_wrap_format)
            report_worksheet.write(row, 6, list_dict['suit_number'], cell_wrap_format)
            report_worksheet.write(row, 7, list_dict['court_name'], cell_wrap_format)
            report_worksheet.write(row, 8, list_dict['judge_magistrate_name'], cell_wrap_format)
            report_worksheet.write(row, 9, list_dict['location'], cell_wrap_format)
            report_worksheet.write(row, 10, list_dict['state'], cell_wrap_format)
            report_worksheet.write(row, 11, list_dict['description'], cell_wrap_format)
            row += 1
