# -*- coding: utf-8 -*-

from openerp import api, fields, models
from openerp.exceptions import UserError

class ChangePriceWizard(models.TransientModel):
    _name = 'change.price.wizard.aviation'
    _description = 'Change Price Wizard'

    @api.multi
    def action_change_price(self):
        if self.new_price <= 0 :
            raise UserError(_('New Price cannot be lesser than or equal to Zero'))
        recs = self.env.context['active_ids']
        pumps = self.env['kin.fuel.pump.aviation'].browse(recs)
        pumps.change_prices(self.new_price)
        return


    new_price = fields.Monetary(string='New Price',required=True)
    currency_id = fields.Many2one("res.currency", string="Currency", required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)

