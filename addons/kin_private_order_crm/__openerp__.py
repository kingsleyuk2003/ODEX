# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Private Sales Order and CRM',
    'version': '0.1',
    'category': 'other',
    'description': """
Product Sales Order and Marketing
=======================================================================================
""",
    'author': 'Kinsolve Solutions - kingsley@kinsolve.com',
    'website': 'http://kinsolve.com',
    'depends': ['base','mail','sale','report_xlsx','calendar'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'private_order_view.xml',
        'wizard/activity_report_wizard_view.xml',
        'kin_report.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}