# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api


class MLReportWizard(models.TransientModel):
    _name = 'ml.report.wizard'

    @api.multi
    def ml_excel_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0] #converts all objects to lists that can be easily be passed to the report
        data = {'name': 'Move Line Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'start_date' : wiz_data['start_date'],'end_date' : wiz_data['end_date'],'account_id' : wiz_data['account_id']}
        return {
                     'name':'Move Line Report',
                     'type': 'ir.actions.report.xml',
                    'report_name': 'rog_modifications.report_ml_excel_rog',
                    'datas': data, #It is required you use datas as parameter, otherwise it will transfer data correctly.
                    }

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    account_id = fields.Many2one('account.account',string='GL Account')
