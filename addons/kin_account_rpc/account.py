# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models, _


class AccountMoveExtend(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        if 'is_from_rpc' in vals:
            #sudo() needed here, otherwise it does not save from another user other than admin
            move = super(AccountMoveExtend, self.sudo().with_context(check_move_validity=False, partner_id=vals.get('partner_id'))).create(vals)
        else:
            move = super(AccountMoveExtend, self).create(vals)
        return move

    is_from_rpc = fields.Boolean(string='Is From RPC')


class AccountMoveLineExtend(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def create(self, vals, apply_taxes=False):
        if 'is_from_rpc' in vals:
            #sudo() is not required here
            move_line = super(AccountMoveLineExtend,self.sudo().with_context({'check_move_validity':False})).create(vals)
        else:
            move_line = super(AccountMoveLineExtend,self).create(vals)
        return move_line

    is_from_rpc = fields.Boolean(string='Is From RPC')