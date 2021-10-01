# -*- coding: utf-8 -*-

from openerp import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'

    compacted = fields.Boolean('Summary Account', help='If flagged, no details will be displayed in the Standard report, only summary amounts.', default=False)
    type_third_parties = fields.Selection([('no', 'No'), ('supplier', 'Supplier'), ('customer', 'Customer')], string='Third Party', required=True, default='no')
