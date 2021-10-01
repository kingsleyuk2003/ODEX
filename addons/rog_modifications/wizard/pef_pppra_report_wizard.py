# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017-2019  Kinsolve Solutions
# Copyright 2017-2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api


class PEFPPPRAReportWizard(models.TransientModel):
    _name = 'pef.pppra.wizard'


    @api.multi
    def pef_pppra_excel_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0]  # converts all objects to lists that can be easily be passed to the report
        data = {'name': 'PEF PPPRA Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'start_date': wiz_data['start_date'], 'end_date': wiz_data['end_date'],
                        'product_ids': wiz_data['product_ids']}
        return {
            'name': 'PEF PPPRA Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'rog_modifications.pef_pppra_report',
            'datas': data,  # It is required you use datas as parameter, otherwise it will transfer data correctly.

        }


    start_date = fields.Date('Date Issued/Paid Start Date')
    end_date = fields.Date('Date Issued/Paid End Date')
    product_ids = fields.Many2many('product.product', 'pef_pppra_prod_rel', 'pef_pppra_id', 'product_id', string='Products')



