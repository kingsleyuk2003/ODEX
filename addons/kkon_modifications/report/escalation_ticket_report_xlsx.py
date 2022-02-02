# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2020  Kinsolve Solutions
# Copyright 2020 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsxAbstract
# from odoo.report import report_sxw
from openerp import models
from datetime import datetime
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from openerp.report import report_sxw
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz


class EscalationTicketReport(ReportXlsx):

    def _get_data(self, form):
        start_date = form.start_date
        end_date = form.end_date
        category_id = form['category_id'][0].id
        company_id = form['company_id'][0].id

        if not start_date:
            where_start_date = ''
        else:
            where_start_date = "open_date >= '%s' AND" % (start_date)
        if not end_date:
            where_end_date = "open_date <= '%s'" % datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        else:
            where_end_date = "open_date <= '%s'" % (end_date)

        if category_id:
            where_category = "category_id = %s AND" % (category_id)

        if company_id:
            where_company = "ticket_company_id = %s AND" % (company_id)

        if company_id:
            where_company = "ticket_company_id = %s AND" % (company_id)

        sql_statement = """
                SELECT     
                  kin_ticket.partner_id as partner_id,           
                  kin_ticket.name as name,
                  user_ticket_group_id,
                  open_date,
                  done_ticket_date,
                  closed_date,
                  time_spent,
                  is_major_support,                  
                  total_elapsed_hours_first_support,
                  total_elapsed_hours_second_support,
                  total_elapsed_hours_major_support,
                  current_escalation_level_support,
                  is_service_relocation,
                  total_elapsed_hours_first,
                  total_elapsed_hours_second,
                  total_elapsed_hours_third,                  
                  current_escalation_level_service_relocation,
                  state
                FROM
                  kin_ticket
                WHERE  
                   (is_service_relocation IS NOT NULL OR 
                   is_major_support IS NOT NULL) AND                  
                    state != 'cancel' AND                   
                    """ + where_category + """ 
                     """ + where_company + """
                      """ + where_start_date + """
                       """ + where_end_date + """                
            """
        self.env.cr.execute(sql_statement)
        dictAll = self.env.cr.dictfetchall()
        return dictAll

    def generate_xlsx_report(self, workbook, data, objects):
        user_company = self.env.user.company_id
        list_dicts = self._get_data(objects)

        start_date = objects.start_date
        end_date = objects.end_date
        category_id = objects.category_id.id
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        user_tz_obj = pytz.timezone(self.env.context.get('tz') or 'utc')
        localize_tz = pytz.utc.localize

        control_report_worksheet = workbook.add_worksheet('Escalation Ticket Report')
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

        cat_name = objects.category_id.name
        # Period
        control_report_worksheet.set_row(0, 20)
        if start_date and end_date:
            start_date_format = localize_tz(datetime.strptime(start_date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p')
            end_date_format = localize_tz(datetime.strptime(end_date, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p')
            control_report_worksheet.merge_range(0, 0, 0, 10,
                                                 '%s %s ESCALATION TICKET REPORT FROM %s to %s' % (
                                                 user_company.name, cat_name, start_date_format, end_date_format),
                                                 title_format)
        else:
            control_report_worksheet.merge_range(0, 0, 0, 10,
                                                 '%s %s ESCALATION TICKET REPORT FOR ALL PERIOD' % (user_company.name, cat_name),
                                                 title_format)

        col = 0
        row = 2
        control_report_worksheet.set_column(0, 0, 30)
        control_report_worksheet.set_column(1, 1, 15)
        control_report_worksheet.set_column(2, 2, 10)
        control_report_worksheet.set_column(3, 3, 30)
        control_report_worksheet.set_column(4, 4, 15)
        control_report_worksheet.set_column(5, 5, 15)
        control_report_worksheet.set_column(6, 6, 15)
        control_report_worksheet.set_column(7, 7, 15)

        control_report_worksheet.set_column(8, 8, 15)
        control_report_worksheet.set_column(9, 9, 20)
        control_report_worksheet.set_column(10, 10, 20)
        control_report_worksheet.set_column(11, 11, 20)
        control_report_worksheet.set_column(12, 12, 30)
        control_report_worksheet.set_column(13, 13, 15)

        if category_id == 3:
            control_report_worksheet.write_row(row, col, ('Title','Open DateTime','Client ID', 'Customer','Assigned Group','Completed DateTime', 'Closed DateTime', 'Time Spent', 'Is Major Support Ticket', 'Elapsed Hours (First)',  'Elapsed Hours (Second)', 'Elapsed Hours (Third)' ,'Current Escalation level' , 'Stage'), head_format)
        elif category_id == 7:
            control_report_worksheet.write_row(row, col, ( 'Title', 'Open DateTime', 'Client ID', 'Customer', 'Assigned Group', 'Completed DateTime', 'Closed DateTime',   'Time Spent', 'Is Service Relocation', 'Elapsed Hours (First)',  'Elapsed Hours (Second)', 'Elapsed Hours (Third)' , 'Current Escalation level', 'Stage'), head_format)


        user_ticket_group_obj = self.env['user.ticket.group']
        res_partner_obj = self.env['res.partner']

        row += 1
        for list_dict in list_dicts:
            control_report_worksheet.write(row, 0, list_dict['name'], cell_wrap_format)
            control_report_worksheet.write(row, 1, localize_tz(datetime.strptime(list_dict['open_date'], '%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict['open_date'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 2, res_partner_obj.sudo().browse(list_dict['partner_id']).ref or '',cell_wrap_format)
            control_report_worksheet.write(row, 3, res_partner_obj.sudo().browse(list_dict['partner_id']).name or '', cell_wrap_format)
            control_report_worksheet.write(row, 4, user_ticket_group_obj.sudo().browse(list_dict['user_ticket_group_id']).name or '', cell_wrap_format)
            control_report_worksheet.write(row, 5, localize_tz(datetime.strptime(list_dict['done_ticket_date'], '%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime('%d/%m/%Y %I:%M:%S %p') if list_dict['done_ticket_date'] else '', cell_wrap_format)
            control_report_worksheet.write(row, 6, (localize_tz(datetime.strptime(list_dict['closed_date'], '%Y-%m-%d %H:%M:%S')).astimezone(user_tz_obj).strftime('%d/%m/%Y %H:%%I:%M:%S %p:%S') if list_dict['closed_date'] else ''), cell_wrap_format)
            control_report_worksheet.write(row, 7, list_dict['time_spent'], cell_wrap_format)

            if category_id == 3 :
                control_report_worksheet.write(row, 8, list_dict['is_major_support'], cell_wrap_format)
                control_report_worksheet.write(row, 9, list_dict['total_elapsed_hours_first_support'], cell_wrap_format)
                control_report_worksheet.write(row, 10, list_dict['total_elapsed_hours_second_support'], cell_wrap_format)
                control_report_worksheet.write(row, 11, list_dict['total_elapsed_hours_major_support'], cell_wrap_format)
                control_report_worksheet.write(row, 12, list_dict['current_escalation_level_support'], cell_wrap_format)
                control_report_worksheet.write(row, 13, list_dict['state'], cell_wrap_format)
            elif category_id == 7 :
                control_report_worksheet.write(row, 8, list_dict['is_service_relocation'], cell_wrap_format)
                control_report_worksheet.write(row, 9, list_dict['total_elapsed_hours_first'], cell_wrap_format)
                control_report_worksheet.write(row, 10, list_dict['total_elapsed_hours_second'], cell_wrap_format)
                control_report_worksheet.write(row, 11, list_dict['total_elapsed_hours_third'], cell_wrap_format)
                control_report_worksheet.write(row, 12, list_dict['current_escalation_level_service_relocation'], cell_wrap_format)
                control_report_worksheet.write(row, 13, list_dict['state'], cell_wrap_format)

            row += 1


# The purchase.report.wizard in the PurchaseReportWriter function call, represents the "objects" parameter in the generate_xlsx_report function
EscalationTicketReport('report.kkon_modifications.escalation_ticket_report', 'escalation.ticket.wizard', parser=report_sxw.rml_parse)


