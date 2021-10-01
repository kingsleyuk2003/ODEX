# -*- coding: utf-8 -*-

from openerp import api, fields, models

class CreatePOWizard(models.TransientModel):
    _name = 'create.po.wizard'


    @api.multi
    def action_create_po(self):
        rec_ids = self.env.context['active_ids']
        ago_qty = self.ago_qty
        pms_qty = self.pms_qty
        records = self.env['purchase.contract'].browse(rec_ids)
        for rec in records:
            rec.action_create_po_fixing(ago_qty,pms_qty)
        return

    ago_qty = fields.Float(string='AGO Qty.', required='AGO Qty.')
    pms_qty = fields.Float(string='PMS Qty.', required='PMS Qty.')


