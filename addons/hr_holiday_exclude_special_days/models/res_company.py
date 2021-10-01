# -*- coding: utf-8 -*-
# © 2016 Jérôme Guerriat
# © 2016 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openerp import fields
from openerp import models


class ResCompany(models.Model):
    _inherit = "res.company"

    deduct_saturday_in_leave =\
        fields.Boolean(string="Deduct saturdays in the leaves",
                       default=True)

    deduct_sunday_in_leave =\
        fields.Boolean(string="Deduct sundays in the leaves",
                       default=True)
