# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api


class PayeReportWizard(models.TransientModel):
    _inherit = 'paye.report.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }

    @api.multi
    def paye_excel_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0] #converts all objects to lists that can be easily be passed to the report
        data = {'name': 'PAYE Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'select_per': wiz_data['select_per'],'start_date' : wiz_data['start_date'],'end_date':wiz_data['end_date']}
        return {
                     'name':'PAYE Report',
                     'type': 'ir.actions.report.xml',
                    'report_name': 'rog_modifications.report_paye_excel_rog',
                    'datas': data, #It is required you use datas as parameter, otherwise it will transfer data correctly.
                    }

    select_per = fields.Selection([('38', '38 %'), ('62', '62 % '), ('100', '100 % ')], default="38", string='Percentage')



