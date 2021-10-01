# -*- coding: utf-8 -*-

from openerp import api, fields, models

class TicketRecoveredWizard(models.TransientModel):
    _name = 'ticket.recovered.wizard'
    _description = 'Ticket Recovered Wizard'

    @api.multi
    def action_ticket_recovered_wizard(self):
        rec_ids = self.env.context['active_ids']
        is_ticket_recovered = self.env.context.get('is_ticket_recovered','Nil')
        is_ticket_mistake = self.env.context.get('is_ticket_mistake','Nil')

        ctx = dict(self.env.context or {})
        ctx.update({'is_ticket_recovered': is_ticket_recovered,'is_ticket_mistake':is_ticket_mistake,'the_active_ids':rec_ids})

        if is_ticket_recovered == False :
            return self.env['stock.picking'].with_context(ctx).action_police_report()

        records = self.env['stock.picking'].browse(rec_ids)
        for rec in records :
            rec.with_context(ctx).action_cancel()
        return





