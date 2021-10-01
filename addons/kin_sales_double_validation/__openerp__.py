# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Sale Double Validation',
    'version': '0.1',
    'category': 'Sales',
    'description': """
Sales Double Validation
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','sale','account','kin_sales','sale_stock'],
    'data': [
        'security/security.xml',
        'wizard/sales_orders_confirm.xml',
        'wizard/sales_order_disapprove.xml',
        'sale_view.xml',
        'mail_template.xml',
        'wizard/send_to_manager.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}