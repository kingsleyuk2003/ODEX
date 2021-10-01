# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'HR Expense Extensions',
    'version': '0.1',
    'category': 'HR',
    'description': """
Human Expense Extensions.

For Help in Customization: Contact Kingsley Okonkwo on +2348030412562 or email at kingsley@kinsolve.com

=======================================================================================
""",
    'author': 'Kinglsey Okonkwo - Kinsolve Solutions, kingsley@kinsolve.com',
    'website': 'http://kinsolve.com',
    'depends': ['base','hr','hr_payroll','hr_payroll_account','hr_expense','hr_attendance','hr_holidays','hr_contract_operating_unit','kin_report','report_xlsx'],
    'data': [
        'security/rules.xml',
        'security/ir.model.access.csv',
        'hr_expense_view.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}