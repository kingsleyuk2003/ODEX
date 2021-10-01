# -*- coding: utf-8 -*-

from openerp import api, fields, models

class ChangeDestinationWizard(models.TransientModel):
    _name = 'change.destination.wizard.aviation'


    @api.multi
    def action_change_destination(self):
        rec_ids = self.env.context['active_ids']
        new_destination = self.new_to_stock_location_id
        records = self.env['product.received.register.aviation'].browse(rec_ids)
        for rec in records:
            rec.change_destination(new_destination)
        return

    new_to_stock_location_id = fields.Many2one('kin.aviation.station',string='New Aviation Station', required=True)


