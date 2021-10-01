# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html
from openerp import api, fields, models, _
from datetime import datetime, timedelta

class HRAppraisal(models.Model):
    _inherit = 'hr.appraisal'

    firstname = fields.Char(string='First Name')
    lastname = fields.Char(string='Last Name')
    middlename = fields.Char(string='Middle Name')
    state_id = fields.Many2one('res.country.state',string='State of Origin')
    next_of_kin = fields.Char('Next of Kin')
    nok_phone = fields.Char('Next of Kin Phone No.')
    nok_relationship = fields.Many2one('nok.relationship', help='Next of Kin Relationship')
    emergency_contact = fields.Char(string='Emergency Contact')
    emergency_contact_phone = fields.Char(string='Emergency Contact Phone')
    employment_date = fields.Date('Employment Date')
    employment_status = fields.Selection([('confirmed', 'Confirmed'), ('probation', 'Probation')], string='Employment Status')
    guarantor_ids = fields.One2many('guarantor','employee_id', string='Guarantor(s)')
    qualification_ids = fields.One2many('qualification', 'employee_id', string='Guarantor(s)')
