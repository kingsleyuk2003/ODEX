# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'MRP Extensions',
    'version': '0.1',
    'category': 'MRP',
    'description': """
CRM Extensions
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','mrp','kin_stock','mrp_operations'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'mrp_view.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}