# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api


class SalesLoadingReportWizard(models.TransientModel):
    _inherit = 'sales.loading.report.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }

    @api.multi
    def sales_loading_excel_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0] #converts all objects to lists that can be easily be passed to the report
        data = {'name': 'Approved Order Lines Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'start_date' : wiz_data['start_date'],'end_date':wiz_data['end_date'],'type':wiz_data['type'],'partner_id' : wiz_data['partner_id'], 'partner_root_id' : wiz_data['partner_root_id'],'include_root_customer_order': wiz_data['include_root_customer_order'] ,'root_order_transfer_id' : wiz_data['root_order_transfer_id'],'parent_sales_order_transfer_id' : wiz_data['parent_sales_order_transfer_id'], 'product_ids' : wiz_data['product_ids']}
        return {
                    'name':'Sales Order Report',
                    'type': 'ir.actions.report.xml',
                    'report_name': 'rog_modifications.report_sales_loading_report_rog',
                    'datas': data, #It is required you use datas as parameter, otherwise it will transfer data correctly.
                    }

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    partner_id = fields.Many2one('res.partner',string='Customer')
    partner_root_id = fields.Many2one('res.partner',string='Root Customer')
    include_root_customer_order = fields.Boolean(string='Include Root Customer Order')
    root_order_transfer_id = fields.Many2one('sale.order', string='Root Order')
    parent_sales_order_transfer_id = fields.Many2one('sale.order', string='Direct Parent Order')
    product_ids = fields.Many2many('product.product', 'sales_loading_lines_rel', 'sales_loading_wizard_id', 'prod_id', string='Products')
    type =  fields.Selection( [('is_indepot', 'In Depot'), ('is_throughput', 'Throughput'), ('is_internal_use', 'Internal Use'), ('all', 'All Operation Type')],string='Operation Type')




