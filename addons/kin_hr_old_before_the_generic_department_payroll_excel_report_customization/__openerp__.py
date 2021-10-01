# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'HR Extensions',
    'version': '0.1',
    'category': 'HR',
    'description': """
Human Resources Extensions.
Includes Extra Fields for Employee Directory such as Qualifications, Employment Details,
Next of Kin, Emergency Information, Guarantor Information etc
For Help in Customization: Contact Kingsley Okonkwo on +2348030412562 or email at kingsley@kinsolve.com

=======================================================================================
""",
    'author': 'Kinglsey Okonkwo - Kinsolve Solutions, kingsley@kinsolve.com',
    'website': 'http://kinsolve.com',
    'depends': ['base','hr','hr_payroll','hr_expense','hr_attendance','hr_holidays','hr_contract_operating_unit','kin_report','report_xlsx'],
    'data': [
        'kin_report.xml',
        'security/security.xml',
        'security/rules.xml',
        'security/ir.model.access.csv',
        'hr_view.xml',
        'report/custom_report_layouts.xml',
        'report/custom_payslip.xml',
        'wizard/payslip_report_wizard_view.xml',
        'wizard/mass_email_payslip_view.xml',
        'mail_template.xml',


    ],
    'test':[],
    'installable': True,
    'images': [],
}