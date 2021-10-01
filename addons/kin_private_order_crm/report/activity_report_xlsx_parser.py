# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import models, fields, api

class ActivityReportParser(models.TransientModel):

    _name = 'activity.report.parser'

    def _get_activity_report_data(self,form):
        start_date = form['start_date']
        end_date = form['end_date']
        rep_id = form['rep_id']

        mk_obj = self.env['marketing.activity']
        mk_lines = mk_obj.search(
            [('date', '>=', start_date), ('date', '<=', end_date),
             ('user_id', '=', rep_id[0])])

        return mk_lines





