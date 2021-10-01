# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api


class PFAReportWizard(models.TransientModel):
    _inherit = 'pfa.report.wizard'


    @api.multi
    def pfa_excel_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0] #converts all objects to lists that can be easily be passed to the report
        data = {'name': 'PFA Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'select_per': wiz_data['select_per'],'start_date' : wiz_data['start_date'],'end_date':wiz_data['end_date'],'pfa_ids' : wiz_data['pfa_ids']}
        return {
                     'name':'PFA Report',
                     'type': 'ir.actions.report.xml',
                    'report_name': 'rog_modifications.report_pfa_excel_rog',
                    'datas': data, #It is required you use datas as parameter, otherwise it will transfer data correctly.
                    }

    select_per = fields.Selection([('38', '38 %'), ('62', '62 % '), ('100', '100 % ')], default="38", string='Percentage')



