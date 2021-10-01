# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp import api, fields, models, _


class BalanceSheetWizard(models.TransientModel):
    _inherit = 'balance.sheet.wizard'


    @api.multi
    def balance_sheet_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0]
        data = {'name': 'Statement of Fin. Position', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'journal_ids' : wiz_data['journal_ids'],'operating_unit_ids' : wiz_data['operating_unit_ids'],'start_date' : wiz_data['start_date'],'end_date':wiz_data['end_date'],'is_debit_credit': wiz_data['is_debit_credit']}
        return {
                     'name':'Statement of Financial Position Report',
                     'type': 'ir.actions.report.xml',
                    'report_name': 'agary_modifications.report_balance_sheet_agary',
                    'datas': data,
                    }



