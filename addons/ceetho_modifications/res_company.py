# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from openerp import api, fields, models, _, SUPERUSER_ID


class ResCompanyExtend(models.Model):
    _inherit = "res.company"

    email_other = fields.Char(string='Other Emails')
