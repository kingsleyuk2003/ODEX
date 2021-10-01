# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2020  Kinsolve Solutions
# Copyright 2020 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api
from datetime import datetime

class ConsolReportWizard(models.TransientModel):
    _name = 'consol.report.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }

    @api.multi
    def consol_excel_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0] #converts all objects to lists that can be easily be passed to the report
        data = {'name': 'consol Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'start_date' : wiz_data['start_date'],'end_date':wiz_data['end_date'],'type':wiz_data['type'], 'product_ids' : wiz_data['product_ids']}

        date_str = ''
        start_date = wiz_data['start_date']
        end_date = wiz_data['end_date']
        if not end_date:
            end_date = datetime.today().strftime('%Y-%m-%d')

        if start_date and end_date:
            date_str = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d-%m-%Y') + '  to ' + datetime.strptime(
                end_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        else:
            date_str = 'All Period'

        name = ' '
        type = wiz_data['type']
        if type == 'is_throughput':
            name = 'THROUGHPUT MANAGEMENT REPORT-SUMMARY OF OPERATIONS' + " (" + date_str + ")"
        elif type == 'is_indepot':
            name = 'IN DEPOT Depot MANAGEMENT REPORT-SUMMARY OF OPERATIONS' + " (" + date_str + ")"
        elif type == 'all':
            name = 'All MANAGEMENT REPORT-SUMMARY OF OPERATIONS' + " (" + date_str + ")"


        return {
                    'name': name ,
                    'type': 'ir.actions.report.xml',
                    'report_name': 'rog_modifications.consol_excel_report_rog',
                    'datas': data, #It is required you use datas as parameter, otherwise it will transfer data correctly.
                    }

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    product_ids = fields.Many2many('product.product', 'consol_report_product_rel', 'consol_wizard_id', 'prod_id', string='Products')
    type =  fields.Selection( [('is_indepot', 'In Depot'), ('is_throughput', 'Throughput'), ('all', 'All Operation Type')],string='Operation Type')


