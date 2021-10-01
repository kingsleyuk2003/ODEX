# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api


class ActivityReportWizard(models.TransientModel):
    _name = 'activity.report.wizard'

    #     def pdf_report(self, cr, uid, ids, context=None):
    #         context = context or {}
    #         datas = {'name':'PFS Report','ids': context.get('active_ids', [])} # use ids for pdf report otherwise there will be error
    #
    #         return {'type': 'ir.actions.report.xml',
    #                     'report_name': 'pfa.form.pdf.webkit',
    #                     'datas':datas,
    #                     }

    @api.multi
    def activity_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0] #converts all objects to lists that can be easily be passed to the report
        data = {'name': 'Activity Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'start_date' : wiz_data['start_date'],'end_date':wiz_data['end_date'],'rep_id' : wiz_data['rep_id']}
        return  {
                    'name':'Activity Report',
                    'type': 'ir.actions.report.xml',
                    'report_name': 'kin_private_order_crm.report_activity_report',
                    'datas':data, #It is required you use datas as parameter, otherwise it will transfer data correctly.

                }


    start_date = fields.Date('Start Date',required=True)
    end_date = fields.Date('End Date',required=True)
    rep_id = fields.Many2one('res.users', string='Sales Representative', required=True)





