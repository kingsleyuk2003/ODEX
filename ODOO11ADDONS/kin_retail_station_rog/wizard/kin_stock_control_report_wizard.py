# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import models, fields, api


class KinStockControlReportWizard(models.TransientModel):
    _name = 'kin.stock.control.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }

    @api.multi
    def stock_control_excel_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0] #converts all objects to lists that can be easily be passed to the report
        # data = {'name': 'Day Control Report', 'active_ids': context.get('active_ids', [])}
        # data['form'] = {'start_date' : wiz_data['start_date'],'end_date':wiz_data['end_date'],'retail_station_ids' : wiz_data['retail_station_ids']}
        return self.env.ref('kin_retail_station_rog.stock_control_report').report_action(self)


    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    retail_station_ids = fields.Many2many('kin.retail.station', 'control_retail_rel', 'controlwizard_id', 'retailstation_id', string='Retail Stations')




