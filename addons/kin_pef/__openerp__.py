# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Petroleum Equalisation Fund',
    'version': '0.1',
    'description': """
Petroleum Equalization Fund
=======================================================================================
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','account','kin_stock'],
    'data': [
        'security/security.xml',
        'security/rules.xml',
        'security/ir.model.access.csv',
        'sequence.xml',
        'pef_view.xml',
    ],
    'test':[],
    'installable': True,
    'images': [],
}