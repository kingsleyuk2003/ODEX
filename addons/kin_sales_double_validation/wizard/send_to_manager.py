# -*- coding: utf-8 -*-

from openerp import api, fields, models

class sales_orders_confirm_wizard(models.TransientModel):
    _name = 'send.manager.wizard'
    _description = 'Send to Manager Wizard'

    @api.multi
    def send_to_manager_ok(self):
        return
