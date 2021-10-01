# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from odoo import models, fields, api


class CaseFileReportWizard(models.TransientModel):
    _name = 'case.file.wizard'


    @api.multi
    def case_file_excel_report(self):
        return self.env.ref('rog_legal.case_file_report').report_action(self)


    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')



