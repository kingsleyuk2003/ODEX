# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Oil Lifting',
    'description': """
Lifting for Oil and Gas
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','kin_stock','kin_sales_double_validation','kin_delivery','kin_report','kin_account'],
    'data': [
        'security/security.xml',
        'report/custom_report_layouts.xml',
        'report/custom_instant_delivery_order.xml',
        'security/ir.model.access.csv',
        'sequence.xml',
         'lifting_view.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}