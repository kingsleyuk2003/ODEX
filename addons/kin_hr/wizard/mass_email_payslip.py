# -*- coding: utf-8 -*-

from openerp import api, fields, models

class mass_email_payslip_wizard(models.TransientModel):
    _name = 'mass.email.payslip.wizard'
    _description = 'Mass Email Payslip Wizard'

    @api.multi
    def mass_email_payslip(self):
        ps_ids = self.env.context['active_ids']
        payslips = self.env['hr.payslip'].browse(ps_ids)
        payslips.send_mass_email_payslip()
        return
