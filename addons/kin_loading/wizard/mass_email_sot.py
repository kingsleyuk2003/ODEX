# -*- coding: utf-8 -*-

from openerp import api, fields, models

class mass_email_sot_wizard(models.TransientModel):
    _name = 'mass.email.sot.wizard'
    _description = 'Mass Email Summary of Transactions (SOT) Wizard'

    @api.multi
    def mass_email_sot(self):
        ids = self.env.context['active_ids']
        partners = self.env['res.partner'].browse(ids)
        partners.send_mass_email_sot()
        return
