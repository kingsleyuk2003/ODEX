# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Account Payment Group Extensions',
    'version': '0.1',
    'category': 'Accounting',
    'description': """
Account Payment Group Extensions
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','kin_account','account_payment_group'],
    'data': [
        'data/data.xml',
        'security/security.xml',
        'account_payment_group_view.xml',
         'report/custom_report_layouts.xml',
        'report/custom_receipt.xml',
        'mail_template.xml',

    ],
    'test':[],
    'installable': True,
    'images': [],
}