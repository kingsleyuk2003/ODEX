# -*- coding: utf-8 -*-
# Copyright 2017 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    @api.multi
    @api.depends('practical_amount', 'planned_amount')
    def _compute_variance_amount(self):
        self.ensure_one()
        for rec in self:
            rec.variance_amount =\
                rec.practical_amount - rec.planned_amount
            if rec.variance_amount != 0.0:
                rec.variance_percent =\
                    (rec.variance_amount / rec.planned_amount)

    variance_amount = fields.Float(
        string="Variance Amount",
        store=False,
        compute='_compute_variance_amount'
    )

    variance_percent = fields.Float(
        string="Variance Percent",
        store=False,
        compute='_compute_variance_amount'
    )
