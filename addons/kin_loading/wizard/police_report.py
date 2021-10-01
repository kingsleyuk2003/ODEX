# -*- coding: utf-8 -*-

from openerp import api, fields, models
from openerp.exceptions import UserError

class PoliceReportWizard(models.TransientModel):
    _name = 'police.report.wizard'
    _description = 'Police report Wizard'



    @api.multi
    def action_police_report_wizard(self):
        is_police_report = self.env.context['is_police_report']
        if is_police_report == False :
            raise UserError('Please you may not Cancel this Loading Ticket, without the ticket being recovered or a police report')

        return

    @api.multi
    def action_police_report_confirm(self):
        rec_ids = self.env.context['the_active_ids']
        is_police_report = self.env.context['is_police_report']
        ctx = dict(self.env.context or {})
        ctx.update({'is_police_report': is_police_report})

        records = self.env['stock.picking'].browse(rec_ids)
        for rec in records:
            rec.with_context(ctx).action_cancel()
        return



