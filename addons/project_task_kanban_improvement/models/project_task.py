# -*- coding: utf-8 -*-
# © 2016 Pierre Faniel
# © 2016 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    customer_image = fields.Binary(related='partner_id.image')
