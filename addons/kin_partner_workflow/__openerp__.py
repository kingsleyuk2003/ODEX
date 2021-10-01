# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Partner Workflow',
    'version': '0.1',
    'category': 'Sales',
    'description': """
Partner Extensions
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'wizard/customer_disapproval_reason.xml',
        'res_partner_view.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}