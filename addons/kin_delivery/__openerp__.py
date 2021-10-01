# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Delivery Grid',
    'version': '0.1',
    'description': """
Delivery Grid for Oil and Gas
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','account','kin_stock','kin_account'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'sequence.xml',
        'delivery_grid_view.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}