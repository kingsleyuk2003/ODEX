# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, fields, models
from openerp.tools.translate import _
import re
from openerp.exceptions import UserError



class crm_lead2opportunity_mass_convert(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner.mass'

    action = fields.Selection([('nothing', 'Do not link to a customer')],string='Related Customer',default='nothing', required=True)


class crm_lead2opportunity_partner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    action = fields.Selection([
        ('nothing', 'Nothing')
    ], 'Related Customer',default='nothing',  required=True)

