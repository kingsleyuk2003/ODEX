# -*- coding: utf-8 -*-
# © 2017 Pierre Faniel
# © 2017 Niboo SPRL (<https://www.niboo.be/>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openerp import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    issue_ids = fields.One2many('project.issue', 'task_id', 'Issues')
