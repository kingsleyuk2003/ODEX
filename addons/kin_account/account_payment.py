# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from openerp import api, fields, models, _


class AccountPaymentExtend(models.Model):
    _inherit = 'account.payment'

    ref_no = fields.Char(string='Reference No')

################################################################################################
#This code below generated an error that made the account group to be read only, on Aminata project.
#It  took so much time to get this discovered. So dont ever do this again
###########################################################################################


# class AccountPaymentExtend(models.Model):
#     _name = 'account.payment'
#     _inherit = [ 'account.payment','mail.thread', 'ir.needaction_mixin']
#
#     ref_no = fields.Char(string='Reference No')


################################################################################################





