# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html


from openerp import api, fields, models, _


class BalanceSheetWizard(models.TransientModel):
    _name = 'balance.sheet.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }

    @api.multi
    def balance_sheet_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0] #converts all objects to lists that can be easily be passed to the report
        data = {'name': 'Balance Sheet Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'journal_ids' : wiz_data['journal_ids'],'operating_unit_ids' : wiz_data['operating_unit_ids'],'start_date' : wiz_data['start_date'],'end_date':wiz_data['end_date'],'is_debit_credit': wiz_data['is_debit_credit']}
        return {
                     'name':'Balance Sheet Report',
                     'type': 'ir.actions.report.xml',
                    'report_name': 'kin_report.report_balance_sheet',
                    'datas': data,  #It is required you use datas as parameter, otherwise it will transfer data correctly.
        }



    @api.onchange('date_range_id')
    def onchange_date_range(self):
        # self.ensure_one()
        self.start_date = self.date_range_id.date_start
        self.end_date = self.date_range_id.date_end



    date_range_id = fields.Many2one('date.range','Date Range',required=True)
    start_date = fields.Date('Start Date',required=True)
    end_date = fields.Date('End Date',required=True)
    is_debit_credit = fields.Boolean('Display Debit/Credit')
    operating_unit_ids = fields.Many2many('operating.unit', 'operating_unit_balance_sheet_rel', 'financialwizard_id', 'operateunit_id', string='Operating Units')
    journal_ids = fields.Many2many('account.journal','journal_balance_sheet_rel','financialwizard_id','journalid',string='Journals', default = lambda self : self.env['account.journal'].search([]))




