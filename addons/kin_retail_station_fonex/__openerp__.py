# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright 2017  Kinsolve Solutions
# Copyright 2017 Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)
# License: see https://www.gnu.org/licenses/lgpl-3.0.en.html

{
    'name': 'Fuel Retail Station Extension for Fonex',
    'version': '0.1',
    'category': 'Sales',
    'description': """
 Retail Station extention for Fonex
image from openclip http://openclipart.org/
""",
    'author': 'Kingsley Okonkwo (kingsley@kinsolve.com, +2348030412562)',
    'website': 'http://kinsolve.com',
    'depends': ['base','kin_retail_station_general'],
    'data': [
        'security/security.xml',
        'retail_station_view.xml'
    ],
    'test':[],
    'installable': True,
    'images': [],
}