# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Sales Modifications',
    'version': '0.1',
    'category': 'Sales',
    'description': """
Sales Modifications.
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','sale','account','kin_account','sale_margin','sales_team','sale_stock','purchase_request','sale_operating_unit'],
    'data': [
        'wizard/credit_limit_by_pass.xml',
        'wizard/credit_limit_disapproval.xml',
        # 'wizard/create_advance_invoice.xml',
        'security/security.xml',
         'sale_view.xml',
        'security/ir.model.access.csv',
        'mail_template.xml',
        'sequence.xml',
        'cron_data.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}