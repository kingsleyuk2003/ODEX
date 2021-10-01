# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2020  Kinsolve Solutions
# Copyright 2020 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api
from datetime import datetime

class BankReportWizard(models.TransientModel):
    _name = 'bank.report.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }

    @api.multi
    def bank_excel_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0] #converts all objects to lists that can be easily be passed to the report
        data = {'name': 'Bank / Cash Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'start_date' : wiz_data['start_date'],'end_date':wiz_data['end_date']}

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

        return {
                    'name':'Bank / Cash Report' + " (" + date_str + ")",
                    'type': 'ir.actions.report.xml',
                    'report_name': 'rog_modifications.bank_excel_report_rog',
                    'datas': data, #It is required you use datas as parameter, otherwise it will transfer data correctly.
                    }

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')



