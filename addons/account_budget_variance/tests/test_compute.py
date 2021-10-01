# -*- coding: utf-8 -*-
# Copyright 2017 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase


class TestCompute(TransactionCase):
    def setUp(self, *args, **kwargs):
        super(TestCompute, self).setUp(*args, **kwargs)
        # Objects
        self.obj_budget = self.env['crossovered.budget.lines']

    def test_compute(self):
        new = self.obj_budget.new()
        new.planned_amount = 50000

        # Check Variance Amount
        self.assertEqual(-50000, new.variance_amount)

        # Check Variance Percent
        self.assertEqual(-1, new.variance_percent)
