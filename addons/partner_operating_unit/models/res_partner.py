# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L.
# - Jordi Ballester Alomar
# © 2015 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# @ 2017 Kinsolve Solutions - Kingsley Okonkwo - kingsley@kinsolve.com
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from openerp import _, api, fields, models
from openerp.exceptions import ValidationError, UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    operating_unit_id = fields.Many2one(
        comodel_name='operating.unit',
        string='Operating Unit',
        default=lambda self: (self.env['res.users'].operating_unit_default_get(self.env.uid))
    )

