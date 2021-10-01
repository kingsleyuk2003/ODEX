# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw
from datetime import datetime


class ActivityReportWriter(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, objects):

        lines = objects._get_activity_report_data(data['form'])

        the_date = datetime.today().strftime('%d %B %Y')
        start_date = datetime.strptime(data['form']['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        end_date = datetime.strptime(data['form']['end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        user_company = self.env.user.company_id
        rep_name = self.env['res.users'].browse(data['form']['rep_id'][0]).name

        activity_worksheet = workbook.add_worksheet(data['name'])
        header_format = workbook.add_format({'bold':True,'align':'center','valign':'vcenter','font_size':24})
        title_format = workbook.add_format({'bold': True,'underline':1, 'align': 'center', 'valign': 'vcenter', 'font_size': 14})
        cell_wrap_format = workbook.add_format({'valign':'vjustify','font_size':10})
        cell_total_currency = workbook.add_format({'font_size': 10})
        cell_total_currency.set_num_format('#,#00.00')
        head_format = workbook.add_format({'bold':True})
        cell_date = workbook.add_format({'font_size': 10})
        cell_date.set_num_format('dd/mm/yyyy')

        # Header Format
        activity_worksheet.set_row(2,30)  #Set row height
        activity_worksheet.merge_range(2,2,2,9,user_company.name,header_format)

        #Title Format
        activity_worksheet.set_row(4, 20)
        activity_worksheet.merge_range(4, 2, 4, 9, '%s\'s Activity Report from %s to %s '%(rep_name,start_date,end_date), title_format)

        col = 2
        row = 5
        activity_worksheet.set_column(3,3, 50,cell_wrap_format)  # set column width with wrap format.
        activity_worksheet.set_row(row, 20)
        row += 2
        activity_worksheet.write_row(row, col, ('S/N', 'Name', 'Phone/Mobile No.','Territory','Speciality','Product','Outcome','Next Appointment','Next Appointment Date','Activity Type','Description'), head_format)
        row += 1
        sn = 1
        for line in lines:
            activity_worksheet.write(row, col, sn, cell_wrap_format)
            activity_worksheet.write(row, 3, line.name or '', cell_wrap_format)
            activity_worksheet.write(row, 4, line.mobile or '', cell_wrap_format)
            activity_worksheet.write(row, 5, line.territory_id.name or '', cell_wrap_format)
            activity_worksheet.write(row, 6, line.speciality_id.name or '', cell_wrap_format)
            activity_worksheet.write(row, 7, line.product_id.name or '', cell_wrap_format)
            activity_worksheet.write(row, 8, line.outcome_id.name or '', cell_wrap_format)
            activity_worksheet.write(row, 9, line.appointment_id.name or '', cell_wrap_format)
            nad = ''
            if line.next_app_date : nad = datetime.strptime(line.next_app_date or '', '%Y-%m-%d')
            activity_worksheet.write(row, 10, nad or '', cell_date)
            activity_worksheet.write(row, 11, line.activity_type_id.name or '', cell_wrap_format)
            activity_worksheet.write(row, 12, line.description or '', cell_wrap_format)
            row += 1
            sn += 1
        return

# The activity.report.parser in the ActivityReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
ActivityReportWriter('report.kin_private_order_crm.report_activity_report', 'activity.report.parser',parser=report_sxw.rml_parse)


