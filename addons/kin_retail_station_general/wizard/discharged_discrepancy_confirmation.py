# -*- coding: utf-8 -*-

from openerp import api, fields, models

class DischargedDiscrepancyConfirmationWizard(models.TransientModel):
    _name = 'discharged.discrepancy.confirmation.wizard'
    _description = 'Discharged Discrepancy Confirmation Wizard'

    @api.multi
    def action_confirm_wizard(self):
        rec_ids = self.env.context['active_ids']
        records = self.env['product.received.register'].browse(rec_ids)
        for rec in records :
            rec.action_validate()
        return

    prod_alloc = fields.Float(string='Product Allocation')
    qty_rec = fields.Float(string='Qty. Received')
    prod_uom_name = fields.Char(string='Product')


