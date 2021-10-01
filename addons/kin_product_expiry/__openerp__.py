# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Product Expiry',
    'version': '0.1',
    'category': 'tock',
    'description': """
Product Expiry Module
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','mail','product','product_expiry_simple','stock'],
    'data': [
        'security/security.xml',
        'product_expiry.xml',
        'cron_data.xml',
        'product_expiry.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}