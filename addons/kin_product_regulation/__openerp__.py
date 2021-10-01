# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Product Regulation',
    'version': '0.1',
    'category': 'Regulation',
    'description': """
Product Regulation Module
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','mail','product'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'product_regulation.xml',
        'cron_data.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}