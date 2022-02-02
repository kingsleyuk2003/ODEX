# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2020  Kinsolve Solutions
# Copyright 2020 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api


class EscalationTicketReportWizard(models.TransientModel):
    _name = 'escalation.ticket.wizard'

    @api.multi
    def escalation_ticket_excel_report(self):
        context = self.env.context or {}
        wiz_data = self.read([])[0]  # converts all objects to lists that can be easily be passed to the report
        data = {'name': 'Escalation Ticket Report', 'active_ids': context.get('active_ids', [])}
        data['form'] = {'start_date': wiz_data['start_date'], 'end_date': wiz_data['end_date'],
                        'category_id':wiz_data['category_id'],'company_id':wiz_data['company_id']}
        return {
            'name': 'Escalation Ticket Report',
            'type': 'ir.actions.report.xml',
            'report_name': 'kkon_modifications.escalation_ticket_report',
            'datas': data,  # It is required you use datas as parameter, otherwise it will transfer data correctly.

        }



    start_date = fields.Datetime('Start Open DateTime')
    end_date = fields.Datetime('End Open DateTime')
    category_id = fields.Many2one('kin.ticket.category',string='Escalation Ticket Category')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)



