# -*- coding: utf-8 -*-

from openerp import api, fields, models

class RetailSaleDisApprovalWizard(models.TransientModel):
    _name = 'retail.sale.disapproval.wizard'
    _description = 'Retail Sale Disapproval Wizard'


    @api.multi
    def action_disapprove(self):
        rec_ids = self.env.context['active_ids']
        msg = self.msg
        records = self.env['kin.retail.sale'].browse(rec_ids)
        for rec in records:
            rec.action_disapprove(msg)
        return



    msg = fields.Text(string='Message', required=True)


