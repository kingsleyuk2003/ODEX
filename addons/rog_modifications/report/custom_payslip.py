# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2019  Kinsolve Solutions
# Copyright 2019 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

from openerp import api, models

class HRPayslipReport(models.AbstractModel):
    _name = 'report.rog_modifications.report_payslip_custom_rog'

    @api.multi
    def render_html(self, data=None):
        #active_ids = self.env.context.get('active_ids',[])
        payslip_objs = self.env['hr.payslip'].browse(self.ids)
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('rog_modifications.report_payslip_custom_rog')

        docargs = {
            'doc_ids': self.ids,
            'doc_model': 'hr.payslip',  # or replace it with 'report.model'
            'docs': payslip_objs,
            'get_payment_slip_lines' : self.get_payment_slip_lines
        }
        return report_obj.render('rog_modifications.report_payslip_custom_rog', docargs)


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

class HRPayslipReport(models.AbstractModel):
    _name = 'report.rog_modifications.report_payslip_custom_rog_other'

    @api.multi
    def render_html(self, data=None):
        #active_ids = self.env.context.get('active_ids',[])
        payslip_objs = self.env['hr.payslip'].browse(self.ids)
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('rog_modifications.report_payslip_custom_rog_other')

        docargs = {
            'doc_ids': self.ids,
            'doc_model': 'hr.payslip',  # or replace it with 'report.model'
            'docs': payslip_objs,
            'get_payment_slip_lines' : self.get_payment_slip_lines
        }
        return report_obj.render('rog_modifications.report_payslip_custom_rog_other', docargs)


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

class HRPayslipReport(models.AbstractModel):
    _name = 'report.rog_modifications.report_payslip_custom_rog_62'

    @api.multi
    def render_html(self, data=None):
        #active_ids = self.env.context.get('active_ids',[])
        payslip_objs = self.env['hr.payslip'].browse(self.ids)
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('rog_modifications.report_payslip_custom_rog_62')

        docargs = {
            'doc_ids': self.ids,
            'doc_model': 'hr.payslip',  # or replace it with 'report.model'
            'docs': payslip_objs,
            'get_payment_slip_lines' : self.get_payment_slip_lines
        }
        return report_obj.render('rog_modifications.report_payslip_custom_rog_62', docargs)


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


class HRPayslipReport(models.AbstractModel):
    _name = 'report.rog_modifications.report_payslip_custom_rog_100'

    @api.multi
    def render_html(self, data=None):
        #active_ids = self.env.context.get('active_ids',[])
        payslip_objs = self.env['hr.payslip'].browse(self.ids)
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('rog_modifications.report_payslip_custom_rog_100')

        docargs = {
            'doc_ids': self.ids,
            'doc_model': 'hr.payslip',  # or replace it with 'report.model'
            'docs': payslip_objs,
            'get_payment_slip_lines' : self.get_payment_slip_lines
        }
        return report_obj.render('rog_modifications.report_payslip_custom_rog_100', docargs)


    def get_payment_slip_lines(self, obj):
        payslip_line = self.env['hr.payslip.line']
        res = []
        ids = []
        for id in range(len(obj)):
            if obj[id].appears_on_payslip is True:
                ids.append(obj[id].id)
        if ids:
            payslip_lines = payslip_line.browse(ids)

        line_list = []
        additions = 0
        deductions = 0
        for line in payslip_lines:
            if line.salary_rule_id.code == 'PAYE':
                line_list.append([{'name':line.name},{'value':line.total},{'category':line.category_id.code}])
                deductions += line.total
            if line.salary_rule_id.code != 'PAYE':
                if line.slip_id.struct_id.name not in ['GMD', 'RETAIL']:
                    if line.salary_rule_id.code in (
                    'LO', 'SAR', 'lieo', 'lwp', 'absent', 'absent_refund', 'lwpr_refund', 'lieo_refund', 'other_refund',
                    'reward'):
                        line_list.append([{'name': line.name}, {'value': line.total}, {'category': line.category_id.code}])
                        if line.salary_rule_id.is_addition:
                            additions += line.total
                        if line.salary_rule_id.is_deduction:
                            deductions += line.total
                    else:
                        line_list.append([{'name': line.name}, {'value': line.total * 2.631578947}, {'category': line.category_id.code}])
                        if line.salary_rule_id.is_addition:
                            additions += line.total * 2.631578947
                        if line.salary_rule_id.is_deduction:
                            deductions += line.total * 2.631578947

                else:
                    line_list.append([{'name': line.name}, {'value': line.total}, {'category': line.category_id.code}])
                    if line.salary_rule_id.is_addition:
                        additions += line.total
                    if line.salary_rule_id.is_deduction:
                        deductions += line.total

            if line.salary_rule_id.is_net_amount:
                line_list.append([{'name': line.name}, {'value': additions - deductions}, {'category': line.category_id.code}])

        return line_list