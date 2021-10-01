# -*- coding: utf-8 -*-

from openerp import api, fields, models

class ProductReceivedRegisterResolutionWizard(models.TransientModel):
    _name = 'product.received.register.resolution.wizard'


    @api.multi
    def action_resolution(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        records = self.env['product.received.register'].browse(rec_ids)
        for rec in records:
            rec.action_resolution_message(msg)
        return


    msg = fields.Text(string='Resolution Message', required=True)


