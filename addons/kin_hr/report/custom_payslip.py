# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, models

class HRPayslipReport(models.AbstractModel):
    _name = 'report.kin_hr.report_payslip_custom'

    @api.multi
    def render_html(self, data=None):
        #active_ids = self.env.context.get('active_ids',[])
        payslip_objs = self.env['hr.payslip'].browse(self.ids)
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('kin_hr.report_payslip_custom')

        docargs = {
            'doc_ids': self.ids,
            'doc_model': 'hr.payslip',  # or replace it with 'report.model'
            'docs': payslip_objs,
            'get_payment_slip_lines' : self.get_payment_slip_lines
        }
        return report_obj.render('kin_hr.report_payslip_custom', docargs)


    def get_payment_slip_lines(self, obj):
        payslip_line = self.env['hr.payslip.line']
        res = []
        ids = []
        for id in range(len(obj)):
            if obj[id].appears_on_payslip is True:
                ids.append(obj[id].id)
        if ids:
            res = payslip_line.browse(ids)
        return res
#   ------------------------------  OR USE THE FOLLOWING OTHER WAY   -------------------------------------
    # make sure you comment 'get_payment_slip_lines' : self.get_payment_slip_lines in the docargs
    # and add "o" to get_payment_slip_lines in the xml report to become <tr t-foreach="o.get_payment_slip_lines(o.line_ids)" t-as="p">

# class HRPayslip(models.Model):
#     _inherit = 'hr.payslip'
#
#     @api.model
#     def get_payment_slip_lines(self, obj):
#         payslip_line = self.env['hr.payslip.line']
#         res = []
#         ids = []
#         for id in range(len(obj)):
#             if obj[id].appears_on_payslip is True:
#                 ids.append(obj[id].id)
#         if ids:
#             res = payslip_line.browse(ids)
#         return res