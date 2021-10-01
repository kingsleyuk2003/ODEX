# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _
from openerp.exceptions import UserError

class ProductReceivedRegister(models.Model):
    _inherit = 'product.received.register'

    state = fields.Selection(selection_add=[('waiting', 'Awaiting Approval')])


    @api.multi
    def action_submit(self):
        self.state = 'waiting'

        # Notify the manager
        user_ids = []
        group_obj = self.env.ref('kin_retail_station_fonex.group_show_validate_inventory_button')
        for user in group_obj.users:
            user_ids.append(user.id)

        self.message_unsubscribe_users(user_ids=user_ids)
        self.message_subscribe_users(user_ids=user_ids)
        self.message_post(_(
                'The Product Received Record with ID %s from %s for the %s is Awaiting Validation. Please follow the link or log in to validate and update the stock') % (
                                  self.name, self.env.user.name, self.to_stock_location_id.name),
                              subject='Product Received Record Awaiting Validation',
                              subtype='mail.mt_comment')


class ProductReceivedRegisterLines(models.Model):
    _inherit = 'product.received.register.lines'

    state = fields.Selection(selection_add=[('waiting', 'Awaiting Approval')])